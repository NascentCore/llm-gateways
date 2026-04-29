#!/usr/bin/env python3
"""
读取 vendor_models_official_catalog.json，按各厂商 release_rank 取 Top2 模型，
通过 NewAPI 管理接口 POST /api/channel/ 创建渠道（幂等：默认跳过已存在同名渠道）；
若模型在目录中带 pricing，则向 PUT /api/option/ 合并写入 ModelRatio / CompletionRatio 等
（需 Root 权限，可用 NEWAPI_ROOT_* 或与普通管理员同账号的 Root 用户）。

鉴权与 scripts/newapi_batch_accounts/create_account.py 一致：管理员用户名密码登录取 Cookie。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
try:
    import requests
except ImportError:
    print("需要 requests：pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

# 复用批量建号脚本中的登录与请求封装
_BATCH_DIR = Path(__file__).resolve().parent.parent / "newapi_batch_accounts"
sys.path.insert(0, str(_BATCH_DIR))
import create_account as ca  # noqa: E402


def _q4(x: float) -> float:
    return round(float(x), 4)


def _load_catalog(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _top_models(models: list[dict], n: int) -> list[dict]:
    ranked = sorted(models, key=lambda m: int(m.get("release_rank", 0)), reverse=True)
    return ranked[:n]


def _top_model_ids(models: list[dict], n: int) -> list[str]:
    return [m["model_id"] for m in _top_models(models, n)]


def _resolve_api_key(provider: dict) -> str | None:
    """从环境变量读取密钥；腾讯支持 TENCENT_HUNYUAN_KEY 或 APP_ID/SECRET_ID/SECRET_KEY 三段。"""
    pid = provider["id"]
    name = provider.get("env_key_name", "")
    if pid == "tencent":
        single = os.environ.get("TENCENT_HUNYUAN_KEY") or os.environ.get(name)
        if single:
            return single.strip()
        app = os.environ.get("TENCENT_APP_ID", "0").strip()
        sid = os.environ.get("TENCENT_SECRET_ID", "").strip()
        sk = os.environ.get("TENCENT_SECRET_KEY", "").strip()
        if sid and sk:
            return f"{app}|{sid}|{sk}"
        return None
    if not name:
        return None
    v = os.environ.get(name)
    return v.strip() if v else None


def _fetch_status(base_url: str) -> dict | None:
    url = f"{base_url.rstrip('/')}/api/status"
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        print(f"[warn] GET /api/status 失败 HTTP {r.status_code}: {r.text[:500]}", file=sys.stderr)
        return None
    data = r.json()
    if not data.get("success"):
        return None
    return data.get("data") or {}


def _env_float(name: str) -> float | None:
    v = os.environ.get(name)
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    try:
        return float(v)
    except ValueError:
        print(f"[warn] 环境变量 {name} 非数字，已忽略", file=sys.stderr)
        return None


def _cx_to_usd(amount: float, currency: str, usd_cny_rate: float) -> float:
    """将「每百万 token」的单价换为美元。usd_cny_rate 为 1 USD = X CNY。"""
    c = (currency or "USD").upper()
    if c == "USD":
        return float(amount)
    if c in ("CNY", "RMB"):
        if usd_cny_rate <= 0:
            raise ValueError("invalid usd_cny rate")
        return float(amount) / usd_cny_rate
    raise ValueError(f"unsupported currency: {currency}")


def _get_first_tier_pricing(pricing: dict) -> dict[str, float] | None:
    """从阶梯结构取首档 input/output（及可选 cache），值仍为原币种/百万 token。"""
    for key in ("tiers_by_prompt_tokens",):
        arr = pricing.get(key)
        if isinstance(arr, list) and arr:
            t0 = arr[0]
            if not isinstance(t0, dict):
                return None
            ip = t0.get("input_per_million_tokens")
            op = t0.get("output_per_million_tokens")
            if ip is not None and op is not None:
                return {"input": float(ip), "output": float(op)}

    arr = pricing.get("tiers")
    if isinstance(arr, list) and arr:
        t0 = arr[0]
        if not isinstance(t0, dict):
            return None
        ip = t0.get("input_per_million_tokens")
        op = t0.get("output_per_million_tokens")
        cip = t0.get("cache_input_per_million_tokens")
        if ip is not None and op is not None:
            out: dict[str, float] = {"input": float(ip), "output": float(op)}
            if cip is not None:
                out["cache_read"] = float(cip)
            return out

    bds = pricing.get("by_deployment_scope")
    if isinstance(bds, dict):
        for scope_key in ("china_mainland", "中国内地", "mainland"):
            if scope_key not in bds:
                continue
            sc = bds[scope_key]
            if not isinstance(sc, dict):
                continue
            tarr = sc.get("tiers_by_input_tokens")
            if isinstance(tarr, list) and tarr:
                t0 = tarr[0]
                if isinstance(t0, dict):
                    ip = t0.get("input_per_million_tokens")
                    op = t0.get("output_per_million_tokens")
                    if ip is not None and op is not None:
                        return {"input": float(ip), "output": float(op)}

    return None


def _parse_pricing_to_usd(
    model_id: str, pricing: dict, usd_cny_rate: float
) -> tuple[float, float, float | None, float | None] | None:
    """
    返回 (usd_in_per_m, usd_out_per_m, cache_read_ratio, create_cache_write_ratio) 或 None。
    缓存类为「相对每百万 input 的倍率」：cache_read 官方价(每百万) / usd_in。
    """
    unit = (pricing.get("unit") or "").lower()
    if unit and "million" not in unit and "per_million" not in unit:
        print(f"[warn] 跳过倍率 {model_id}: 未知 unit={unit!r}", file=sys.stderr)
        return None

    cur = pricing.get("currency") or "USD"
    if str(cur).upper() not in ("USD", "CNY", "RMB"):
        print(f"[warn] 跳过倍率 {model_id}: 未知 currency={cur!r}", file=sys.stderr)
        return None
    cstr = str(cur)

    usd_in: float | None = None
    usd_out: float | None = None
    cr_ratio: float | None = None
    cw_ratio: float | None = None

    if "input" in pricing and "output" in pricing:
        usd_in = _cx_to_usd(float(pricing["input"]), cstr, usd_cny_rate)
        usd_out = _cx_to_usd(float(pricing["output"]), cstr, usd_cny_rate)
        if "cache_read" in pricing:
            ur = _cx_to_usd(float(pricing["cache_read"]), cstr, usd_cny_rate)
            cr_ratio = ur / usd_in if usd_in else None
        if "cache_write" in pricing:
            uw = _cx_to_usd(float(pricing["cache_write"]), cstr, usd_cny_rate)
            cw_ratio = uw / usd_in if usd_in else None
    elif "input_cache_hit" in pricing and "input_cache_miss" in pricing and "output" in pricing:
        usd_in = _cx_to_usd(float(pricing["input_cache_miss"]), cstr, usd_cny_rate)
        usd_out = _cx_to_usd(float(pricing["output"]), cstr, usd_cny_rate)
        uhit = _cx_to_usd(float(pricing["input_cache_hit"]), cstr, usd_cny_rate)
        cr_ratio = uhit / usd_in if usd_in else None
    elif (tier := _get_first_tier_pricing(pricing)) is not None:
        usd_in = _cx_to_usd(tier["input"], cstr, usd_cny_rate)
        usd_out = _cx_to_usd(tier["output"], cstr, usd_cny_rate)
        if "cache_read" in tier:
            ur = _cx_to_usd(tier["cache_read"], cstr, usd_cny_rate)
            cr_ratio = ur / usd_in if usd_in else None
    else:
        print(f"[warn] 跳过倍率 {model_id}: 无可用 input/output 或阶梯首档", file=sys.stderr)
        return None

    if usd_in is None or usd_out is None or usd_in <= 0:
        print(f"[warn] 跳过倍率 {model_id}: 无效 input/output 价", file=sys.stderr)
        return None

    return (usd_in, usd_out, cr_ratio, cw_ratio)


def _compute_option_updates(
    model_id: str,
    usd_in: float,
    usd_out: float,
    cr_ratio: float | None,
    cw_ratio: float | None,
    quota_per_unit: float,
) -> dict[str, dict[str, float]]:
    """单模型写入到各 option key 的条目标量（已四位小数）。"""
    if quota_per_unit <= 0:
        raise ValueError("quota_per_unit")
    model_ratio = (usd_in * quota_per_unit) / 1_000_000.0
    completion_ratio = (usd_out / usd_in) if usd_in else 0.0
    out: dict[str, dict[str, float]] = {
        "ModelRatio": {model_id: _q4(model_ratio)},
        "CompletionRatio": {model_id: _q4(completion_ratio)},
    }
    if cr_ratio is not None and cr_ratio > 0:
        out["CacheRatio"] = {model_id: _q4(cr_ratio)}
    if cw_ratio is not None and cw_ratio > 0:
        out["CreateCacheRatio"] = {model_id: _q4(cw_ratio)}
    return out


def _option_json_to_map(val: str) -> dict[str, float]:
    if not val or not str(val).strip():
        return {}
    try:
        raw = json.loads(val)
    except json.JSONDecodeError:
        return {}
    if not isinstance(raw, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in raw.items():
        if isinstance(v, (int, float)):
            out[str(k)] = float(v)
        else:
            try:
                out[str(k)] = float(v)
            except (TypeError, ValueError):
                pass
    return out


def _map_to_json(m: dict[str, float]) -> str:
    return json.dumps(m, ensure_ascii=False, separators=(",", ":"))


def _get_option_list(cfg: dict) -> list[dict] | None:
    base = cfg["base_url"].rstrip("/")
    r = ca._admin_request(cfg, "GET", f"{base}/api/option/", timeout=30)
    if r.status_code != 200:
        return None
    data = r.json()
    if not data.get("success"):
        return None
    d = data.get("data")
    if isinstance(d, list):
        return d
    return None


def _get_option_value(cfg: dict, key: str) -> str | None:
    opts = _get_option_list(cfg)
    if opts is None:
        return None
    for item in opts:
        if not isinstance(item, dict):
            continue
        if item.get("key") == key:
            v = item.get("value")
            if v is None:
                return ""
            return v if isinstance(v, str) else str(v)
    return None


def _put_option_key(cfg: dict, key: str, value_str: str, dry_run: bool) -> bool:
    if dry_run:
        print(f"[dry-run] PUT /api/option/ key={key!r} value_len={len(value_str)}")
        return True
    base = cfg["base_url"].rstrip("/")
    r = ca._admin_request(
        cfg,
        "PUT",
        f"{base}/api/option/",
        json={"key": key, "value": value_str},
        timeout=60,
    )
    if r.status_code == 403:
        print("写入倍率失败: 403 无超级管理员权限（需 Root 访问 /api/option/）", file=sys.stderr)
        return False
    if r.status_code != 200:
        print(f"写入倍率失败 HTTP {r.status_code}: {r.text[:800]}", file=sys.stderr)
        return False
    data = r.json()
    if not data.get("success"):
        print(f"写入倍率失败: {data.get('message', r.text)[:500]}", file=sys.stderr)
        return False
    return True


def _merge_pricing_for_catalog(
    catalog: dict,
    top_n: int,
    usd_cny_rate: float,
    quota_per_unit: float,
    *,
    only_provider_ids: set[str] | None = None,
) -> tuple[dict[str, dict[str, float]], list[str]]:
    """
    收集全目录各厂商 top_n 的模型倍率更新。
    返回 ( { OptionKey: merged_map }, list of warn-skip model_ids )
    """
    option_maps: dict[str, dict[str, float]] = {
        "ModelRatio": {},
        "CompletionRatio": {},
        "CacheRatio": {},
        "CreateCacheRatio": {},
    }
    for p in catalog.get("providers") or []:
        if only_provider_ids and p.get("id") not in only_provider_ids:
            continue
        for m in _top_models(p.get("models") or [], top_n):
            mid = m.get("model_id")
            if not mid:
                continue
            pr = m.get("pricing")
            if not isinstance(pr, dict) or not pr:
                continue
            parsed = _parse_pricing_to_usd(str(mid), pr, usd_cny_rate)
            if parsed is None:
                continue
            uin, uout, ucread, ucwrite = parsed
            try:
                up = _compute_option_updates(str(mid), uin, uout, ucread, ucwrite, quota_per_unit)
            except (ValueError, ZeroDivisionError) as e:
                print(f"[warn] 倍率计算失败 {mid}: {e}", file=sys.stderr)
                continue
            for ok, mpart in up.items():
                option_maps[ok].update(mpart)
    for k, v in list(option_maps.items()):
        if not v:
            del option_maps[k]
    return option_maps, []


def _find_channel_by_name(cfg: dict, channel_name: str) -> dict | None:
    base = cfg["base_url"].rstrip("/")
    url = f"{base}/api/channel/search"
    r = ca._admin_request(cfg, "GET", url, params={"keyword": channel_name, "p": 1, "page_size": 50})
    if r.status_code != 200:
        print(f"[warn] 搜索渠道失败 HTTP {r.status_code}: {r.text[:500]}", file=sys.stderr)
        return None
    data = r.json()
    if not data.get("success"):
        return None
    for item in (data.get("data") or {}).get("items") or []:
        if item.get("name") == channel_name:
            return item
    return None


def _post_channel(cfg: dict, body: dict, dry_run: bool) -> bool:
    if dry_run:
        print(json.dumps(body, ensure_ascii=False, indent=2))
        return True
    base = cfg["base_url"].rstrip("/")
    url = f"{base}/api/channel/"
    r = ca._admin_request(cfg, "POST", url, json=body)
    if r.status_code != 200:
        print(f"创建渠道失败 HTTP {r.status_code}: {r.text}", file=sys.stderr)
        return False
    data = r.json()
    if not data.get("success"):
        print(f"创建渠道失败: {data.get('message', r.text)}", file=sys.stderr)
        return False
    return True


def _build_root_cfg(
    base_url: str,
    admin_user: str,
    admin_pass: str,
    root_user: str | None,
    root_pass: str | None,
    existing_cfg: dict | None,
) -> dict | None:
    """为 /api/option/ 使用 Root 会话。若与管理员同账号且已有 Session，则复用 existing_cfg。"""
    ru = (root_user or admin_user or "").strip()
    rp = root_pass if root_pass is not None else admin_pass
    if (
        existing_cfg
        and (root_user is None or root_user.strip() == (admin_user or "").strip())
        and (root_pass is None or root_pass == admin_pass)
    ):
        return existing_cfg
    s, uid = ca.admin_login(base_url, ru, rp or "")
    if s is None or uid is None:
        return None
    return {
        "base_url": base_url,
        "admin_session": s,
        "admin_user_id": str(uid),
    }


def _apply_pricing_merges(
    root_cfg: dict,
    desired: dict[str, dict[str, float]],
    dry_run: bool,
) -> bool:
    """GET 现网 JSON、合并、再 PUT 各 key。"""
    if not desired:
        return True
    ok = True
    for key, patch in desired.items():
        if not patch:
            continue
        current_s = _get_option_value(root_cfg, key)
        if current_s is None and not dry_run:
            print(
                f"[warn] 无法读取 Option {key}，跳过合并（/api/option/ 可能 403 或失败）",
                file=sys.stderr,
            )
            ok = False
            continue
        base_map = _option_json_to_map(current_s or "")
        for mk, mv in patch.items():
            base_map[mk] = _q4(mv)
        merged = _map_to_json(base_map)
        if not _put_option_key(root_cfg, key, merged, dry_run):
            ok = False
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="按官方目录向 NewAPI 导入多渠道（每渠道 Top2 模型）并可选同步全站倍率")
    ap.add_argument(
        "--catalog",
        type=Path,
        default=Path(__file__).resolve().parent / "vendor_models_official_catalog.json",
        help="vendor_models_official_catalog.json 路径",
    )
    ap.add_argument("--base-url", default=os.environ.get("NEWAPI_BASE_URL"), help="NewAPI 根 URL（或环境变量 NEWAPI_BASE_URL）")
    ap.add_argument("--admin-username", default=os.environ.get("NEWAPI_ADMIN_USERNAME"), help="管理员用户名")
    ap.add_argument("--admin-password", default=os.environ.get("NEWAPI_ADMIN_PASSWORD"), help="管理员密码")
    ap.add_argument(
        "--root-username",
        default=os.environ.get("NEWAPI_ROOT_USERNAME"),
        help="超级管理员用户名（改倍率用；或设 NEWAPI_ROOT_USERNAME；未设则与 --admin-username 相同）",
    )
    ap.add_argument(
        "--root-password",
        default=os.environ.get("NEWAPI_ROOT_PASSWORD"),
        help="超级管理员密码（或 NEWAPI_ROOT_PASSWORD；未设则与 admin 相同）",
    )
    ap.add_argument("--dry-run", action="store_true", help="仅打印将提交的 JSON，不调用接口（仍会登录以便与线上校验流程一致）")
    ap.add_argument(
        "--offline",
        action="store_true",
        help="不访问 NewAPI：仅根据目录打印拟创建的渠道 JSON（密钥用占位符，无需管理员账号）",
    )
    ap.add_argument("--force", action="store_true", help="若已存在同名渠道仍尝试创建（可能失败）")
    ap.add_argument("--top", type=int, default=2, help="每厂商取模型数（默认 2）")
    ap.add_argument(
        "--skip-pricing",
        action="store_true",
        help="不读取/不写入全站倍率（ModelRatio 等）",
    )
    ap.add_argument(
        "--fail-on-pricing",
        action="store_true",
        help="若倍率写入失败则不创建渠道（默认：倍率失败仍继续创建渠道，整体以非 0 退出表示部分失败）",
    )
    args = ap.parse_args()

    base_url = (args.base_url or "").rstrip("/")
    if args.offline:
        cfg = None
    else:
        if not base_url:
            print("请设置 NEWAPI_BASE_URL 或 --base-url", file=sys.stderr)
            return 1
        if not args.admin_username or not args.admin_password:
            print("请设置 NEWAPI_ADMIN_USERNAME / NEWAPI_ADMIN_PASSWORD 或命令行传入", file=sys.stderr)
            return 1
        session, user_id = ca.admin_login(base_url, args.admin_username, args.admin_password)
        if session is None or user_id is None:
            return 1
        cfg = {
            "base_url": base_url,
            "admin_session": session,
            "admin_user_id": str(user_id),
        }

    catalog = _load_catalog(args.catalog)
    top_n = int(args.top)
    meta = catalog.get("meta") or {}
    if "top_models_per_provider" in meta:
        top_n = min(top_n, int(meta["top_models_per_provider"]))

    usd_cny: float | None = _env_float("IMPORT_USD_CNY_RATE")
    quota_pu: float = 500_000.0
    if not args.offline and base_url:
        status_data = _fetch_status(base_url)
        if status_data:
            if usd_cny is None and status_data.get("usd_exchange_rate") is not None:
                try:
                    u = float(status_data["usd_exchange_rate"])
                    if u > 0:
                        usd_cny = u
                except (TypeError, ValueError):
                    pass
            if status_data.get("quota_per_unit") is not None:
                try:
                    q = float(status_data["quota_per_unit"])
                    if q > 0:
                        quota_pu = q
                except (TypeError, ValueError):
                    pass
    if not args.skip_pricing and not args.offline and (usd_cny is None or usd_cny <= 0) and not args.dry_run:
        print(
            "无法获得美元/人民币汇率：请设 IMPORT_USD_CNY_RATE 或保证 GET /api/status 的 usd_exchange_rate；已跳过全站倍率写入。",
            file=sys.stderr,
        )

    pricing_desired: dict[str, dict[str, float]] = {}
    if not args.skip_pricing:
        rate_for_calc: float | None = usd_cny if (usd_cny and usd_cny > 0) else None
        if rate_for_calc is None and (args.dry_run or args.offline):
            rate_for_calc = 7.3
        if rate_for_calc is not None:
            pricing_desired, _ = _merge_pricing_for_catalog(
                catalog, top_n, rate_for_calc, quota_pu
            )

    root_cfg: dict | None = None
    pricing_write_ok: bool = True
    if (
        pricing_desired
        and not args.skip_pricing
        and not args.offline
        and usd_cny
        and usd_cny > 0
    ):
        root_cfg = _build_root_cfg(
            base_url,
            args.admin_username or "",
            args.admin_password or "",
            args.root_username,
            args.root_password,
            cfg,
        )
        if root_cfg is None:
            print("无法登录超级管理员，已跳过倍率写入（需 Root 调 GET/PUT /api/option/）。", file=sys.stderr)
            pricing_write_ok = False
        else:
            mnames = list((pricing_desired.get("ModelRatio") or {}).keys())
            print(
                f"同步倍率: 1 USD = {usd_cny} CNY, quota_per_unit={quota_pu} "
                f"（{len(mnames)} 个模型: {', '.join(mnames[:8])}{'...' if len(mnames) > 8 else ''}）"
            )
            if args.dry_run:
                print("定价合并预览(四位小数):", json.dumps(pricing_desired, ensure_ascii=False, indent=2))
            if not _apply_pricing_merges(root_cfg, pricing_desired, args.dry_run):
                pricing_write_ok = False
        if not pricing_write_ok and args.fail_on_pricing:
            print("因 --fail-on-pricing 已中止，不再创建渠道。", file=sys.stderr)
            return 3
    elif (args.dry_run or args.offline) and not args.skip_pricing and pricing_desired and (usd_cny is None or usd_cny <= 0 or args.offline):
        rlab = usd_cny if (usd_cny and usd_cny > 0) else 7.3
        tag = "[offline] " if args.offline else "[dry-run] "
        print(
            f"{tag}倍率计算预览(未取到站点汇率时假定 1 USD = {rlab} CNY, quota_per_unit={quota_pu}):"
        )
        print(json.dumps(pricing_desired, ensure_ascii=False, indent=2))

    ok_all = True
    for p in catalog.get("providers") or []:
        ch_name = p["channel_name"]
        if cfg is not None and not args.force and not args.offline:
            existing = _find_channel_by_name(cfg, ch_name)
            if existing:
                print(f"跳过（已存在）: {ch_name} id={existing.get('id')}")
                continue

        key = _resolve_api_key(p)
        if args.offline:
            key = key or f"<{p.get('env_key_name', 'API_KEY')}>"
        elif args.dry_run and not key:
            key = f"<{p.get('env_key_name', 'API_KEY')}>"
        if not key:
            print(f"跳过（未设置密钥环境变量）: {p['id']} env={p.get('env_key_name')}", file=sys.stderr)
            ok_all = False
            continue

        model_ids = _top_model_ids(p.get("models") or [], top_n)
        if len(model_ids) < top_n:
            print(f"[warn] {p['id']} 模型不足 {top_n} 个，仅有: {model_ids}", file=sys.stderr)

        if args.fail_on_pricing and not args.skip_pricing and not pricing_write_ok:
            return 3

        body = {
            "mode": "single",
            "channel": {
                "name": ch_name,
                "type": int(p["newapi_channel_type"]),
                "key": key,
                "base_url": (p.get("default_base_url") or "").strip(),
                "models": ",".join(model_ids),
                "groups": ["default"],
                "priority": 0,
                "weight": 1,
            },
        }
        tag = "[offline] " if args.offline else ("[dry-run] " if args.dry_run else "")
        print(f"{tag}创建渠道: {ch_name} type={p['newapi_channel_type']} models={body['channel']['models']}")
        if args.offline:
            safe = json.loads(json.dumps(body))
            safe["channel"]["key"] = f"<{p.get('env_key_name', 'API_KEY')}>"
            print(json.dumps(safe, ensure_ascii=False, indent=2))
            continue
        if not _post_channel(cfg, body, args.dry_run):
            ok_all = False

    if not ok_all:
        return 2
    if not args.skip_pricing and not args.offline and not pricing_write_ok and bool(pricing_desired) and usd_cny and usd_cny > 0:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

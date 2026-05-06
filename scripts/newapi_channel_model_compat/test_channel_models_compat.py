#!/usr/bin/env python3
"""
枚举 NewAPI 已启用渠道及其模型，对每个模型调用管理端 GET /api/channel/test/:id
（与控制台「测试」同源），分别探测 endpoint_type=openai 与 anthropic。

鉴权复用 scripts/newapi_batch_accounts/create_account.py（Cookie 或 Token）。
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, TextIO
from urllib.parse import urlencode

try:
    import requests
except ImportError:
    print("需要 requests：pip install -r requirements.txt", file=sys.stderr)
    sys.exit(1)

_BATCH_DIR = Path(__file__).resolve().parent.parent / "newapi_batch_accounts"
sys.path.insert(0, str(_BATCH_DIR))
import create_account as ca  # noqa: E402

# 与上游 new-api controller/channel-test.go unsupportedTestChannelTypes 对齐
UNSUPPORTED_TEST_CHANNEL_TYPES: frozenset[int] = frozenset(
    {
        2,  # Midjourney
        5,  # MidjourneyPlus
        36,  # SunoAPI
        50,  # Kling
        51,  # Jimeng
        52,  # Vidu
        54,  # DoubaoVideo
    }
)


def _stdout_is_tty() -> bool:
    return sys.stdout.isatty()


def _term_palette(no_color: bool) -> dict[str, str]:
    if no_color or not _stdout_is_tty():
        return {k: "" for k in ("reset", "bold", "dim", "ok", "fail", "warn", "rule", "head")}
    return {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "dim": "\033[2m",
        "ok": "\033[32m",
        "fail": "\033[31m",
        "warn": "\033[33m",
        "rule": "\033[90m",
        "head": "\033[36m",
    }


def _ellipsize(s: str, max_len: int) -> str:
    s = s.replace("\n", " ").strip()
    if len(s) <= max_len:
        return s
    if max_len <= 1:
        return "…"
    return s[: max_len - 1] + "…"


def _fmt_cell(s: str, width: int, align: str = "<") -> str:
    t = _ellipsize(s, width)
    if align == "<":
        return t.ljust(width)
    if align == ">":
        return t.rjust(width)
    return t.center(width)


TABLE_COL_WIDTHS: tuple[int, ...] = (6, 22, 26, 14, 14)


def _table_outer_line(widths: tuple[int, ...], *, sep: str = "-") -> str:
    return "+" + "+".join(sep * (w + 2) for w in widths) + "+"


def _table_row_line(widths: tuple[int, ...], cells: tuple[str, ...]) -> str:
    parts: list[str] = []
    for w, cell in zip(widths, cells, strict=True):
        parts.append(" " + _fmt_cell(cell, w) + " ")
    return "|" + "|".join(parts) + "|"


def _fmt_probe_cell(p: dict[str, Any] | None, width: int) -> str:
    """纯文本单元格，便于等宽对齐（不含 ANSI）。"""
    if p is None:
        return _fmt_cell("—", width)
    ok = bool(p.get("success"))
    t = p.get("time")
    ts = f"{float(t):.2f}s" if isinstance(t, (int, float)) else (str(t) if t not in (None, "") else "?")
    sym = "+" if ok else "x"
    return _fmt_cell(f"{sym} {ts}", width)


def _fmt_probe_fail_hint(
    p: dict[str, Any] | None, max_len: int, c: dict[str, str], label: str
) -> str | None:
    if p is None or p.get("success"):
        return None
    msg = (p.get("message") or "").strip()
    if not msg:
        return None
    line = _ellipsize(msg, max_len)
    return f"{c['dim']}    {label}: {line}{c['reset']}"


def _print_run_header(
    *,
    base_url: str,
    only: str,
    channel_ids: str,
    max_models: int,
    stream: str,
    sleep: float,
    c: dict[str, str],
    out: TextIO,
) -> None:
    b, r, d, h = c["bold"], c["reset"], c["dim"], c["head"]
    w = 72
    line = "═" * w
    print(f"{h}{line}{r}", file=out)
    print(f"{h}  NewAPI 渠道模型 · OpenAI / Anthropic 兼容探测{r}", file=out)
    print(f"{h}{line}{r}", file=out)
    print(f"  {b}网关{r}     {base_url}", file=out)
    print(f"  {b}模式{r}     {only}", file=out)
    extras: list[str] = []
    if channel_ids.strip():
        extras.append(f"渠道 ID 过滤: {channel_ids.strip()}")
    if max_models > 0:
        extras.append(f"每渠道最多模型数: {max_models}")
    if sleep > 0:
        extras.append(f"请求间隔: {sleep}s")
    if stream != "omit":
        extras.append(f"stream={stream}")
    if extras:
        print(f"  {b}选项{r}     {' · '.join(extras)}", file=out)
    print(f"{d}{'─' * w}{r}", file=out)


def _print_table_header(only: str, c: dict[str, str], out: TextIO) -> None:
    ru, rs = c["rule"], c["reset"]
    w = TABLE_COL_WIDTHS
    if only == "openai":
        lab_o, lab_a = "OpenAI", "—"
    elif only == "anthropic":
        lab_o, lab_a = "—", "Anthropic"
    else:
        lab_o, lab_a = "OpenAI", "Anthropic"
    line_plain = _table_outer_line(w)
    line = f"{ru}{line_plain}{rs}"
    print(line, file=out)
    head_plain = _table_row_line(
        w,
        (
            _fmt_cell("ID", w[0], ">"),
            _fmt_cell("渠道", w[1]),
            _fmt_cell("模型", w[2]),
            _fmt_cell(lab_o, w[3], "^"),
            _fmt_cell(lab_a, w[4], "^"),
        ),
    )
    print(f"{ru}{head_plain}{rs}", file=out)
    print(line, file=out)


def _print_table_row(
    cid: int,
    cname: str,
    model_disp: str,
    openai_p: dict[str, Any] | None,
    anthropic_p: dict[str, Any] | None,
    *,
    c: dict[str, str],
    only: str,
    out: TextIO,
) -> None:
    ru, rs = c["rule"], c["reset"]
    w = TABLE_COL_WIDTHS
    o_cell = _fmt_probe_cell(openai_p, w[3]) if only in ("openai", "both") else _fmt_cell("—", w[3])
    a_cell = _fmt_probe_cell(anthropic_p, w[4]) if only in ("anthropic", "both") else _fmt_cell("—", w[4])
    row_plain = _table_row_line(
        w,
        (
            _fmt_cell(str(cid), w[0], ">"),
            _fmt_cell(cname, w[1]),
            _fmt_cell(model_disp, w[2]),
            o_cell,
            a_cell,
        ),
    )
    print(f"{ru}{row_plain}{rs}", file=out)
    hint_w = sum(w) + 14
    if only in ("openai", "both"):
        m = _fmt_probe_fail_hint(openai_p, hint_w, c, "OpenAI")
        if m:
            print(m, file=out)
    if only in ("anthropic", "both"):
        m = _fmt_probe_fail_hint(anthropic_p, hint_w, c, "Anthropic")
        if m:
            print(m, file=out)


def _print_channel_banner(cid: int, cname: str, ctype: int, c: dict[str, str], out: TextIO) -> None:
    d, b, h, r = c["dim"], c["bold"], c["head"], c["reset"]
    title = _ellipsize(f"{cname} (type={ctype})", 64)
    print(f"\n{d}──{r} {h}{b}渠道 {cid}{r} {h}·{r} {title} {d}{'─' * 12}{r}", file=out)


def _print_skip_channel(cid: int, cname: str, ctype: int, reason: str, c: dict[str, str], out: TextIO) -> None:
    w = c["warn"]
    r = c["reset"]
    d = c["dim"]
    print(
        f"\n{w}跳过渠道{r} {d}#{cid}{r} {_ellipsize(cname, 40)} {d}(type={ctype}){r}\n  {d}{reason}{r}",
        file=out,
    )


def _print_footer_summary(
    *,
    counts: dict[str, int],
    any_fail: bool,
    any_strict_skip: bool,
    strict: bool,
    c: dict[str, str],
    out: TextIO,
) -> None:
    b, r, d, ok, fl, wn = c["bold"], c["reset"], c["dim"], c["ok"], c["fail"], c["warn"]
    w = 56
    print(f"\n{d}{'─' * w}{r}", file=out)
    print(f"{b}汇总{r}", file=out)
    oa_ran = counts["oa_ok"] + counts["oa_fail"]
    an_ran = counts["an_ok"] + counts["an_fail"]
    print(
        f"  渠道数: {counts['channels']} · 数据行: {counts['rows']}",
        file=out,
    )
    if oa_ran:
        print(
            f"  OpenAI     {ok}通过 {counts['oa_ok']}{r}  ·  {fl}失败 {counts['oa_fail']}{r}"
            f"  {d}(合计 {oa_ran} 次){r}",
            file=out,
        )
    if an_ran:
        print(
            f"  Anthropic  {ok}通过 {counts['an_ok']}{r}  ·  {fl}失败 {counts['an_fail']}{r}"
            f"  {d}(合计 {an_ran} 次){r}",
            file=out,
        )
    if counts["skipped_channels"]:
        print(f"  {wn}跳过渠道（类型不支持 test）: {counts['skipped_channels']}{r}", file=out)
    if any_fail:
        print(f"  {fl}{b}结论: 存在失败用例（退出码 1）{r}", file=out)
    elif strict and any_strict_skip:
        print(f"  {wn}{b}结论: --strict 且存在跳过渠道（退出码 1）{r}", file=out)
    else:
        print(f"  {ok}{b}结论: 本次探测全部通过{r}", file=out)
    print(f"{d}{'─' * w}{r}\n", file=out)


def _parse_models_field(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        out = [str(x).strip() for x in raw if str(x).strip()]
        return list(dict.fromkeys(out))
    s = str(raw).strip()
    if not s:
        return []
    parts = re.split(r"[\n,，;；]+", s)
    out = [p.strip() for p in parts if p.strip()]
    return list(dict.fromkeys(out))


def _build_cfg(args: argparse.Namespace) -> dict | None:
    base_url = (args.base_url or os.environ.get("NEWAPI_BASE_URL", "")).rstrip("/")
    if not base_url:
        print("错误: 请设置 NEWAPI_BASE_URL 或 --base-url", file=sys.stderr)
        return None

    token = args.admin_token or os.environ.get("NEWAPI_ADMIN_TOKEN")
    user_id = args.admin_user_id or os.environ.get("NEWAPI_ADMIN_USER_ID")
    username = args.admin_username or os.environ.get("NEWAPI_ADMIN_USERNAME")
    password = args.admin_password or os.environ.get("NEWAPI_ADMIN_PASSWORD")

    if token and user_id:
        return {
            "base_url": base_url,
            "admin_session": None,
            "admin_token": token.strip(),
            "admin_user_id": str(user_id).strip(),
        }
    if username and password:
        session, uid = ca.admin_login(base_url, username, password)
        if session is None or uid is None:
            return None
        return {
            "base_url": base_url,
            "admin_session": session,
            "admin_token": None,
            "admin_user_id": str(uid),
        }
    print(
        "错误: 请提供管理员鉴权："
        "NEWAPI_ADMIN_USERNAME + NEWAPI_ADMIN_PASSWORD，或 "
        "NEWAPI_ADMIN_TOKEN + NEWAPI_ADMIN_USER_ID",
        file=sys.stderr,
    )
    return None


def _fetch_all_enabled_channels(cfg: dict, page_size: int) -> list[dict]:
    base = cfg["base_url"].rstrip("/")
    all_items: list[dict] = []
    page = 1
    ps = min(max(1, page_size), 100)
    while True:
        url = f"{base}/api/channel/"
        r = ca._admin_request(
            cfg,
            "GET",
            url,
            params={"status": "enabled", "p": page, "page_size": ps},
            timeout=60,
        )
        if r.status_code != 200:
            print(f"获取渠道列表失败 HTTP {r.status_code}: {r.text[:800]}", file=sys.stderr)
            break
        data = r.json()
        if not data.get("success"):
            print(f"获取渠道列表失败: {data.get('message', r.text[:500])}", file=sys.stderr)
            break
        inner = data.get("data") or {}
        items = inner.get("items") or []
        if not items:
            break
        all_items.extend(items)
        if len(items) < ps:
            break
        page += 1
    return all_items


def _channel_test(
    cfg: dict,
    channel_id: int,
    model: str | None,
    endpoint_type: str,
    stream: bool | None,
    timeout: float,
) -> dict[str, Any]:
    base = cfg["base_url"].rstrip("/")
    q: dict[str, str] = {"endpoint_type": endpoint_type}
    if model is not None and model != "":
        q["model"] = model
    if stream is not None:
        q["stream"] = "true" if stream else "false"
    qs = urlencode(q)
    url = f"{base}/api/channel/test/{int(channel_id)}?{qs}"
    start = time.perf_counter()
    r = ca._admin_request(cfg, "GET", url, timeout=timeout)
    elapsed = time.perf_counter() - start
    try:
        body = r.json()
    except Exception:
        return {
            "http_status": r.status_code,
            "success": False,
            "message": r.text[:500] if r.text else "(empty body)",
            "time": round(elapsed, 3),
            "error_code": None,
        }
    if r.status_code != 200:
        return {
            "http_status": r.status_code,
            "success": False,
            "message": body.get("message") or str(body)[:500],
            "time": body.get("time", round(elapsed, 3)),
            "error_code": body.get("error_code"),
        }
    return {
        "http_status": r.status_code,
        "success": bool(body.get("success")),
        "message": (body.get("message") or "")[:2000],
        "time": body.get("time"),
        "error_code": body.get("error_code"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(
        description="对已启用 NewAPI 渠道的每个模型做 openai / anthropic 管理端连通性测试（GET /api/channel/test/:id）。"
    )
    ap.add_argument("--base-url", default=os.environ.get("NEWAPI_BASE_URL"), help="NewAPI 根 URL")
    ap.add_argument("--admin-username", default=os.environ.get("NEWAPI_ADMIN_USERNAME"))
    ap.add_argument("--admin-password", default=os.environ.get("NEWAPI_ADMIN_PASSWORD"))
    ap.add_argument("--admin-token", default=os.environ.get("NEWAPI_ADMIN_TOKEN"))
    ap.add_argument("--admin-user-id", default=os.environ.get("NEWAPI_ADMIN_USER_ID"))
    ap.add_argument(
        "--only",
        choices=("openai", "anthropic", "both"),
        default="both",
        help="探测的 endpoint_type（默认 both）",
    )
    ap.add_argument(
        "--channel-ids",
        default="",
        help="仅测试这些渠道 ID，逗号分隔，例如 1,2,3",
    )
    ap.add_argument("--max-models", type=int, default=0, help="每个渠道最多测前 N 个模型；0 表示不限制")
    ap.add_argument("--page-size", type=int, default=100, help="拉取渠道列表的分页大小（最大 100）")
    ap.add_argument("--sleep", type=float, default=0.0, help="每次 test 请求后的休眠秒数")
    ap.add_argument(
        "--stream",
        choices=("true", "false", "omit"),
        default="omit",
        help="是否传 stream 查询参数；omit=不传（由服务端默认）",
    )
    ap.add_argument("--timeout", type=float, default=120.0, help="单次 test 请求超时（秒）")
    ap.add_argument("--json-out", type=Path, default=None, help="将完整结果写入 JSON 文件")
    ap.add_argument(
        "--strict",
        action="store_true",
        help="若存在因渠道类型而跳过的渠道，也以非零退出码结束",
    )
    ap.add_argument(
        "--no-color",
        action="store_true",
        help="关闭 ANSI 颜色（默认可在 TTY 下着色）",
    )
    ap.add_argument(
        "--emit-json-summary",
        action="store_true",
        help="结束时额外打印一行 JSON 汇总（便于脚本解析）",
    )
    args = ap.parse_args()

    stream_val: bool | None
    if args.stream == "omit":
        stream_val = None
    else:
        stream_val = args.stream == "true"

    cfg = _build_cfg(args)
    if cfg is None:
        return 1

    id_filter: set[int] | None = None
    if args.channel_ids.strip():
        id_filter = set()
        for part in args.channel_ids.split(","):
            part = part.strip()
            if part:
                id_filter.add(int(part))

    channels = _fetch_all_enabled_channels(cfg, args.page_size)
    if id_filter is not None:
        channels = [c for c in channels if int(c.get("id", -1)) in id_filter]

    pal = _term_palette(args.no_color)
    _print_run_header(
        base_url=cfg["base_url"],
        only=args.only,
        channel_ids=args.channel_ids,
        max_models=args.max_models,
        stream=args.stream,
        sleep=args.sleep,
        c=pal,
        out=sys.stdout,
    )

    rows: list[dict[str, Any]] = []
    any_fail = False
    any_strict_skip = False
    counts = {
        "channels": len(channels),
        "rows": 0,
        "oa_ok": 0,
        "oa_fail": 0,
        "an_ok": 0,
        "an_fail": 0,
        "skipped_channels": 0,
    }

    if not channels:
        print(f"{pal['dim']}（没有符合条件的已启用渠道）{pal['reset']}", file=sys.stdout)
    else:
        has_probe_target = any(
            int(ch.get("type", -1)) not in UNSUPPORTED_TEST_CHANNEL_TYPES for ch in channels
        )
        if has_probe_target:
            _print_table_header(args.only, pal, sys.stdout)
        else:
            print(
                f"{pal['warn']}当前列表中的渠道均不支持管理端 test（如 Midjourney / Suno 等），无探测表格。{pal['reset']}",
                file=sys.stdout,
            )

        for ch in channels:
            cid = int(ch["id"])
            cname = str(ch.get("name") or "")
            ctype = int(ch.get("type", -1))

            if ctype in UNSUPPORTED_TEST_CHANNEL_TYPES:
                any_strict_skip = True
                counts["skipped_channels"] += 1
                rows.append(
                    {
                        "channel_id": cid,
                        "channel_name": cname,
                        "channel_type": ctype,
                        "model": None,
                        "skipped_channel": True,
                        "skip_reason": f"渠道类型 {ctype} 不支持管理端渠道测试（与 NewAPI 一致）",
                        "openai": None,
                        "anthropic": None,
                    }
                )
                _print_skip_channel(
                    cid,
                    cname,
                    ctype,
                    "该渠道类型不支持 GET /api/channel/test（与 NewAPI 内置列表一致）",
                    pal,
                    sys.stdout,
                )
                continue

            _print_channel_banner(cid, cname, ctype, pal, sys.stdout)

            models = _parse_models_field(ch.get("models"))
            if args.max_models > 0:
                models = models[: args.max_models]

            if not models:
                models_to_run: list[str | None] = [None]
                display_model = "(默认/空模型)"
            else:
                models_to_run = list(models)
                display_model = None

            for m in models_to_run:
                dm = display_model if display_model is not None else (m or "")
                row: dict[str, Any] = {
                    "channel_id": cid,
                    "channel_name": cname,
                    "channel_type": ctype,
                    "model": dm,
                    "skipped_channel": False,
                    "skip_reason": None,
                    "openai": None,
                    "anthropic": None,
                }
                o = None
                a = None

                if args.only in ("openai", "both"):
                    o = _channel_test(cfg, cid, m, "openai", stream_val, args.timeout)
                    row["openai"] = o
                    if o.get("success"):
                        counts["oa_ok"] += 1
                    else:
                        counts["oa_fail"] += 1
                        any_fail = True
                    if args.sleep > 0:
                        time.sleep(args.sleep)

                if args.only in ("anthropic", "both"):
                    a = _channel_test(cfg, cid, m, "anthropic", stream_val, args.timeout)
                    row["anthropic"] = a
                    if a.get("success"):
                        counts["an_ok"] += 1
                    else:
                        counts["an_fail"] += 1
                        any_fail = True
                    if args.sleep > 0:
                        time.sleep(args.sleep)

                _print_table_row(
                    cid,
                    cname,
                    str(dm),
                    o,
                    a,
                    c=pal,
                    only=args.only,
                    out=sys.stdout,
                )
                rows.append(row)

        if has_probe_target:
            print(f"{pal['rule']}{_table_outer_line(TABLE_COL_WIDTHS)}{pal['reset']}", file=sys.stdout)

    counts["rows"] = len(rows)

    summary = {
        "channels_total": counts["channels"],
        "rows": counts["rows"],
        "openai_ok": counts["oa_ok"],
        "openai_fail": counts["oa_fail"],
        "anthropic_ok": counts["an_ok"],
        "anthropic_fail": counts["an_fail"],
        "skipped_channels": counts["skipped_channels"],
        "any_probe_failed": any_fail,
        "any_channel_type_skipped": any_strict_skip,
    }

    if args.json_out is not None:
        out_obj = {"summary": summary, "results": rows}
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(out_obj, f, ensure_ascii=False, indent=2)

    _print_footer_summary(
        counts=counts,
        any_fail=any_fail,
        any_strict_skip=any_strict_skip,
        strict=args.strict,
        c=pal,
        out=sys.stdout,
    )

    if args.emit_json_summary:
        print(json.dumps(summary, ensure_ascii=False), file=sys.stdout)

    if any_fail:
        return 1
    if args.strict and any_strict_skip:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

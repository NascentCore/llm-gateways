#!/usr/bin/env python3
"""
四模型（或任意 --models 列表）× 多档输入 token × 双路线流式剖面：首行指令 + tiktoken 定长填充，
max_tokens = input_tokens / output_ratio（默认 200:1，floor/ceil 可选）。

指标（每路线、每模型、每输入档一批完成后打印）：
  RPM  ≈ samples / wall_s * 60
  TPM  ≈ sum(usage.total_tokens) / wall_s * 60（缺 usage 时记 null）
  TTFT mean/p50/p95
  TPS  成功样本：completion_tokens / max(total_s - ttft_s, 1e-9)（total/ttft 均相对同一起点）

tiktoken 仅用于构造用户消息近似长度；计费以响应 usage 为准。勿将 API Key 写入仓库。
默认遇 **429 / 上游限流** 立即中止当前 cell（**退出码 3**），无自动 sleep；可用 `--no-abort-on-429` 改为尽量跑满样本。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, TextIO

import tiktoken
from openai import AsyncOpenAI

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

DEFAULT_BASE_URL = "https://api.mixroute.ai/v1"
_DEFAULT_INSTRUCTION = "请按指令输出一段《哈利波特》风格短文。"
_FILLER_UNIT = " The quick brown fox jumps over the lazy dog."


def _safe_model_filename(model: str) -> str:
    return (
        model.replace("/", "_")
        .replace(":", "_")
        .replace(" ", "_")
        .replace("\\", "_")
    )


def _normalize_base_url(url: str) -> str:
    u = url.rstrip("/")
    return u or DEFAULT_BASE_URL


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return float("nan")
    xs = sorted(vals)
    if len(xs) == 1:
        return xs[0]
    k = (len(xs) - 1) * (p / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return xs[int(k)]
    return xs[f] * (c - k) + xs[c] * (k - f)


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def _is_rate_limit_429(exc: BaseException) -> bool:
    """识别 429 / 上游饱和类限流（用于立即中止，不做自动重试）。"""
    if type(exc).__name__ == "RateLimitError":
        return True
    code = getattr(exc, "status_code", None)
    if code == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or ("rate" in msg and "limit" in msg) or "负载已饱和" in msg


class ProbeAbort429(Exception):
    """同 cell 内首次 429 后中止整批；无 sleep，由操作者择时重跑脚本。"""


def _delta_first_token(delta: Any) -> tuple[bool, str]:
    if delta is None:
        return False, ""
    c = getattr(delta, "content", None)
    if isinstance(c, str) and c.strip():
        return True, "content"
    for attr in ("reasoning_content", "reasoning", "thought", "thought_signature"):
        v = getattr(delta, attr, None)
        if isinstance(v, str) and v.strip():
            return True, attr
    if hasattr(delta, "model_dump"):
        raw = delta.model_dump(exclude_unset=True)
        for k, v in raw.items():
            if k in (
                "content",
                "reasoning_content",
                "role",
                "refusal",
                "function_call",
                "tool_calls",
            ):
                continue
            if isinstance(v, str) and v.strip():
                return True, k
            if isinstance(v, list) and v:
                return True, k
            if isinstance(v, dict):
                for sk, sv in v.items():
                    if isinstance(sv, str) and sv.strip():
                        return True, f"{k}.{sk}"
                    if isinstance(sv, list) and sv:
                        return True, f"{k}.{sk}"
    return False, ""


def _chunk_first_token(chunk: Any) -> tuple[bool, str]:
    ch0 = chunk.choices[0] if getattr(chunk, "choices", None) else None
    if ch0 is None:
        return False, ""
    return _delta_first_token(getattr(ch0, "delta", None))


def build_instruction_padded_user_text(
    instruction_first_line: str,
    target_tokens: int,
    encoding_name: str,
) -> str:
    """首行指令（可含换行，以第一行语义为主）+ 填充至恰好 target_tokens 个 tiktoken。"""
    if target_tokens < 1:
        return ""
    enc = tiktoken.get_encoding(encoding_name)
    first = instruction_first_line.strip() if instruction_first_line else _DEFAULT_INSTRUCTION
    if not first.endswith("\n"):
        first = first + "\n"
    prefix_ids = enc.encode(first)
    if len(prefix_ids) >= target_tokens:
        ids = prefix_ids[:target_tokens]
    else:
        rest = target_tokens - len(prefix_ids)
        rnd = secrets.token_hex(32)
        filler = f"{_FILLER_UNIT}{rnd}\n"
        fill_ids: list[int] = []
        while len(fill_ids) < rest + 256:
            fill_ids.extend(enc.encode(filler))
            filler = f"{_FILLER_UNIT}{secrets.token_hex(16)}\n"
        ids = prefix_ids + fill_ids[:rest]
    text = enc.decode(ids)
    actual = len(enc.encode(text))
    if actual != target_tokens:
        print(
            f"错误: 指令+填充在「{encoding_name}」下为 {actual} tokens，目标 {target_tokens}",
            file=sys.stderr,
        )
        sys.exit(3)
    return text


def max_tokens_for_input(
    input_tokens: int,
    output_ratio: int,
    rounding: str,
) -> int:
    if output_ratio < 1:
        print("错误: --output-ratio 须 >= 1", file=sys.stderr)
        sys.exit(2)
    x = input_tokens / float(output_ratio)
    if rounding == "floor":
        v = int(math.floor(x))
    elif rounding == "ceil":
        v = int(math.ceil(x))
    else:
        print("错误: --max-tokens-rounding 须为 floor 或 ceil", file=sys.stderr)
        sys.exit(2)
    return max(1, v)


def parse_samples_by_input(spec: str | None, inputs: list[int], default: int) -> dict[int, int]:
    out = {n: default for n in inputs}
    if not spec:
        return out
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            print(f"错误: --samples-by-input 段无效: {part}", file=sys.stderr)
            sys.exit(2)
        k, v = part.split(":", 1)
        n = int(k.strip())
        c = int(v.strip())
        if n not in out:
            print(f"错误: --samples-by-input 含未知输入档 {n}", file=sys.stderr)
            sys.exit(2)
        out[n] = max(0, c)
    return out


def _truncate_text(s: str, max_chars: int | None, no_truncate: bool) -> tuple[str, bool]:
    if no_truncate or max_chars is None or len(s) <= max_chars:
        return s, False
    return s[:max_chars], True


async def _consume_stream_profile(
    stream: Any,
    t0: float,
) -> tuple[float | None, str, float | None, dict[str, Any] | None, str, bool]:
    """
    返回 (ttft_s_from_t0, first_kind, total_s, usage_dict, output_text, output_truncated)。
    total_s 为从 t0 到最后一个「含内容 delta」的 chunk 的墙钟；若仅有 usage 终块，则退化为最后 chunk。
    """
    ttft: float | None = None
    first_kind = ""
    usage: dict[str, Any] | None = None
    parts: list[str] = []
    last_content_wall: float | None = None
    last_any_wall: float | None = None
    async for chunk in stream:
        now = time.perf_counter()
        last_any_wall = now
        ch0 = chunk.choices[0] if getattr(chunk, "choices", None) else None
        delta = getattr(ch0, "delta", None) if ch0 else None
        c = getattr(delta, "content", None) if delta else None
        rc = getattr(delta, "reasoning_content", None) if delta else None
        rs = getattr(delta, "reasoning", None) if delta else None
        if isinstance(c, str) and c:
            parts.append(c)
            last_content_wall = now
        elif isinstance(rc, str) and rc:
            parts.append(rc)
            last_content_wall = now
        elif isinstance(rs, str) and rs:
            parts.append(rs)
            last_content_wall = now
        elif isinstance(rs, dict) and rs:
            try:
                blob = json.dumps(rs, ensure_ascii=False)[:4000]
            except (TypeError, ValueError):
                blob = str(rs)[:4000]
            if blob.strip():
                parts.append(blob)
                last_content_wall = now
        if ttft is None:
            hit, kind = _chunk_first_token(chunk)
            if hit:
                ttft = now - t0
                first_kind = kind
                if last_content_wall is None:
                    last_content_wall = now
        u = getattr(chunk, "usage", None)
        if u is not None and hasattr(u, "model_dump"):
            usage = u.model_dump()
        elif u is not None:
            usage = {"repr": repr(u)[:200]}
    end_wall = last_content_wall if last_content_wall is not None else last_any_wall
    total_s = (end_wall - t0) if end_wall is not None else None
    return ttft, first_kind, total_s, usage, "".join(parts), False


async def one_stream_completion(
    client: AsyncOpenAI,
    model: str,
    input_tokens_target: int,
    user_content: str,
    max_tokens: int,
    stream_timeout: float,
    route_id: str,
    idx: int,
    jsonl_fp: TextIO | None,
    truncate_chars: int | None,
    no_truncate: bool,
    abort_on_429: bool = True,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "route_id": route_id,
        "i": idx,
        "model": model,
        "input_tokens_target": input_tokens_target,
        "max_tokens": max_tokens,
        "ok": False,
        "ttft_s": None,
        "total_s": None,
        "gen_s": None,
        "tps_output": None,
        "tps_approx": False,
        "first_kind": "",
        "usage": None,
        "output_text": "",
        "output_truncated": False,
        "error": "",
    }
    t0 = time.perf_counter()
    abort_after_write = False

    async def _run() -> None:
        stream = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user_content}],
            max_tokens=max_tokens,
            stream=True,
        )
        ttft, first_kind, total_s, usage, text, _ = await _consume_stream_profile(stream, t0)
        rec["first_kind"] = first_kind
        rec["usage"] = usage
        ot, was_trunc = _truncate_text(text, truncate_chars, no_truncate)
        rec["output_text"] = ot
        rec["output_truncated"] = was_trunc
        wall_full = time.perf_counter() - t0
        if ttft is None:
            ct0 = 0
            if usage and isinstance(usage.get("completion_tokens"), int):
                ct0 = int(usage["completion_tokens"])
            if ct0 > 0:
                # 部分上游在极小 max_tokens 或 reasoning 形态下不在 delta 中暴露可解析首包，但 usage 有 completion
                rec["ok"] = True
                rec["ttft_s"] = None
                rec["total_s"] = round(wall_full, 6)
                rec["gen_s"] = round(wall_full, 6)
                rec["first_kind"] = "usage_only_no_stream_delta"
                rec["tps_output"] = round(ct0 / max(wall_full, 1e-9), 4)
                rec["tps_approx"] = True
                return
            rec["error"] = "no_first_token_chunk"
            rec["total_s"] = round(wall_full, 6)
            return
        rec["ttft_s"] = round(ttft, 6)
        rec["total_s"] = round(wall_full, 6)
        ts_stream = total_s if total_s is not None else wall_full
        rec["gen_s"] = round(max(ts_stream - ttft, 0.0), 6)
        ct: int | None = None
        if usage:
            ct = usage.get("completion_tokens")
            if isinstance(ct, int) and ct > 0 and rec["gen_s"] is not None and rec["gen_s"] > 1e-9:
                rec["tps_output"] = round(ct / max(float(rec["gen_s"]), 1e-9), 4)
            elif isinstance(ct, int) and ct > 0:
                rec["tps_output"] = round(ct / max(wall_full, 1e-9), 4)
        if rec["tps_output"] is None and text:
            approx = len(text) / max(float(rec["gen_s"] or wall_full), 1e-9)
            rec["tps_output"] = round(approx, 4)
            rec["tps_approx"] = True
        rec["ok"] = True

    try:
        await asyncio.wait_for(_run(), timeout=stream_timeout)
    except TimeoutError:
        rec["total_s"] = round(time.perf_counter() - t0, 6)
        rec["error"] = "TimeoutError"
    except Exception as e:
        rec["total_s"] = round(time.perf_counter() - t0, 6)
        rec["error"] = f"{type(e).__name__}: {e}"[:800]
        if abort_on_429 and _is_rate_limit_429(e):
            abort_after_write = True
    finally:
        if jsonl_fp:
            jsonl_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
            jsonl_fp.flush()
    # 注：不能在 except 里直接 raise 再依赖 finally 写盘；用标志在 flush 后中止。
    if abort_after_write:
        raise ProbeAbort429(rec.get("error", "")[:500])
    return rec


async def run_cell(
    client: AsyncOpenAI,
    model: str,
    input_tokens: int,
    user_content: str,
    max_tokens: int,
    samples: int,
    route_id: str,
    jsonl_fp: TextIO | None,
    stream_timeout: float,
    intra_concurrency: int,
    truncate_chars: int | None,
    no_truncate: bool,
    raw_jsonl_path: str | None = None,
    abort_on_429: bool = True,
) -> dict[str, Any]:
    sem = asyncio.Semaphore(max(1, intra_concurrency))
    wall0 = time.perf_counter()

    async def _one(i: int) -> dict[str, Any]:
        async with sem:
            return await one_stream_completion(
                client,
                model,
                input_tokens,
                user_content,
                max_tokens,
                stream_timeout,
                route_id,
                i + 1,
                jsonl_fp,
                truncate_chars,
                no_truncate,
                abort_on_429=abort_on_429,
            )

    try:
        async with asyncio.TaskGroup() as tg:
            tasks = [tg.create_task(_one(i)) for i in range(samples)]
    except* ProbeAbort429 as eg:
        err0 = str(eg.exceptions[0])
        print(
            f"遇 429，已中止本 cell（已取消未完成的同档并发请求）: {err0[:400]}",
            flush=True,
        )
        raise ProbeAbort429(err0) from eg

    rows = [t.result() for t in tasks]
    wall = time.perf_counter() - wall0

    oks = [r for r in rows if r.get("ok")]
    fails = [r for r in rows if not r.get("ok")]
    ttfts = [float(r["ttft_s"]) for r in oks if r.get("ttft_s") is not None]
    tps_list = [float(r["tps_output"]) for r in oks if r.get("tps_output") is not None]

    total_usage_tokens = 0
    usage_count = 0
    for r in oks:
        u = r.get("usage")
        if isinstance(u, dict) and u.get("total_tokens") is not None:
            try:
                total_usage_tokens += int(u["total_tokens"])
                usage_count += 1
            except (TypeError, ValueError):
                pass

    rpm = (60.0 * len(rows) / wall) if wall > 0 else 0.0
    tpm = (60.0 * total_usage_tokens / wall) if wall > 0 and usage_count > 0 else float("nan")

    summary = {
        "route_id": route_id,
        "model": model,
        "input_tokens_target": input_tokens,
        "max_tokens": max_tokens,
        "samples": samples,
        "n_ok": len(oks),
        "n_fail": len(fails),
        "wall_s": round(wall, 4),
        "rpm_requests": round(rpm, 4),
        "tpm_total_tokens": round(tpm, 4) if not math.isnan(tpm) else None,
        "mean_ttft_s": round(_mean(ttfts), 4) if ttfts else None,
        "p50_ttft_s": round(_percentile(ttfts, 50), 4) if ttfts else None,
        "p95_ttft_s": round(_percentile(ttfts, 95), 4) if ttfts else None,
        "mean_tps_output": round(_mean(tps_list), 4) if tps_list else None,
        "p50_tps_output": round(_percentile(tps_list, 50), 4) if tps_list else None,
        "fail_errors": _fail_summary(fails),
    }
    if raw_jsonl_path is not None:
        summary["raw_jsonl_path"] = raw_jsonl_path
    return summary


def _fail_summary(fails: list[dict[str, Any]]) -> str:
    if not fails:
        return ""
    counts: dict[str, int] = {}
    for r in fails:
        e = (r.get("error") or "unknown")[:120]
        counts[e] = counts.get(e, 0) + 1
    parts = [f"{k}:{v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])[:5]]
    return "; ".join(parts)


def _print_cell_banner() -> None:
    print(
        "note=tiktoken 仅用于构造用户消息长度；RPM=requests/wall*60；TPM=sum(usage.total_tokens)/wall*60；"
        "TTFT=从发起 create 到首 token chunk；TPS=completion_tokens/max(gen_s,eps) 或字符粗估",
        flush=True,
    )


async def async_route_worker(args: argparse.Namespace) -> int:
    base_url = _normalize_base_url(args.base_url)
    api_key = args.api_key or os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 未设置 API Key", file=sys.stderr)
        return 2

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    inputs = [int(x.strip()) for x in args.input_tokens.split(",") if x.strip()]
    samples_map = parse_samples_by_input(args.samples_by_input, inputs, args.samples)

    jsonl_layout = getattr(args, "jsonl_layout", "flat")
    jsonl_path: Path | None = Path(args.jsonl_out) if args.jsonl_out else None
    jsonl_fp: TextIO | None = None
    flat_path_resolved: str | None = None
    if jsonl_layout == "flat" and jsonl_path:
        jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        jsonl_fp = jsonl_path.open("a", encoding="utf-8")
        flat_path_resolved = str(jsonl_path.resolve())
    elif jsonl_layout == "nested":
        if not jsonl_path:
            print("错误: --jsonl-layout nested 须指定 --jsonl-out 为目录路径", file=sys.stderr)
            return 2
        jsonl_path.mkdir(parents=True, exist_ok=True)
        (jsonl_path / "cells").mkdir(parents=True, exist_ok=True)

    summary_fp: TextIO | None = None
    if args.summary_jsonl:
        sp = Path(args.summary_jsonl)
        sp.parent.mkdir(parents=True, exist_ok=True)
        summary_fp = sp.open("a", encoding="utf-8")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=args.stream_timeout,
        max_retries=0,
    )

    truncate = None if args.no_truncate else args.truncate_response_chars

    _print_cell_banner()
    print(
        f"route_worker route_id={args.route_id} models={models} inputs={inputs} "
        f"base_url={base_url} dual_mode=worker",
        flush=True,
    )

    exit_code = 0
    try:
        for model in models:
            for input_n in inputs:
                n_samp = samples_map[input_n]
                if n_samp < 1:
                    print(f"skip model={model} input={input_n} samples=0", flush=True)
                    continue
                user = build_instruction_padded_user_text(
                    args.instruction,
                    input_n,
                    args.tiktoken_encoding,
                )
                max_t = max_tokens_for_input(input_n, args.output_ratio, args.max_tokens_rounding)
                print(
                    f"--- route={args.route_id} model={model} input_tokens={input_n} "
                    f"max_tokens={max_t} samples={n_samp} ---",
                    flush=True,
                )
                cell_fp: TextIO | None = jsonl_fp
                cell_raw_path: str | None = flat_path_resolved
                if jsonl_layout == "nested" and jsonl_path is not None:
                    assert jsonl_path is not None
                    cell_file = (
                        jsonl_path
                        / "cells"
                        / f"{_safe_model_filename(model)}__in{input_n}__route{args.route_id}.jsonl"
                    )
                    cell_fp = cell_file.open("w", encoding="utf-8")
                    cell_raw_path = str(cell_file.resolve())
                try:
                    summ = await run_cell(
                        client,
                        model,
                        input_n,
                        user,
                        max_t,
                        n_samp,
                        args.route_id,
                        cell_fp,
                        args.stream_timeout,
                        args.intra_route_concurrency,
                        truncate,
                        args.no_truncate,
                        raw_jsonl_path=cell_raw_path,
                        abort_on_429=not getattr(args, "no_abort_on_429", False),
                    )
                except ProbeAbort429:
                    return 3
                finally:
                    if jsonl_layout == "nested" and cell_fp is not None and cell_fp is not jsonl_fp:
                        cell_fp.close()
                line = json.dumps(summ, ensure_ascii=False)
                print(line, flush=True)
                if summary_fp:
                    summary_fp.write(line + "\n")
                    summary_fp.flush()
                if summ["n_fail"] and summ["n_ok"] == 0:
                    exit_code = 1
    finally:
        if jsonl_fp:
            jsonl_fp.close()
        if summary_fp:
            summary_fp.close()
        await client.close()

    return exit_code


def build_argv_for_child(
    base_args: argparse.Namespace,
    route_id: str,
    jsonl_out: str,
    models_csv: str,
    summary_jsonl: str | None,
) -> list[str]:
    py = sys.executable
    script = str(Path(__file__).resolve())
    cmd = [
        py,
        script,
        "--role",
        "route-worker",
        "--route-id",
        route_id,
        "--models",
        models_csv,
        "--input-tokens",
        base_args.input_tokens,
        "--output-ratio",
        str(base_args.output_ratio),
        "--max-tokens-rounding",
        base_args.max_tokens_rounding,
        "--instruction",
        base_args.instruction,
        "--tiktoken-encoding",
        base_args.tiktoken_encoding,
        "--samples",
        str(base_args.samples),
        "--intra-route-concurrency",
        str(base_args.intra_route_concurrency),
        "--stream-timeout",
        str(base_args.stream_timeout),
        "--base-url",
        base_args.base_url,
        "--jsonl-out",
        jsonl_out,
        "--truncate-response-chars",
        str(base_args.truncate_response_chars),
    ]
    if base_args.samples_by_input:
        cmd.extend(["--samples-by-input", base_args.samples_by_input])
    if summary_jsonl:
        cmd.extend(["--summary-jsonl", summary_jsonl])
    if base_args.no_truncate:
        cmd.append("--no-truncate")
    if getattr(base_args, "jsonl_layout", "flat") == "nested":
        cmd.extend(["--jsonl-layout", "nested"])
    if base_args.api_key:
        cmd.extend(["--api-key", base_args.api_key])
    if getattr(base_args, "no_abort_on_429", False):
        cmd.append("--no-abort-on-429")
    return cmd


def run_subprocess_orchestrator(args: argparse.Namespace) -> int:
    models_csv = ",".join(m.strip() for m in args.models.split(",") if m.strip())
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = args.output_stem or f"dual_profile_{ts}"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nested = getattr(args, "jsonl_layout", "flat") == "nested"
    if nested:
        ja = str(out_dir / f"{stem}_route_A")
        jb = str(out_dir / f"{stem}_route_B")
    else:
        ja = str(out_dir / f"{stem}_A.jsonl")
        jb = str(out_dir / f"{stem}_B.jsonl")
    want_summary = bool(getattr(args, "emit_summary_jsonl", False) or args.summary_jsonl)
    sa = str(out_dir / f"{stem}_A_summary.jsonl") if want_summary else None
    sb = str(out_dir / f"{stem}_B_summary.jsonl") if want_summary else None

    print(f"orchestrator subprocess stem={stem} dir={out_dir}", flush=True)
    print(f"route A/B 使用相同模型列表（双路叠加压测）: {models_csv}", flush=True)
    print(f"jsonl_layout={'nested' if nested else 'flat'} A={ja} B={jb}", flush=True)

    env = os.environ.copy()
    if args.api_key:
        env["NEWAPI_API_KEY"] = args.api_key

    cmd_a = build_argv_for_child(args, "A", ja, models_csv, sa)
    cmd_b = build_argv_for_child(args, "B", jb, models_csv, sb)

    # 子进程继承环境变量中的 KEY
    p_a = subprocess.Popen(cmd_a, env=env)
    p_b = subprocess.Popen(cmd_b, env=env)
    rc_a = p_a.wait()
    rc_b = p_b.wait()
    print(f"subprocess done rc_A={rc_a} rc_B={rc_b}", flush=True)
    manifest = {
        "stem": stem,
        "output_dir": str(out_dir.resolve()),
        "jsonl_layout": "nested" if nested else "flat",
        "route_A_root": ja,
        "route_B_root": jb,
        "summary_A": sa,
        "summary_B": sb,
        "models_csv": models_csv,
    }
    (out_dir / f"{stem}_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote_manifest={out_dir / f'{stem}_manifest.json'}", flush=True)
    return max(rc_a, rc_b)


async def async_inproc_orchestrator(args: argparse.Namespace) -> int:
    models_csv = ",".join(m.strip() for m in args.models.split(",") if m.strip())
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    stem = args.output_stem or f"dual_profile_{ts}"
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    nested = getattr(args, "jsonl_layout", "flat") == "nested"
    if nested:
        ja = str(out_dir / f"{stem}_route_A")
        jb = str(out_dir / f"{stem}_route_B")
    else:
        ja = str(out_dir / f"{stem}_A.jsonl")
        jb = str(out_dir / f"{stem}_B.jsonl")
    want_summary = bool(getattr(args, "emit_summary_jsonl", False) or args.summary_jsonl)
    sa = str(out_dir / f"{stem}_A_summary.jsonl") if want_summary else None
    sb = str(out_dir / f"{stem}_B_summary.jsonl") if want_summary else None

    wa = argparse.Namespace(**vars(args))
    wb = argparse.Namespace(**vars(args))
    wa.route_id = "A"
    wb.route_id = "B"
    wa.models = models_csv
    wb.models = models_csv
    wa.jsonl_out = ja
    wb.jsonl_out = jb
    wa.summary_jsonl = sa
    wb.summary_jsonl = sb

    print(f"orchestrator inproc stem={stem} dir={out_dir}", flush=True)
    ra, rb = await asyncio.gather(async_route_worker(wa), async_route_worker(wb))
    print(f"inproc done rc_A={ra} rc_B={rb}", flush=True)
    return max(ra, rb)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--role",
        choices=("orchestrator", "route-worker"),
        default="orchestrator",
        help="orchestrator：按 --dual-mode 调度；route-worker：单路线跑全量矩阵（供子进程调用）",
    )
    p.add_argument(
        "--dual-mode",
        choices=("none", "inproc", "subprocess"),
        default="none",
        help="none：单路线；inproc / subprocess：双路线并行（A/B 使用相同 --models 列表叠加压测）",
    )
    p.add_argument("--route-id", default="S", help="route-worker 必填语义标签（A/B/S）")
    p.add_argument(
        "--models",
        default="claude-opus-4-6,claude-sonnet-4-6,gemini-3-flash-preview,gemini-3.1-pro-preview",
        help="逗号分隔模型 id",
    )
    p.add_argument("--input-tokens", default="1500,15000,150000", help="逗号分隔输入 tiktoken 目标长度")
    p.add_argument("--output-ratio", type=int, default=200, help="输入:输出 token 比（整数除法）")
    p.add_argument(
        "--max-tokens-rounding",
        choices=("floor", "ceil"),
        default="floor",
        help="max_tokens = input/output_ratio 的取整方式",
    )
    p.add_argument("--instruction", default=_DEFAULT_INSTRUCTION, help="首行指令（后可换行）；其后自动填充")
    p.add_argument("--tiktoken-encoding", default="cl100k_base")
    p.add_argument("--samples", type=int, default=5, help="每输入档每模型样本数（可被 --samples-by-input 覆盖）")
    p.add_argument(
        "--samples-by-input",
        default=None,
        metavar="SPEC",
        help="如 1500:20,15000:5,150000:2 按输入档覆盖样本数",
    )
    p.add_argument(
        "--intra-route-concurrency",
        type=int,
        default=2,
        metavar="N",
        help="单路线内同一 cell 的并发请求数",
    )
    p.add_argument("--stream-timeout", type=float, default=3600.0, help="单请求流式总超时（秒）")
    p.add_argument(
        "--no-abort-on-429",
        action="store_true",
        help="遇 429/上游限流时不立即退出（默认：立即中止本 cell，进程退出码 3，无 sleep/自动重试）",
    )
    p.add_argument(
        "--base-url",
        default=os.environ.get("NEWAPI_BASE_URL", DEFAULT_BASE_URL),
    )
    p.add_argument("--api-key", default=os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY"))
    p.add_argument(
        "--jsonl-layout",
        choices=("flat", "nested"),
        default="flat",
        help="flat：单文件追加；nested：--jsonl-out 为目录，每 cell 写入 cells/<model>__inN__routeR.jsonl",
    )
    p.add_argument(
        "--jsonl-out",
        default=None,
        help="flat 时为逐请求 JSONL 文件路径；nested 时为该路线根目录（下建 cells/）",
    )
    p.add_argument("--summary-jsonl", default=None, help="追加每 cell 的 summary JSON 行（显式路径）")
    p.add_argument(
        "--emit-summary-jsonl",
        action="store_true",
        help="写每 cell 的 summary：orchestrator 为 *_A/_B_summary.jsonl；--dual-mode none 时为 <jsonl-stem>_summary.jsonl",
    )
    p.add_argument("--output-dir", default="/tmp", help="subprocess/inproc  orchestrator 写 JSONL 的目录")
    p.add_argument("--output-stem", default=None, help="输出文件名前缀（默认 UTC 时间戳）")
    p.add_argument("--truncate-response-chars", type=int, default=8000)
    p.add_argument("--no-truncate", action="store_true")

    ns = p.parse_args()

    if ns.role == "route-worker":
        return asyncio.run(async_route_worker(ns))

    if ns.dual_mode == "subprocess":
        return run_subprocess_orchestrator(ns)
    if ns.dual_mode == "inproc":
        return asyncio.run(async_inproc_orchestrator(ns))

    # none：单路线
    ns.route_id = ns.route_id if ns.route_id != "S" else "single"
    if not ns.jsonl_out:
        ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
        if ns.jsonl_layout == "nested":
            ns.jsonl_out = str(Path(ns.output_dir) / f"single_profile_{ts}")
        else:
            ns.jsonl_out = str(Path(ns.output_dir) / f"single_profile_{ts}.jsonl")
    if ns.emit_summary_jsonl and not ns.summary_jsonl:
        pth = Path(ns.jsonl_out)
        if ns.jsonl_layout == "nested":
            ns.summary_jsonl = str(pth.parent / f"{pth.name}_summary.jsonl")
        else:
            ns.summary_jsonl = str(pth.with_name(pth.stem + "_summary.jsonl"))
    return asyncio.run(async_route_worker(ns))


if __name__ == "__main__":
    raise SystemExit(main())

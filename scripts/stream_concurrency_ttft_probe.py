#!/usr/bin/env python3
"""
单模型流式并发探针：固定 heavy 正文（tiktoken 定长）+ max_tokens，对多档并发
（Semaphore）各跑 N 次 stream=True 请求，统计 TTFT 与整段流式墙钟。

每次命令仅传一个 --model；四模型请分四次执行。勿将 API Key 写入仓库。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Any, TextIO

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from openai import AsyncOpenAI
from openai_probe_payload import build_heavy_user_content

DEFAULT_BASE_URL = "https://api.mixroute.ai/v1"


def _normalize_base_url(url: str) -> str:
    u = url.rstrip("/")
    return u or DEFAULT_BASE_URL


def _percentile(vals: list[float], p: float) -> float:
    """p in [0, 100]. NaN if empty."""
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


def _delta_first_token(delta: Any) -> tuple[bool, str]:
    """首个可计 TTFT 的增量：content 或 reasoning 等任一非空字符串字段。"""
    if delta is None:
        return False, ""
    c = getattr(delta, "content", None)
    if isinstance(c, str) and c.strip():
        return True, "content"
    rc = getattr(delta, "reasoning_content", None)
    if isinstance(rc, str) and rc.strip():
        return True, "reasoning_content"
    if hasattr(delta, "model_dump"):
        raw = delta.model_dump(exclude_unset=True)
        for k, v in raw.items():
            if k in ("content", "reasoning_content", "role", "refusal", "function_call", "tool_calls"):
                continue
            if isinstance(v, str) and v.strip():
                return True, k
            if isinstance(v, list) and v:
                return True, k
    return False, ""


def _chunk_first_token(chunk: Any) -> tuple[bool, str]:
    ch0 = chunk.choices[0] if getattr(chunk, "choices", None) else None
    if ch0 is None:
        return False, ""
    return _delta_first_token(getattr(ch0, "delta", None))


async def _consume_stream(
    stream: Any,
    t0: float,
) -> tuple[float | None, str, float | None]:
    """
    返回 (ttft_s_from_t0, first_kind, usage_dict_or_none)。
    ttft 为从 t0 到首个含 token 的 chunk 的秒数。
    """
    ttft: float | None = None
    first_kind = ""
    usage: dict[str, Any] | None = None
    async for chunk in stream:
        if ttft is None:
            hit, kind = _chunk_first_token(chunk)
            if hit:
                ttft = time.perf_counter() - t0
                first_kind = kind
        u = getattr(chunk, "usage", None)
        if u is not None and hasattr(u, "model_dump"):
            usage = u.model_dump()
        elif u is not None:
            usage = {"repr": repr(u)[:200]}
    return ttft, first_kind, usage


async def _one_stream_request(
    client: AsyncOpenAI,
    model: str,
    user_content: str,
    max_tokens: int,
    stream_timeout: float,
    sem: asyncio.Semaphore,
    idx: int,
    concurrency: int,
    jsonl_fp: TextIO | None,
) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "i": idx,
        "model": model,
        "concurrency": concurrency,
        "ok": False,
        "ttft_s": None,
        "total_s": None,
        "first_kind": "",
        "error": "",
    }
    async with sem:
        t0 = time.perf_counter()

        async def _run_stream() -> tuple[float | None, str, float]:
            stream = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": user_content}],
                max_tokens=max_tokens,
                stream=True,
            )
            ttft, first_kind, _usage = await _consume_stream(stream, t0)
            total = time.perf_counter() - t0
            return ttft, first_kind, total

        try:
            ttft, first_kind, total = await asyncio.wait_for(
                _run_stream(),
                timeout=stream_timeout,
            )
            rec["total_s"] = round(total, 6)
            rec["first_kind"] = first_kind
            if ttft is None:
                rec["error"] = "no_first_token_chunk"
                rec["ok"] = False
            else:
                rec["ttft_s"] = round(ttft, 6)
                rec["ok"] = True
        except TimeoutError:
            rec["total_s"] = round(time.perf_counter() - t0, 6)
            rec["error"] = "TimeoutError"
        except Exception as e:
            rec["total_s"] = (
                round(time.perf_counter() - t0, 6) if rec["total_s"] is None else rec["total_s"]
            )
            rec["error"] = f"{type(e).__name__}: {e}"[:500]
        finally:
            if jsonl_fp:
                jsonl_fp.write(json.dumps(rec, ensure_ascii=False) + "\n")
                jsonl_fp.flush()
    return rec


async def _run_concurrency_level(
    client: AsyncOpenAI,
    model: str,
    user_content: str,
    max_tokens: int,
    stream_timeout: float,
    concurrency: int,
    samples: int,
    jsonl_fp: TextIO | None,
) -> dict[str, Any]:
    sem = asyncio.Semaphore(concurrency)
    wall0 = time.perf_counter()
    tasks = [
        asyncio.create_task(
            _one_stream_request(
                client,
                model,
                user_content,
                max_tokens,
                stream_timeout,
                sem,
                i + 1,
                concurrency,
                jsonl_fp,
            )
        )
        for i in range(samples)
    ]
    rows = await asyncio.gather(*tasks)
    wall = time.perf_counter() - wall0

    oks = [r for r in rows if r.get("ok")]
    fails = [r for r in rows if not r.get("ok")]
    ttfts = [float(r["ttft_s"]) for r in oks if r.get("ttft_s") is not None]
    totals = [float(r["total_s"]) for r in oks if r.get("total_s") is not None]

    def _mean(xs: list[float]) -> float:
        return sum(xs) / len(xs) if xs else float("nan")

    out: dict[str, Any] = {
        "concurrency": concurrency,
        "samples": samples,
        "n_ok": len(oks),
        "n_fail": len(fails),
        "wall_s": round(wall, 4),
        "mean_ttft_s": round(_mean(ttfts), 4) if ttfts else float("nan"),
        "p50_ttft_s": round(_percentile(ttfts, 50), 4) if ttfts else float("nan"),
        "p95_ttft_s": round(_percentile(ttfts, 95), 4) if ttfts else float("nan"),
        "mean_total_s": round(_mean(totals), 4) if totals else float("nan"),
        "p50_total_s": round(_percentile(totals, 50), 4) if totals else float("nan"),
        "p95_total_s": round(_percentile(totals, 95), 4) if totals else float("nan"),
        "fail_errors": _fail_summary(fails),
    }
    return out


def _fail_summary(fails: list[dict[str, Any]]) -> str:
    if not fails:
        return ""
    counts: dict[str, int] = {}
    for r in fails:
        e = (r.get("error") or "unknown")[:120]
        counts[e] = counts.get(e, 0) + 1
    parts = [f"{k}:{v}" for k, v in sorted(counts.items(), key=lambda x: -x[1])[:5]]
    return "; ".join(parts)


async def _async_main(args: argparse.Namespace) -> None:
    base_url = _normalize_base_url(args.base_url)
    api_key = args.api_key or os.environ.get("NEWAPI_API_KEY") or os.environ.get(
        "OPENAI_API_KEY"
    )
    if not api_key:
        print("错误: 未设置 API Key（--api-key 或 NEWAPI_API_KEY / OPENAI_API_KEY）", file=sys.stderr)
        sys.exit(2)

    user_content = build_heavy_user_content(args.input_tokens, args.tiktoken_encoding)

    jsonl_fp: TextIO | None = None
    if args.jsonl_out:
        p = Path(args.jsonl_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        jsonl_fp = p.open("a", encoding="utf-8")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=args.stream_timeout,
        max_retries=0,
    )

    print(
        f"stream_ttft_probe model={args.model} base_url={base_url} "
        f"input_tokens={args.input_tokens} tiktoken={args.tiktoken_encoding} "
        f"max_tokens={args.max_tokens} samples={args.samples} "
        f"concurrency_list={args.concurrency_list} stream_timeout_s={args.stream_timeout}",
        flush=True,
    )

    results: list[dict[str, Any]] = []
    try:
        for conc in args.concurrency_list:
            r = await _run_concurrency_level(
                client,
                args.model,
                user_content,
                args.max_tokens,
                args.stream_timeout,
                conc,
                args.samples,
                jsonl_fp,
            )
            results.append(r)
            print(
                f"--- concurrency={conc} --- n_ok={r['n_ok']} n_fail={r['n_fail']} "
                f"wall_s={r['wall_s']} mean_ttft_s={r['mean_ttft_s']} p50_ttft={r['p50_ttft_s']} "
                f"p95_ttft={r['p95_ttft_s']} mean_total_s={r['mean_total_s']} "
                f"p50_total={r['p50_total_s']} p95_total={r['p95_total_s']}",
                flush=True,
            )
            if r["fail_errors"]:
                print(f"  fail_summary: {r['fail_errors']}", flush=True)
    finally:
        if jsonl_fp:
            jsonl_fp.close()
        await client.close()

    print("", flush=True)
    print("### Markdown（本模型 × 并发档，便于粘贴报告）", flush=True)
    print("", flush=True)
    print(f"- **model**: `{args.model}`", flush=True)
    print(f"- **input_tokens（tiktoken 目标）**: {args.input_tokens}", flush=True)
    print(f"- **max_tokens**: {args.max_tokens}", flush=True)
    print(f"- **samples / 档**: {args.samples}", flush=True)
    print("", flush=True)
    print("| 并发 | n_ok | n_fail | wall_s | mean_ttft_s | p50_ttft | p95_ttft | mean_total_s | p50_total | p95_total |", flush=True)
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |", flush=True)
    for r in results:
        print(
            f"| {r['concurrency']} | {r['n_ok']} | {r['n_fail']} | {r['wall_s']} | "
            f"{r['mean_ttft_s']} | {r['p50_ttft_s']} | {r['p95_ttft_s']} | "
            f"{r['mean_total_s']} | {r['p50_total_s']} | {r['p95_total_s']} |",
            flush=True,
        )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", required=True, help="单个模型 id（每次命令只跑一个）")
    p.add_argument(
        "--base-url",
        default=os.environ.get("NEWAPI_BASE_URL", DEFAULT_BASE_URL),
        help="网关 base_url（默认 NEWAPI_BASE_URL 或 mixroute）",
    )
    p.add_argument(
        "--api-key",
        default=os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        help="API Key；可改用环境变量",
    )
    p.add_argument("--input-tokens", type=int, default=4096, metavar="N")
    p.add_argument("--max-tokens", type=int, default=512, metavar="N")
    p.add_argument("--tiktoken-encoding", default="cl100k_base")
    p.add_argument(
        "--concurrency-list",
        type=str,
        default="50,100",
        dest="concurrency_list_str",
        metavar="LIST",
        help="逗号分隔并发档，按顺序执行（默认 50,100）",
    )
    p.add_argument("--samples", type=int, default=100, metavar="N")
    p.add_argument(
        "--stream-timeout",
        type=float,
        default=600.0,
        metavar="SEC",
        help="单流整体超时（create + consume）",
    )
    p.add_argument("--jsonl-out", default=None, metavar="PATH")
    args = p.parse_args()

    try:
        concs = [
            int(x.strip()) for x in args.concurrency_list_str.split(",") if x.strip()
        ]
    except ValueError:
        print("错误: --concurrency-list 须为逗号分隔整数", file=sys.stderr)
        sys.exit(2)
    if not concs or any(c < 1 for c in concs):
        print("错误: 并发列表须为正整数", file=sys.stderr)
        sys.exit(2)
    if args.samples < 1:
        print("错误: --samples 须 >= 1", file=sys.stderr)
        sys.exit(2)
    setattr(args, "concurrency_list", concs)

    asyncio.run(_async_main(args))


if __name__ == "__main__":
    main()

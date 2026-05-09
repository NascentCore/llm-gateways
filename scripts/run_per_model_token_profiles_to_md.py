#!/usr/bin/env python3
"""
依次对多个模型各跑一批 dual_route_stream_profile_probe（单路线 + nested JSONL），
读取各模型的 summary，生成一份合并 Markdown。

默认（可用 CLI 覆盖）：
  - 单路线内并发：--intra-route-concurrency 100
  - 每输入档样本数：1500→1000 次、15000→500 次、150000→100 次（--samples-by-input）
  - 单请求流式超时：--stream-timeout 21600（秒），适配 150k 输入 + 高并发排队

勿将 API Key 写入仓库；依赖环境变量 NEWAPI_API_KEY / OPENAI_API_KEY。
全量默认跑满费用与耗时极高，建议在目标机用 nohup 后台执行。
nohup 子进程须继承 Key：请在已 export 的交互 shell 内启动，或使用 `nohup env NEWAPI_API_KEY=…`（勿写入仓库）。
分档减负：可传 `--input-tokens 1500` 与匹配的 `--samples-by-input 1500:1000` 等，仅跑单档。

示例：
  uv run python scripts/run_per_model_token_profiles_to_md.py \\
    --markdown-out docs/per-model-token-profile-$(date -u +%Y%m%d).md \\
    --output-dir /tmp/per_model_profiles_$(date -u +%Y%m%dT%H%M%SZ)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "gemini-3-flash-preview",
    "gemini-3.1-pro-preview",
]


def _safe(s: str) -> str:
    return (
        s.replace("/", "_")
        .replace(":", "_")
        .replace(" ", "_")
        .replace("\\", "_")
    )


def _load_summary(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    out: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="逗号分隔模型列表（将按顺序各跑一轮）",
    )
    p.add_argument("--markdown-out", type=Path, required=True)
    p.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="本次批次根目录（其下为每模型子目录，含 cells/ 与 *_summary.jsonl）",
    )
    p.add_argument(
        "--input-tokens",
        default="1500,15000,150000",
        help="传给探针的 --input-tokens（逗号分隔；单档如 1500 可减轻并发与配额压力）",
    )
    p.add_argument(
        "--samples-by-input",
        default="1500:1000,15000:500,150000:100",
        help="传给探针的 --samples-by-input（每档总请求数）",
    )
    p.add_argument(
        "--stream-timeout",
        type=float,
        default=21600.0,
        help="单请求流式超时（秒）；150k 输入建议保持较大值",
    )
    p.add_argument(
        "--intra-route-concurrency",
        type=int,
        default=100,
        help="单路线、同一 cell 内 Semaphore 并发上限（默认 100）",
    )
    p.add_argument(
        "--no-abort-on-429",
        action="store_true",
        help="传给探针：遇 429 时不立即中止（默认探针遇 429 立即退出码 3）",
    )
    p.add_argument("--base-url", default=os.environ.get("NEWAPI_BASE_URL", "https://api.mixroute.ai/v1"))
    p.add_argument("--host-note", default="", help="写入 Markdown 的执行主机说明")
    args = p.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        print("错误: --models 为空", file=sys.stderr)
        return 2

    api_key = os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("错误: 请设置 NEWAPI_API_KEY 或 OPENAI_API_KEY", file=sys.stderr)
        return 2

    root = args.output_dir.resolve()
    root.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).resolve().parent / "dual_route_stream_profile_probe.py"
    py = sys.executable

    runs: list[tuple[str, Path, Path, int]] = []
    for model in models:
        sub = root / _safe(model)
        sub.mkdir(parents=True, exist_ok=True)
        # 与 dual_route 单路线 nested 一致：--jsonl-out 指向 .../run 目录时，summary 为 .../run_summary.jsonl
        jsonl_base = sub / "run"
        summary_path = sub / "run_summary.jsonl"
        cmd = [
            py,
            str(script),
            "--dual-mode",
            "none",
            "--jsonl-layout",
            "nested",
            "--emit-summary-jsonl",
            "--models",
            model,
            "--input-tokens",
            args.input_tokens,
            "--samples-by-input",
            args.samples_by_input,
            "--stream-timeout",
            str(args.stream_timeout),
            "--intra-route-concurrency",
            str(args.intra_route_concurrency),
            "--base-url",
            args.base_url,
            "--output-dir",
            str(sub),
            "--jsonl-out",
            str(jsonl_base),
        ]
        if args.no_abort_on_429:
            cmd.append("--no-abort-on-429")
        env = os.environ.copy()
        env["NEWAPI_API_KEY"] = api_key
        env["PYTHONUNBUFFERED"] = "1"
        print(f"=== run model={model} ===", flush=True)
        print(" ".join(cmd), flush=True)
        rc = subprocess.run(cmd, env=env).returncode
        runs.append((model, sub, summary_path, rc))
        if rc == 3:
            print("探针因 429 中止（退出码 3），已跳过后续模型。", flush=True)
            break

    ts = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    lines: list[str] = []
    lines.append("# 四模型 Token 剖面（逐模型 × 三档输入加压）\n\n")
    lines.append(f"- **生成时间**：{ts}\n")
    if args.host_note:
        lines.append(f"- **执行环境**：{args.host_note}\n")
    lines.append(f"- **批次根目录**：`{root}`\n")
    lines.append(f"- **网关**：`{args.base_url}`\n")
    lines.append(f"- **单路线并发（Semaphore）**：`{args.intra_route_concurrency}`\n")
    lines.append(f"- **input-tokens**：`{args.input_tokens}`\n")
    lines.append(f"- **samples-by-input**：`{args.samples_by_input}`\n")
    if args.no_abort_on_429:
        lines.append("- **429**：已传 `--no-abort-on-429`（遇 429 仍尽量跑满本 cell）\n")
    else:
        lines.append(
            "- **429**：默认遇 **429 / 上游限流** 立即中止本 cell，**进程退出码 3**（无 sleep、无自动重试）；由操作者择时重跑脚本\n"
        )
    lines.append(f"- **单请求 stream 超时（秒）**：`{args.stream_timeout}`\n")
    lines.append("\n指标口径与 `dual_route_stream_profile_probe.py --help` 一致（RPM/TPM/TTFT/TPS）。\n\n")

    for model, sub, summary_path, rc in runs:
        lines.append(f"## `{model}`\n\n")
        lines.append(f"- **工作目录**：`{sub}`\n")
        lines.append(f"- **探针退出码**：{rc}\n")
        rows = _load_summary(summary_path)
        if not rows:
            lines.append(
                f"- **summary 文件**：未找到或为空（预期路径 `{summary_path.resolve()}`）。\n\n"
            )
            continue
        lines.append(f"- **summary 文件**：`{summary_path.resolve()}`\n\n")
        head = (
            "| input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始请求 JSONL（该 case 全部行） |\n"
        )
        sep = "| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n"
        lines.append(head + sep)
        for r in rows:
            raw = r.get("raw_jsonl_path") or "—"
            tpm = r.get("tpm_total_tokens")
            tpm_s = f"{float(tpm):.2f}" if tpm is not None else "null"
            mtt = r.get("mean_ttft_s")
            mtt_s = f"{float(mtt):.4f}" if mtt is not None else "null"
            mtp = r.get("mean_tps_output")
            mtp_s = f"{float(mtp):.4f}" if mtp is not None else "null"
            lines.append(
                f"| {r.get('input_tokens_target', '')} | {r.get('max_tokens', '')} | {r.get('samples', '')} | "
                f"{r.get('n_ok', '')} | {r.get('n_fail', '')} | {r.get('rpm_requests', '')} | {tpm_s} | {mtt_s} | {mtp_s} | `{raw}` |\n"
            )
        if any(r.get("fail_errors") for r in rows):
            lines.append("\n失败摘要：\n\n")
            for r in rows:
                fe = r.get("fail_errors")
                if fe:
                    lines.append(f"- input={r.get('input_tokens_target')}: `{fe}`\n")
        lines.append("\n")

    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {args.markdown_out.resolve()}", flush=True)
    if any(rc == 3 for _, _, _, rc in runs):
        return 3
    return 0 if all(rc == 0 for _, _, _, rc in runs) else 1


if __name__ == "__main__":
    raise SystemExit(main())

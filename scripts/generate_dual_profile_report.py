#!/usr/bin/env python3
"""
读取 dual_route_stream_profile_probe 一次 subprocess/inproc run 产出的
`*_A_summary.jsonl` / `*_B_summary.jsonl`（及可选 manifest），生成简要 Markdown 报告。

示例：
  python scripts/generate_dual_profile_report.py \\
    --output-dir /tmp \\
    --stem dual_profile_20260509T120000Z \\
    --markdown-out /tmp/dual_profile_20260509T120000Z_brief.md \\
    --host ubuntu@18.183.174.245
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_summary_lines(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    rows: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--stem", required=True, help="与探针 --output-stem 一致（不含路径）")
    p.add_argument("--markdown-out", type=Path, required=True)
    p.add_argument("--host", default="", help="报告中标注的执行主机")
    args = p.parse_args()

    out = args.output_dir
    stem = args.stem
    man_path = out / f"{stem}_manifest.json"
    manifest: dict[str, object] = {}
    if man_path.is_file():
        try:
            manifest = json.loads(man_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}

    sa = out / f"{stem}_A_summary.jsonl"
    sb = out / f"{stem}_B_summary.jsonl"
    rows_a = _load_summary_lines(sa)
    rows_b = _load_summary_lines(sb)

    lines: list[str] = []
    lines.append("# 双路线 Token 剖面 — 简要报告\n")
    if args.host:
        lines.append(f"- **执行主机**：`{args.host}`\n")
    lines.append(f"- **输出目录**：`{out.resolve()}`\n")
    lines.append(f"- **run stem**：`{stem}`\n")
    if manifest:
        lines.append(f"- **manifest**：`{man_path.resolve()}`\n")
    lines.append(f"- **汇总 JSONL**：路线 A `{sa.resolve()}`；路线 B `{sb.resolve()}`\n")
    lines.append("\n## 指标说明\n\n")
    lines.append(
        "每行 summary 与探针 stdout 一致：**RPM**=该 cell 请求数/墙钟×60；"
        "**TPM**=Σ`usage.total_tokens`/墙钟×60；**TTFT** 为 mean/p50/p95；"
        "**TPS** 为输出阶段吞吐（见探针 `--help`）。\n\n"
    )
    lines.append("## 分 case 结果与原始请求数据位置\n\n")
    lines.append(
        "下表中 **原始数据路径** 为该 case 下**全部逐请求 JSONL**（每行一次 HTTP）；"
        "`nested` 布局下一 case 对应独立文件；`flat` 布局下多 case 共用同一文件，可按 "
        "`jq 'select(.model==... and .input_tokens_target==...)'` 过滤。\n\n"
    )

    def emit_table(title: str, rows: list[dict[str, object]]) -> None:
        lines.append(f"### {title}\n\n")
        if not rows:
            lines.append("*（无 summary 行；文件不存在或为空）*\n\n")
            return
        head = (
            "| route | model | input_tokens | max_tokens | samples | n_ok | n_fail | "
            "RPM | TPM | mean_ttft_s | mean_tps | 原始数据（全部请求） |\n"
        )
        sep = "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |\n"
        lines.append(head + sep)
        for r in rows:
            raw = r.get("raw_jsonl_path") or "—"
            tpm = r.get("tpm_total_tokens")
            tpm_s = f"{tpm:.2f}" if tpm is not None else "null"
            mtt = r.get("mean_ttft_s")
            mtt_s = f"{mtt:.4f}" if mtt is not None else "null"
            mtp = r.get("mean_tps_output")
            mtp_s = f"{mtp:.4f}" if mtp is not None else "null"
            lines.append(
                f"| {r.get('route_id', '')} | `{r.get('model', '')}` | {r.get('input_tokens_target', '')} | "
                f"{r.get('max_tokens', '')} | {r.get('samples', '')} | {r.get('n_ok', '')} | {r.get('n_fail', '')} | "
                f"{r.get('rpm_requests', '')} | {tpm_s} | {mtt_s} | {mtp_s} | `{raw}` |\n"
            )
        lines.append("\n")

    emit_table("路线 A", rows_a)
    emit_table("路线 B", rows_b)

    lines.append("## 附属文件\n\n")
    lines.append(f"- `cells/` 目录（nested）：`{out.resolve()}/{stem}_route_A/cells/` 与 `..._route_B/cells/`\n")

    args.markdown_out.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_out.write_text("".join(lines), encoding="utf-8")
    print(f"wrote {args.markdown_out.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

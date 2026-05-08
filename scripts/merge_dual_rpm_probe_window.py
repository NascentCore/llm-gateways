#!/usr/bin/env python3
"""
Merge two rpm_minute_window_probe stdout logs: count ok/fail lines whose
t_start falls in [anchor - 60, anchor], using anchor_t_start from --log-a
(or --anchor).

Example:
  python scripts/merge_dual_rpm_probe_window.py \\
    --log-a /tmp/rpm_dual_sonnet_20260508T015117Z_A.out \\
    --log-b /tmp/rpm_dual_sonnet_20260508T015117Z_B.out
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def _parse_anchor_from_summary(text: str) -> float | None:
    m = re.search(r"anchor_t_start=([0-9]+(?:\.[0-9]+)?)", text)
    return float(m.group(1)) if m else None


def _parse_window_started(text: str) -> int | None:
    m = re.search(r"window_60s_requests_started=(\d+)", text)
    return int(m.group(1)) if m else None


def _collect_t_starts(path: Path) -> list[float]:
    starts: list[float] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.startswith(("ok ", "fail ")):
            continue
        m = re.search(r"t_start=([0-9]+(?:\.[0-9]+)?)", line)
        if m:
            starts.append(float(m.group(1)))
    return starts


def _count_in_window(starts: list[float], lo: float, hi: float) -> int:
    return sum(1 for t in starts if lo <= t <= hi)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log-a", type=Path, required=True, help="First probe log (anchor read from summary here)")
    p.add_argument("--log-b", type=Path, required=True, help="Second probe log")
    p.add_argument(
        "--anchor",
        type=float,
        default=None,
        metavar="T",
        help="Override anchor t_start (default: parse anchor_t_start from log-a summary)",
    )
    args = p.parse_args()

    text_a = args.log_a.read_text(encoding="utf-8", errors="replace")
    anchor = args.anchor if args.anchor is not None else _parse_anchor_from_summary(text_a)
    if anchor is None:
        raise SystemExit("Could not find anchor_t_start in log-a; pass --anchor")

    lo = anchor - 60.0
    hi = anchor
    starts_a = _collect_t_starts(args.log_a)
    starts_b = _collect_t_starts(args.log_b)
    ca = _count_in_window(starts_a, lo, hi)
    cb = _count_in_window(starts_b, lo, hi)
    reported = _parse_window_started(text_a)

    print(f"log_a={args.log_a}")
    print(f"log_b={args.log_b}")
    print(f"anchor_t_start={anchor:.6f}")
    print(f"window_sec=60.0 window=[{lo:.6f}, {hi:.6f}]")
    print(f"count_a_in_window={ca} (ok+fail lines with t_start: {len(starts_a)})")
    print(f"count_b_in_window={cb} (ok+fail lines with t_start: {len(starts_b)})")
    print(f"merged_in_window={ca + cb}")
    if reported is not None:
        print(f"reported_window_60s_requests_started_from_log_a={reported}")


if __name__ == "__main__":
    main()

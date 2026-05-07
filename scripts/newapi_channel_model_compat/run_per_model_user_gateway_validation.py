#!/usr/bin/env python3
"""
对若干模型依次执行「用户 Key + 网关」全量验证（与 mixroute 技术报告 2026-05-06 同档参数）：

1. test_chat.py --client openai
2. test_chat.py --client anthropic
3. OpenAI SDK 单次 chat，打印 usage（默认 prompt / max_tokens=512）
4. scripts/rpm_until_limit.py（heavy，峰值并发 16，max_requests=127）
5. scripts/rpm_minute_window_probe.py（batch + minimal，256×4096）

API Key：仅环境变量 NEWAPI_API_KEY 或 OPENAI_API_KEY，勿写入仓库。

典型用法（仓库根目录、已激活 venv）：

  export NEWAPI_API_KEY=...
  export NEWAPI_BASE_URL=https://llm.sxwl.ai/v1
  python scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py --dry-run

  # 全量（费用与耗时长）
  python scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py \\
    --output-dir /tmp/sxwl_per_model_run
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

# 与 2026-05-06 终端「OpenAI + Anthropic 均通过」的渠道模型列表对齐（llm.sxwl.ai）
DEFAULT_MODELS: tuple[str, ...] = (
    "glm-5.1",
    "glm-5",
    "hunyuan-pro",
    "hunyuan-standard",
    "MiniMax-M2.7",
    "MiniMax-M2.5",
    "kimi-k2.6",
    "kimi-k2.5",
    "step-3.5-flash-2603",
    "step-3.5-flash",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def model_slug(model: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", model.strip())
    return s.strip("_") or "model"


def _api_keys_to_redact() -> list[str]:
    keys: list[str] = []
    for k in ("NEWAPI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        v = os.environ.get(k)
        if v and len(v) >= 8:
            keys.append(v)
    return keys


def redact(text: str) -> str:
    out = text
    for k in _api_keys_to_redact():
        out = out.replace(k, "***")
    return out


def run_cmd(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout: float | None,
    log_path: Path | None,
) -> tuple[int, str, str]:
    """返回 (exit_code, stdout, stderr 合并后的全文用于记录)."""
    p = subprocess.run(
        argv,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    combined = ""
    if p.stdout:
        combined += p.stdout
    if p.stderr:
        if combined and not combined.endswith("\n"):
            combined += "\n"
        combined += p.stderr
    text = redact(combined)
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(text, encoding="utf-8")
    return p.returncode, text, text


USAGE_SNIPPET = r"""
import os, sys, time
from openai import OpenAI

base = os.environ.get("USAGE_BASE_URL", "").rstrip("/")
model = os.environ.get("USAGE_MODEL", "")
prompt = os.environ.get("USAGE_PROMPT", "你好，请用一句话介绍你自己。")
max_tokens = int(os.environ.get("USAGE_MAX_TOKENS", "512"))
if not base or not model:
    print("USAGE_BASE_URL / USAGE_MODEL 未设置", file=sys.stderr)
    sys.exit(2)
key = os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY")
if not key:
    print("未设置 NEWAPI_API_KEY / OPENAI_API_KEY", file=sys.stderr)
    sys.exit(2)
client = OpenAI(
    base_url=base if base.endswith("/v1") else base + "/v1",
    api_key=key,
    default_headers={"Accept": "application/json"},
)
t0 = time.perf_counter()
r = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=max_tokens,
)
dt = time.perf_counter() - t0
u = r.usage
pt = getattr(u, "prompt_tokens", None)
ct = getattr(u, "completion_tokens", None)
tt = getattr(u, "total_tokens", None)
print(f"model={model}\tprompt_tokens={pt}\tcompletion_tokens={ct}\ttotal_tokens={tt}\twall_s={dt:.2f}")
"""


@dataclass
class ModelResult:
    model: str
    slug: str
    steps: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {"model": self.model, "slug": self.slug, "steps": self.steps}


def write_markdown(
    path: Path,
    *,
    base_url: str,
    models: list[str],
    results: list[ModelResult],
    output_dir: Path,
    utc_run: str,
) -> None:
    lines: list[str] = []
    lines.append("# llm.sxwl.ai 逐模型用户侧全量验证报告（生成）\n")
    lines.append(f"**生成时间（UTC）**：{utc_run}  \n")
    lines.append(f"**网关 base_url**：`{base_url}`  \n")
    lines.append(f"**原始日志目录**：`{output_dir}`（机器本地路径，请随跑随备份）  \n")
    lines.append(
        "**说明**：本文件由 "
        "`scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py` "
        "生成；与 `test_channel_models_compat.py`（管理端按渠道探测）口径不同，"
        "此处为用户 Key 经网关路由的 OpenAI / Anthropic 兼容路径。\n"
    )
    lines.append("---\n")
    lines.append("## 汇总表\n")
    lines.append(
        "| 模型 | OpenAI chat | Anthropic msg | usage (p/c/t/墙钟s) | heavy summary | minute summary |\n"
    )
    lines.append("|------|-------------|---------------|---------------------|---------------|----------------|\n")

    def _one(s: dict[str, Any], key: str) -> str:
        st = s.get(key) or {}
        if st.get("skipped"):
            return "跳过"
        if st.get("ok") is True:
            return "OK"
        if st.get("ok") is False:
            return f"FAIL ({st.get('exit_code')})"
        return "—"

    def _short(s: dict[str, Any], key: str, maxlen: int = 80) -> str:
        st = s.get(key) or {}
        if st.get("skipped"):
            return "—"
        tail = (st.get("log_tail") or "").replace("\n", " ").strip()
        if len(tail) > maxlen:
            tail = tail[: maxlen - 1] + "…"
        return tail or "—"

    for r in results:
        s = r.steps
        lines.append(
            f"| `{r.model}` | {_one(s, 'openai')} | {_one(s, 'anthropic')} | "
            f"`{_short(s, 'usage', 60)}` | `{_short(s, 'rpm_heavy', 50)}` | `{_short(s, 'rpm_minute', 50)}` |\n"
        )

    lines.append("\n---\n")
    for r in results:
        lines.append(f"## `{r.model}`（slug=`{r.slug}`）\n")
        for name, title in (
            ("openai", "test_chat OpenAI"),
            ("anthropic", "test_chat Anthropic"),
            ("usage", "Usage 采样"),
            ("rpm_heavy", "rpm_until_limit heavy"),
            ("rpm_minute", "rpm_minute_window_probe batch+minimal"),
        ):
            st = r.steps.get(name) or {}
            lines.append(f"### {title}\n")
            if st.get("skipped"):
                lines.append(f"_跳过：{st.get('reason', '')}_\n")
                continue
            lines.append(f"- exit_code: `{st.get('exit_code')}`\n")
            if st.get("log_file"):
                lines.append(f"- 完整日志：`{st.get('log_file')}`\n")
            body = (st.get("log_tail") or "").strip()
            if body:
                lines.append("\n```\n")
                lines.append(body)
                if not body.endswith("\n"):
                    lines.append("\n")
                lines.append("```\n")
            lines.append("\n")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def main() -> None:
    repo = _repo_root()
    parser = argparse.ArgumentParser(
        description="逐模型用户侧网关全量验证（test_chat + usage + rpm 探针）"
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("NEWAPI_BASE_URL", "https://llm.sxwl.ai/v1"),
        help="网关 OpenAI base_url，默认 NEWAPI_BASE_URL 或 https://llm.sxwl.ai/v1",
    )
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="逗号分隔模型 id 列表",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="原始日志根目录（默认 ./sxwl_per_model_validation_<UTC时间戳>）",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Markdown 报告路径（默认 docs/newapi-sxwl-per-model-validation-<本地日期>.md）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将执行的命令，不调用网络",
    )
    parser.add_argument(
        "--skip-heavy",
        action="store_true",
        help="跳过 rpm_until_limit heavy",
    )
    parser.add_argument(
        "--skip-minute",
        action="store_true",
        help="跳过 rpm_minute_window_probe",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="某步失败后仍继续该模型后续步骤（默认：该模型后续步骤跳过）",
    )
    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not models:
        print("错误: --models 为空", file=sys.stderr)
        sys.exit(2)

    api_key = os.environ.get("NEWAPI_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key and not args.dry_run:
        print(
            "错误: 请设置 NEWAPI_API_KEY 或 OPENAI_API_KEY（--dry-run 除外）",
            file=sys.stderr,
        )
        sys.exit(2)

    base_url = args.base_url.rstrip("/")
    if not base_url.endswith("/v1"):
        base_url = base_url + "/v1"

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = args.output_dir or (Path.cwd() / f"sxwl_per_model_validation_{ts}")
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    report_path = args.report
    if report_path is None:
        report_path = repo / "docs" / f"newapi-sxwl-per-model-validation-{date.today().isoformat()}.md"

    env = os.environ.copy()
    env["NEWAPI_BASE_URL"] = base_url
    if api_key:
        env.setdefault("NEWAPI_API_KEY", api_key)

    py = sys.executable
    test_chat = repo / "test_chat.py"
    rpm_limit = repo / "scripts" / "rpm_until_limit.py"
    rpm_minute = repo / "scripts" / "rpm_minute_window_probe.py"

    results: list[ModelResult] = []
    utc_run = datetime.now(timezone.utc).isoformat(timespec="seconds") + "Z"

    print(f"repo_root={repo}", flush=True)
    print(f"base_url={base_url}", flush=True)
    print(f"output_dir={out_dir}", flush=True)
    print(f"report={report_path}", flush=True)
    print(f"models={len(models)}", flush=True)

    for model in models:
        slug = model_slug(model)
        mr = ModelResult(model=model, slug=slug)
        results.append(mr)
        sub = out_dir / slug

        # --- openai ---
        argv_o = [
            py,
            str(test_chat),
            "--client",
            "openai",
            "--base-url",
            base_url,
            "-m",
            model,
        ]
        if args.dry_run:
            print("[dry-run]", " ".join(argv_o), flush=True)
            mr.steps["openai"] = {"skipped": True, "reason": "dry-run"}
        else:
            log_o = sub / "test_chat_openai.log"
            try:
                code, text, _ = run_cmd(
                    argv_o,
                    cwd=repo,
                    env=env,
                    timeout=600.0,
                    log_path=log_o,
                )
            except subprocess.TimeoutExpired:
                code, text = -1, "TIMEOUT"
                log_o.write_text(redact(text), encoding="utf-8")
            ok = code == 0
            mr.steps["openai"] = {
                "ok": ok,
                "exit_code": code,
                "log_file": str(log_o),
                "log_tail": text[-8000:] if text else "",
            }
            if not ok and not args.continue_on_error:
                mr.steps["anthropic"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["usage"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["rpm_heavy"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["rpm_minute"] = {"skipped": True, "reason": "previous step failed"}
                continue

        # --- anthropic ---
        argv_a = [
            py,
            str(test_chat),
            "--client",
            "anthropic",
            "--base-url",
            base_url,
            "-m",
            model,
        ]
        if args.dry_run:
            print("[dry-run]", " ".join(argv_a), flush=True)
            mr.steps["anthropic"] = {"skipped": True, "reason": "dry-run"}
        else:
            log_a = sub / "test_chat_anthropic.log"
            try:
                code, text, _ = run_cmd(
                    argv_a,
                    cwd=repo,
                    env=env,
                    timeout=600.0,
                    log_path=log_a,
                )
            except subprocess.TimeoutExpired:
                code, text = -1, "TIMEOUT"
                log_a.write_text(redact(text), encoding="utf-8")
            ok = code == 0
            mr.steps["anthropic"] = {
                "ok": ok,
                "exit_code": code,
                "log_file": str(log_a),
                "log_tail": text[-8000:] if text else "",
            }
            if not ok and not args.continue_on_error:
                mr.steps["usage"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["rpm_heavy"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["rpm_minute"] = {"skipped": True, "reason": "previous step failed"}
                continue

        # --- usage ---
        uenv = env.copy()
        uenv["USAGE_BASE_URL"] = base_url.rstrip("/")
        uenv["USAGE_MODEL"] = model
        if args.dry_run:
            print("[dry-run] python -c usage_snippet", model, flush=True)
            mr.steps["usage"] = {"skipped": True, "reason": "dry-run"}
        else:
            log_u = sub / "usage.log"
            try:
                p = subprocess.run(
                    [py, "-c", USAGE_SNIPPET],
                    cwd=str(repo),
                    env=uenv,
                    capture_output=True,
                    text=True,
                    timeout=600.0,
                )
                text = redact((p.stdout or "") + (p.stderr or ""))
                log_u.write_text(text, encoding="utf-8")
                code = p.returncode
            except subprocess.TimeoutExpired:
                code, text = -1, "TIMEOUT"
                log_u.write_text(redact(text), encoding="utf-8")
            ok = code == 0
            mr.steps["usage"] = {
                "ok": ok,
                "exit_code": code,
                "log_file": str(log_u),
                "log_tail": text[-4000:] if text else "",
            }
            if not ok and not args.continue_on_error:
                mr.steps["rpm_heavy"] = {"skipped": True, "reason": "previous step failed"}
                mr.steps["rpm_minute"] = {"skipped": True, "reason": "previous step failed"}
                continue

        # --- rpm_until_limit heavy ---
        if args.skip_heavy:
            mr.steps["rpm_heavy"] = {"skipped": True, "reason": "--skip-heavy"}
        elif args.dry_run:
            print(
                "[dry-run]",
                py,
                str(rpm_limit),
                "--payload heavy --input-tokens 10000 --max-concurrency 16 "
                f"--max-requests 127 --scale double --model {model}",
                flush=True,
            )
            mr.steps["rpm_heavy"] = {"skipped": True, "reason": "dry-run"}
        else:
            jsonl_h = sub / "rpm_heavy.jsonl"
            log_h = sub / "rpm_heavy.log"
            argv_h = [
                py,
                str(rpm_limit),
                "--payload",
                "heavy",
                "--base-url",
                base_url,
                "--input-tokens",
                "10000",
                "--max-concurrency",
                "16",
                "--max-requests",
                "127",
                "--scale",
                "double",
                "--model",
                model,
                "--jsonl-out",
                str(jsonl_h),
            ]
            try:
                code, text, _ = run_cmd(
                    argv_h,
                    cwd=repo,
                    env=env,
                    timeout=1200.0,
                    log_path=log_h,
                )
            except subprocess.TimeoutExpired:
                code, text = -1, "TIMEOUT"
                log_h.write_text(redact(text), encoding="utf-8")
            ok = code == 0
            mr.steps["rpm_heavy"] = {
                "ok": ok,
                "exit_code": code,
                "log_file": str(log_h),
                "jsonl": str(jsonl_h),
                "log_tail": text[-12000:] if text else "",
            }
            if not ok and not args.continue_on_error:
                mr.steps["rpm_minute"] = {"skipped": True, "reason": "previous step failed"}
                continue

        # --- rpm_minute_window ---
        if args.skip_minute:
            mr.steps["rpm_minute"] = {"skipped": True, "reason": "--skip-minute"}
        elif args.dry_run:
            print(
                "[dry-run]",
                py,
                str(rpm_minute),
                "--scheduler batch --payload minimal --scale double "
                f"--start-concurrency 256 --max-concurrency 256 --max-requests 4096 --model {model}",
                flush=True,
            )
            mr.steps["rpm_minute"] = {"skipped": True, "reason": "dry-run"}
        else:
            jsonl_m = sub / "rpm_minute.jsonl"
            log_m = sub / "rpm_minute.log"
            argv_m = [
                py,
                str(rpm_minute),
                "--scheduler",
                "batch",
                "--payload",
                "minimal",
                "--base-url",
                base_url,
                "--model",
                model,
                "--scale",
                "double",
                "--start-concurrency",
                "256",
                "--max-concurrency",
                "256",
                "--max-requests",
                "4096",
                "--jsonl-out",
                str(jsonl_m),
            ]
            try:
                code, text, _ = run_cmd(
                    argv_m,
                    cwd=repo,
                    env=env,
                    timeout=1_800_000.0,
                    log_path=log_m,
                )
            except subprocess.TimeoutExpired:
                code, text = -1, "TIMEOUT"
                log_m.write_text(redact(text), encoding="utf-8")
            mr.steps["rpm_minute"] = {
                "ok": code == 0,
                "exit_code": code,
                "log_file": str(log_m),
                "jsonl": str(jsonl_m),
                "log_tail": text[-12000:] if text else "",
            }

    # JSON 摘要
    if not args.dry_run:
        summary_path = out_dir / "summary.jsonl"
        with summary_path.open("w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r.to_json(), ensure_ascii=False) + "\n")
        print(f"summary.jsonl -> {summary_path}", flush=True)

    if args.dry_run:
        print("dry-run: 未写入 Markdown 报告（避免覆盖 docs）。实跑时写入 --report。", flush=True)
        return

    write_markdown(
        report_path,
        base_url=base_url,
        models=models,
        results=results,
        output_dir=out_dir,
        utc_run=utc_run,
    )
    print(f"report -> {report_path}", flush=True)

    any_fail = any(
        (st.get("ok") is False)
        for r in results
        for st in r.steps.values()
        if isinstance(st, dict) and "ok" in st and not st.get("skipped")
    )
    sys.exit(1 if any_fail else 0)


if __name__ == "__main__":
    main()

# AGENTS.md

This file provides practical guidance for coding agents working in this repository.

## Project overview

- Repo name: `llm_gateways`
- Primary language: Python (requires Python `>=3.13`)
- Package/dependency management: `uv` (preferred) or `pip`
- Main focus:
  - LLM gateway utility scripts
  - NewAPI gateway validation scripts
  - Benchmark stack under `benchmark/` (Mock upstream + NewAPI + Locust)

## Repository layout

- `test_chat.py`  
  Validates NewAPI `chat/completions` compatibility via OpenAI SDK.
- `openrouter.py`  
  Fetches OpenRouter model metadata filtered by provider.
- `max_latency_gemini.py` + `long_prompt_generator.py`  
  Builds huge prompts and measures Gemini high-thinking latency.
- `scripts/newapi_batch_accounts/`  
  Batch NewAPI account creation tooling.
- `docs/newapi-pricing-and-models.md`  
  NewAPI 模型计费、配额、渠道模型列表/映射与补全倍率说明（中文）。
- `scripts/run_dual_overlap_rpm_probe.sh` + `scripts/merge_dual_rpm_probe_window.py`  
  在目标机对任意 OpenAI 兼容 `model` 跑双进程 `rpm_minute_window_probe`（overlap）并合并锚点前 60s 发起数；见 `docs/newapi-mixroute-validation-2026-05-06.md` §6.2。
- `scripts/stream_concurrency_ttft_probe.py`  
  单模型、`stream=True`、Semaphore 限制并发（默认 50→100），测 TTFT 与流式总耗时；四模型分四次各传 `--model`，见 `docs/newapi-mixroute-validation-2026-05-06.md` §6.5。
- `scripts/dual_route_stream_profile_probe.py`  
  四模型 × 多档输入 tiktoken 定长（首行指令 + 填充）、`max_tokens = input/200`（可调），双路线 `inproc`/`subprocess` 或单路 `--dual-mode none`；`--jsonl-layout nested` 时每个 case 独立 `cells/*.jsonl`。`scripts/generate_dual_profile_report.py` 可根据 `*_manifest.json` 与 `*_A/_B_summary.jsonl` 生成简要 Markdown。`scripts/run_per_model_token_profiles_to_md.py` 依次对四模型跑单路线剖面（默认 **并发 100**，样本 **1500→1000 / 15000→500 / 150000→100** 次/档，流式超时 6h）并输出合并 Markdown（见 `docs/per-model-token-profile-2026-05-09.md`）。典型目标机：`ubuntu@18.183.174.245`（`~/llm_gateways`）；全量默认极贵，建议 `nohup`。
- `benchmark/`  
  End-to-end load testing assets and operation docs.

## Environment setup

From repo root:

```bash
uv sync
```

If `uv` is unavailable:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Common run commands

### 1) Test NewAPI chat endpoint

```bash
python test_chat.py \
  --base-url https://your-newapi.example.com/v1 \
  --api-key "$NEWAPI_API_KEY" \
  --models your-model-name
```

Notes:
- You must provide at least one model (`--models` / `-m`).
- API key can also come from `NEWAPI_API_KEY` or `OPENAI_API_KEY`.

### 1b) Stream TTFT / concurrency (single model per run)

```bash
export NEWAPI_BASE_URL="https://api.mixroute.ai/v1"
export NEWAPI_API_KEY="..."
.venv/bin/python scripts/stream_concurrency_ttft_probe.py \
  --model gemini-3-flash-preview \
  --jsonl-out /tmp/stream_ttft_gemini-3-flash-preview.jsonl
```

Repeat with a different `--model` for each of the four models; defaults: `--input-tokens 4096`, `--max-tokens 512`, `--concurrency-list 50,100`, `--samples 100`.

### 1c) 双路线 Token 剖面（RPM / TPM / TTFT / TPS，`1500/15000/150000` 输入档）

在目标机（示例 `ubuntu@18.183.174.245`）配置 `NEWAPI_BASE_URL`、`NEWAPI_API_KEY` 后：

```bash
cd ~/llm_gateways
TS=$(date -u +%Y%m%dT%H%M%SZ)
nohup env PYTHONUNBUFFERED=1 \
  NEWAPI_BASE_URL="https://api.mixroute.ai/v1" \
  NEWAPI_API_KEY="***" \
  .venv/bin/python scripts/dual_route_stream_profile_probe.py \
  --dual-mode subprocess \
  --jsonl-layout nested \
  --emit-summary-jsonl \
  --output-dir /tmp \
  --output-stem "dual_profile_${TS}" \
  --samples-by-input "1500:5,15000:3,150000:1" \
  --intra-route-concurrency 2 \
  --stream-timeout 3600 \
  > "/tmp/dual_profile_${TS}.out" 2>&1 &
```

日志：`/tmp/dual_profile_${TS}.out`；**nested**：逐请求按 case 写入 `/tmp/dual_profile_${TS}_route_A/cells/` 与 `_route_B/cells/`；summary：`*_A_summary.jsonl`、`*_B_summary.jsonl`；manifest：`*_manifest.json`。跑完后（探针退出码可能非 0）可生成简报：  
`.venv/bin/python scripts/generate_dual_profile_report.py --output-dir /tmp --stem dual_profile_${TS} --markdown-out /tmp/dual_profile_${TS}_brief.md --host ubuntu@18.183.174.245`。`150000` 档成本高、耗时长，请先小样本再放大。指标口径见脚本 `--help` 顶部说明；示例报告见 `docs/dual-route-token-profile-brief-2026-05-09.md`。

### 2) Fetch OpenRouter models by provider

```bash
export OPENROUTER_API_KEY=...
python openrouter.py "google,anthropic" --output models.json
```

### 3) Gemini latency probe with long prompt

```bash
export GEMINI_API_KEY=...
python max_latency_gemini.py
```

### 4) NewAPI batch account script

```bash
cd scripts/newapi_batch_accounts
python create_account.py --amount 10
```

Requires `NEWAPI_BASE_URL`, `NEWAPI_ADMIN_USERNAME`, `NEWAPI_ADMIN_PASSWORD`.

### 5) Benchmark docs

Start with:

- `benchmark/README.md`
- `benchmark/OPERATIONS.md`

## Validation guidance for agents

- For small changes, run the most relevant script directly (for example, `python test_chat.py ...`).
- For benchmarking-related changes, validate commands and configuration paths in docs:
  - `benchmark/mock/README.md`
  - `benchmark/locust/README.md`
  - `benchmark/OPERATIONS.md`
- If no automated test suite is present for your modified area, explicitly state what was manually verified.

## Coding and safety conventions

- Keep edits minimal and scoped to the task.
- Do not commit real API keys, tokens, passwords, or `.env` secrets.
- Prefer environment variables for credentials.
- Avoid unnecessary high-cost external API calls during validation unless required by the task.
- Preserve existing Chinese documentation style when editing files that are already Chinese-first.

## Agent workflow expectations

1. Read relevant files before editing.
2. Make focused changes.
3. Run targeted validation commands.
4. Summarize:
   - what changed,
   - how it was validated,
   - any remaining risks or assumptions.

# 四模型 Token 剖面（逐模型 × 三档输入加压）

## 当前默认负载（`run_per_model_token_profiles_to_md.py`）

| 输入档（tiktoken 目标） | 每模型请求次数 | 单路线并发 |
| ----------------------: | -------------: | ---------: |
|                  1500 |           1000 |        100 |
|                 15000 |            500 |        100 |
|                150000 |            100 |        100 |

- **单请求流式超时**：默认 **21600 s**（6 h），可按 `--stream-timeout` 调整。  
- **每模型总请求**：1000 + 500 + 100 = **1600**；四模型合计 **6400** 次（费用与墙钟极高，务必在可承受配额下执行）。  
- **原始数据**：`nested` 布局下每个 case 仍为 `…/run/cells/<model>__in<N>__routesingle.jsonl`（该文件内 **一行一次请求**）。

## 在目标机上执行（建议 nohup）

在 `ubuntu@18.183.174.245` 的 `~/llm_gateways` 中已配置 **`NEWAPI_API_KEY`**（勿写入仓库、勿贴聊天）后：

```bash
cd ~/llm_gateways
ROOT=/tmp/per_model_token_md_$(date -u +%Y%m%dT%H%M%SZ)
MD=/tmp/per_model_token_md_brief_$(date -u +%Y%m%dT%H%M%SZ).md
nohup env PYTHONUNBUFFERED=1 \
  .venv/bin/python scripts/run_per_model_token_profiles_to_md.py \
  --markdown-out "$MD" \
  --output-dir "$ROOT" \
  --host-note "ubuntu@18.183.174.245" \
  >"${MD%.md}.out" 2>&1 &
```

默认即 **并发 100** 与 **1500:1000,15000:500,150000:100**；若需摸底可显式传入例如  
`--samples-by-input "1500:10,15000:5,150000:2" --intra-route-concurrency 10`。  
**单模型单档**（减轻配额/速率压力）：`--models claude-sonnet-4-6 --input-tokens 1500 --samples-by-input 1500:1000`。遇 **429** 时探针默认 **立即中止**（退出码 **3**），无自动 sleep；需继续时由你择时重跑；若要坚持跑满本 cell 可传 `--no-abort-on-429`（详见探针 `--help`）。分步跑批见 [per-model-token-profile-nohup-20260509T063432Z.md](per-model-token-profile-nohup-20260509T063432Z.md) 文末「分步重跑」节。

完成后将 **`$MD`** 拷回本仓库覆盖本文件或另存为新日期的 `docs/per-model-token-profile-*.md`。

### 2026-05-09 nohup 全量跑批结果（已完成）

- **批次 stem**：`per_model_token_md_nohup_20260509T063432Z`  
- **远端根目录（服务器）**：`/tmp/per_model_token_md_nohup_20260509T063432Z`（跑批当时；逐请求 JSONL 与各模型 `run_summary.jsonl` 均在其下子目录）  
- **标准输出日志（服务器）**：`/tmp/per_model_token_md_nohup_20260509T063432Z_brief.out`  
- **TOS 归档**：对象键前缀 `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/`（正文路径见 [per-model-token-profile-nohup-20260509T063432Z.md](per-model-token-profile-nohup-20260509T063432Z.md)；本地 `tos_staging/` 已删除）；**公网直链模板与示例**见该文档「火山引擎 TOS 归档 → 公网 URL」  
- **本仓库归档（完整表格 + 每格 JSONL 路径）**：[per-model-token-profile-nohup-20260509T063432Z.md](per-model-token-profile-nohup-20260509T063432Z.md)

**结论摘要**：

1. **`claude-opus-4-6`**：1500 档 **1000/1000** 成功；15000 档 **483/500** 成功、**17** 次 **429**（网关文案为「当前分组上游负载已饱和，请稍后再试」）；150000 档 **100/100** 成功。探针进程退出码 **0**。  
2. **`claude-sonnet-4-6`、`gemini-3-flash-preview`、`gemini-3.1-pro-preview`**：三档均为 **`n_ok=0`**，错误为 **403 `PermissionDeniedError`**，消息 **`user quota insufficient`**（账户余额/配额不足）。RPM 等成功路径指标为 **`null`**，**不能** 与 opus 成功档做性能对比，仅代表计费侧拒绝。  
3. **复盘**：若要对四模型做同口径可比跑批，需先保证余额与配额充足；或对大消耗模型与轻量模型 **分账号 / 分时段** 跑，避免前置 opus 全量加压耗尽同一 Key 的配额。

**安全**：目标机上的 `NEWAPI_API_KEY` 勿写入仓库；若密钥曾出现在不可信渠道，请 **轮换**。

---

## 附录：历史说明与旧小样本结果（单次请求 / 未跑 150000）

以下内容为 **2026-05-09** 在密钥修复后、**每档仅 1 次请求** 且 **`150000:0`** 的冒烟数据，**与上表默认负载无关**，仅作连通性参考。

- **根因回顾**：此前目标机未配置有效 `NEWAPI_API_KEY` 时出现 **401**，与模型能力无关。  
- **`mean_ttft_s` 为 `null`**：个别 Gemini cell 流式 delta 无可见首包但 `usage.completion_tokens` > 0 时，探针使用 **`usage_only_no_stream_delta`** 回退，TPS 可能带 `tps_approx`（见 JSONL）。  
- **安全**：任何曾出现在聊天中的 Key 应按泄露处理并 **轮换**。

**旧批次根目录**：`/tmp/per_model_token_md_final_20260509T062124Z`

### `claude-opus-4-6`

| input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始请求 JSONL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1500 | 7 | 1 | 1 | 0 | 23.8009 | 39247.75 | 2.4748 | 6392.6941 | `/tmp/per_model_token_md_final_20260509T062124Z/claude-opus-4-6/run/cells/claude-opus-4-6__in1500__routesingle.jsonl` |
| 15000 | 75 | 1 | 1 | 0 | 15.8896 | 262163.23 | 1.7638 | 40.7397 | `/tmp/per_model_token_md_final_20260509T062124Z/claude-opus-4-6/run/cells/claude-opus-4-6__in15000__routesingle.jsonl` |

### `claude-sonnet-4-6`

| input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始请求 JSONL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1500 | 7 | 1 | 1 | 0 | 23.4462 | 38803.44 | 2.5170 | 9150.3268 | `/tmp/per_model_token_md_final_20260509T062124Z/claude-sonnet-4-6/run/cells/claude-sonnet-4-6__in1500__routesingle.jsonl` |
| 15000 | 75 | 1 | 1 | 0 | 15.7981 | 260874.69 | 2.5283 | 60.5015 | `/tmp/per_model_token_md_final_20260509T062124Z/claude-sonnet-4-6/run/cells/claude-sonnet-4-6__in15000__routesingle.jsonl` |

### `gemini-3-flash-preview`

| input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始请求 JSONL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1500 | 7 | 1 | 1 | 0 | 37.6455 | 76495.65 | 1.5870 | 1.8828 | `/tmp/per_model_token_md_final_20260509T062124Z/gemini-3-flash-preview/run/cells/gemini-3-flash-preview__in1500__routesingle.jsonl` |
| 15000 | 75 | 1 | 1 | 0 | 35.1505 | 714153.06 | null | 42.1896 | `/tmp/per_model_token_md_final_20260509T062124Z/gemini-3-flash-preview/run/cells/gemini-3-flash-preview__in15000__routesingle.jsonl` |

### `gemini-3.1-pro-preview`

| input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始请求 JSONL |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1500 | 7 | 1 | 1 | 0 | 26.6756 | 53538.02 | 2.2460 | 1.3340 | `/tmp/per_model_token_md_final_20260509T062124Z/gemini-3.1-pro-preview/run/cells/gemini-3.1-pro-preview__in1500__routesingle.jsonl` |
| 15000 | 75 | 1 | 1 | 0 | 20.1716 | 408716.38 | null | 24.2086 | `/tmp/per_model_token_md_final_20260509T062124Z/gemini-3.1-pro-preview/run/cells/gemini-3.1-pro-preview__in15000__routesingle.jsonl` |

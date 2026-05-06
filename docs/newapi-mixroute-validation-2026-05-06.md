# NewAPI（api.mixroute.ai）连通性与指标验证报告

**执行日期**：2026-05-06（UTC 以远程命令时间为准）  
**执行主机**：`ubuntu@54.238.141.156`（AWS，`Linux 6.17.0-1007-aws`，主机名 `ip-172-31-4-1`）  
**约束**：全部 API 调用与脚本均在上述主机通过 SSH 执行。  
**网关**：`https://api.mixroute.ai/v1`  
**API Key**：报告中不出现明文；若 Key 曾出现在聊天或其它非私密渠道，**请在 NewAPI 后台尽快轮换**。

**前置对照**：[newapi-mixroute-validation-2026-04-09.md](newapi-mixroute-validation-2026-04-09.md)

---

## 1. 环境（目标机）

| 项目 | 结果 |
|------|------|
| 代码 | `~/llm_gateways`（与仓库同步；独立 `.venv`） |
| Python | **3.12.3** |
| openai / anthropic / tiktoken | **2.31.0** / **0.92.0** / **0.12.0** |

---

## 2. 连通性：OpenAI SDK（`test_chat.py --client openai`）

```bash
cd ~/llm_gateways
export NEWAPI_BASE_URL="https://api.mixroute.ai/v1"
export NEWAPI_API_KEY="***"
.venv/bin/python test_chat.py \
  --client openai \
  --base-url "$NEWAPI_BASE_URL" \
  --api-key "$NEWAPI_API_KEY" \
  -m claude-opus-4-6 \
  -m claude-sonnet-4-6 \
  -m gemini-3-flash-preview \
  -m gemini-3.1-pro-preview
```

**原始输出（`api_key` 已替换为 `***`）**：

```
Namespace(client='openai', base_url='https://api.mixroute.ai/v1', api_key='***', models_list=['claude-opus-4-6', 'claude-sonnet-4-6', 'gemini-3-flash-preview', 'gemini-3.1-pro-preview'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://api.mixroute.ai/v1, models=claude-opus-4-6, claude-sonnet-4-6, gemini-3-flash-preview, gemini-3.1-pro-preview
  [claude-opus-4-6] OK (3.01s): 你好！我是Claude，由Anthropic开发的AI助手，乐于通过对话帮助你解答问题、完成任务或探讨各种话题。
  [claude-sonnet-4-6] OK (2.16s): 你好！我是 **Claude**，一个由 Anthropic 开发的 AI 助手，致力于以友好、准确、有帮助的方式回答您的问题。😊
  [gemini-3-flash-preview] OK (3.81s): 我是一个由 Google 训练的大型语言模型，旨在为你提供信息、解答问题并协助你完成各种任务。
  [gemini-3.1-pro-preview] OK (7.05s): 你好，我是由 Google 训练的大型语言模型 Gemini，随时准备为你提供信息、解答
4/4 passed. Exit 0.
```

**结论**：四模型 **全部通过**，退出码 0。

---

## 3. Anthropic SDK / Messages API（`test_chat.py --client anthropic`）与 OpenAI 回归

### 3.1 Anthropic 客户端（四模型）

**原始输出（`api_key` 已替换为 `***`）**：

```
Namespace(client='anthropic', base_url='https://api.mixroute.ai/v1', api_key='***', models_list=['claude-opus-4-6', 'claude-sonnet-4-6', 'gemini-3-flash-preview', 'gemini-3.1-pro-preview'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://api.mixroute.ai, models=claude-opus-4-6, claude-sonnet-4-6, gemini-3-flash-preview, gemini-3.1-pro-preview
  [claude-opus-4-6] OK (2.47s): 你好！我是Claude，由Anthropic公司开发的AI助手，旨在提供有帮助、诚实且安全的对话。
  [claude-sonnet-4-6] OK (2.10s): 你好！我是 **Claude**，一个由 Anthropic 开发的 AI 助手，致力于为你提供有帮助、准确且友好的对话与解答。😊
  [gemini-3-flash-preview] OK (2.47s): 你好！我是由 Google 训练的大型语言模型。
  [gemini-3.1-pro-preview] OK (7.68s): 你好！我是由 Google 开发的大型语言模型 Gemini，致力于为您解答疑问、提供灵感并
4/4 passed. Exit 0.
```

### 3.2 OpenAI 回归（单模型）

```
Namespace(client='openai', base_url='https://api.mixroute.ai/v1', api_key='***', models_list=['claude-opus-4-6'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://api.mixroute.ai/v1, models=claude-opus-4-6
  [claude-opus-4-6] OK (2.61s): 你好！我是Claude，由Anthropic开发的AI助手，致力于以安全、诚实和有帮助的方式与人交流。
1/1 passed. Exit 0.
```

---

## 4. Usage 采样（每模型 1 次，`max_tokens=512`，默认 prompt）

| 模型 | prompt_tokens | completion_tokens | total_tokens | 墙钟耗时 (s) |
|------|----------------|-------------------|--------------|--------------|
| claude-opus-4-6 | 23 | 45 | 68 | 2.78 |
| claude-sonnet-4-6 | 23 | 57 | 80 | 2.07 |
| gemini-3-flash-preview | 10 | 303 | 313 | 2.54 |
| gemini-3.1-pro-preview | 10 | 508 | 518 | 7.20 |

**说明**：Gemini 系列在相同 `max_tokens=512` 下 `completion_tokens` 可能高于 Claude，与网关/上游对思考或多段输出的统计方式有关；以网关返回的 `usage` 为准。

---

## 5. 吞吐：`rpm_until_limit.py`（heavy，与 4 月报告 §5.1.1 同参）

**参数**：`--payload heavy`、`--input-tokens 10000`、`--max-concurrency 16`、`--max-requests 127`、`--scale double`；模型默认 `gemini-3-flash-preview`。  
**远端归档**：`/tmp/rpm_heavy_20260506.jsonl`（与本次 stdout 同源）。

```
rpm_until_limit payload=heavy base_url=https://api.mixroute.ai/v1 model=gemini-3-flash-preview max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
```

```
--- summary ---
stop_reason=max_concurrency_no_limit_hit
successful_requests=31
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=50.6499
approx_throughput_rpm=36.72
latency_s min=7.3384 p50=8.8804 max=14.9231
```

**结论**：并发阶梯 1→16，**31** 次成功，**未出现 429**。与 2026-04-09 同参相比，本次总墙钟更短（**50.65s** vs 当时 **86.12s**），`approx_throughput_rpm` 更高，属时段与负载波动，不宜单点外推容量。

**本次未重跑**：4 月文档 §5.1.2 的 heavy **32→512** 高并发探针（费用与耗时极高，需 `--i-know-expensive`）；若需对照历史 **992** 次成功那一轮，请在目标机按需单独执行。

---

## 6. RPM 窗口探针：`rpm_minute_window_probe.py`（batch + minimal）

**参数**：`--scheduler batch`、`--payload minimal`、`--model gemini-3-flash-preview`、`--scale double`、`--start-concurrency 256`、`--max-concurrency 256`、`--max-requests 4096`。  
**远端归档**：`/tmp/rpm_minute_window_256x16_20260506.jsonl`。

```
--- summary ---
stop_reason=max_requests
successful_requests=4096
total_attempts=4096
rounds_run=16
peak_concurrency=256
total_wall_s=141.8231
approx_throughput_rpm=1732.86
reference_only_last_start_t=1778048721.102207 window_60s_requests_started=1024 (no API failure; stop=max_requests; not a rate-limit RPM)
latency_s min=1.3015 p50=3.5629 max=47.9287
```

**结论**：**全程无 API 失败**，用尽 `max_requests` 结束；`window_60s_requests_started` 为脚本在 **无首次失败** 时以最后一次发起为锚的**参考值**，**不代表**触限 RPM（口径见 [newapi-mixroute-validation-2026-04-09.md](newapi-mixroute-validation-2026-04-09.md) §6）。

**本次未重跑**：`--scheduler overlap` 及更大 `max_concurrency` 组合（参见 4 月文档 §6）。

---

## 7. 总结

- **连通性**：四模型在目标机上 **`/v1/chat/completions`（OpenAI SDK）** 与 **`/v1/messages`（Anthropic SDK）** 均通过。  
- **吞吐 vs RPM**：§5 与 §6 的统计口径不同，勿与 4 月数值直接混比为「变差/变好」的绝对结论。  
- **安全**：勿在聊天或文档中粘贴明文 Key；本次用于跑通的 Key 若已暴露，请**轮换**。

---

*本报告对应主机 `ubuntu@54.238.141.156`，2026-05-06 实测输出已脱敏整理。*

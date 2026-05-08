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

**结论**：**全程无 API 失败**，用尽 `max_requests` 结束；`window_60s_requests_started` 为脚本在 **无首次失败** 时以最后一次发起为锚的**参考值**，**不代表**触限 RPM（口径见 [newapi-mixroute-validation-2026-04-09.md](newapi-mixroute-validation-2026-04-09.md) §6）。**2026-05-06 当日**未再跑 4 月文档中的 `overlap` 更大档；**`overlap` 与首次失败窗口 RPM 的补充实测见 §6.1**（2026-05-07）。

### 6.1 补充（2026-05-07）：双进程 overlap 加压 —— 首次失败锚定的窗口 RPM（含服务端错误）

在一轮**刻意加压**中，将「429 以外的首次失败」（连接错误、超时等）也视为需要记录的**稳定性阈值**：仍采用技术版 §6 的定义 —— **以首次失败请求的发起时刻 \(t^\*\) 为锚**，统计闭区间 \([t^\*-60\text{s},\, t^\*]\) 内**曾经发起**的请求个数（`window_60s_requests_started`）。

**场景**：同一主机上 **两个进程并行**运行 `rpm_minute_window_probe.py`（调度均为 `--scheduler overlap`、`--payload minimal`、`--model gemini-3-flash-preview`、`--scale double`、`--start-concurrency 2048`、`--max-concurrency 12000`、`--ramp-interval-sec 1`、`--max-requests 2048`）；网关总负载约为双进程叠加，以下指标来自**先触发失败的进程**（归档：`/tmp/rpm_dual_A.out`）。

**进程 A — `--- summary ---`（节选）**：

```
stop_reason=APIConnectionError
successful_requests=1528
total_attempts=2048
first_failure_i=1380 anchor_t_start=1778157963.657488 window_60s_requests_started=1380
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
approx_throughput_rpm=88.04
total_wall_s=1041.3989
latency_s min=406.2005 p50=920.9686 max=1039.5017
```

**计算与表述**：

- **窗口 RPM（发起计数，脚本口径，仅进程 A）**：`window_60s_requests_started` = **1380**。含义：在锚点 \(t^\*\) 前 **60 秒**内，**进程 A** 记录到的 **HTTP 发起次数**（含随后失败的一批）；**不是** HTTP 429 限流读数，失败形态以 **`APIConnectionError` / `APITimeoutError`** 为主（连接重置、请求超时等）。
- **双进程合并（同一锚点、手工统计）**：锚点仍取 **进程 A** summary 中的 `anchor_t_start`（与脚本首次失败锚一致）。对归档 **`/tmp/rpm_dual_A.out`**、**`/tmp/rpm_dual_B.out`** 中全部 **`ok` / `fail`** 行解析 `t_start`，落在闭区间 \([t^\*-60\text{s},\, t^\*]\) 内的条数分别记为 \(N_A,\, N_B\)（两进程为独立客户端，请求互不重复），**合并窗口内发起数**为 \(N_A + N_B\)。  
  **本次实测**：\(N_A = 1380\)（与脚本字段一致），\(N_B = 1385\)（两进程启动与爬坡节奏略有差别，故与 1380 不完全相同），**合并** **\(N_A + N_B = 2765\)**。
- **整段墙钟平均完成节奏（对照）**：`approx_throughput_rpm` ≈ **88**（成功次数 ÷ `total_wall_s` × 60；与窗口发起计数 **不可混用**）。

**TPM（粗算，基于单次 input/output 假设 × 窗口内合并发起数）**：本次日志**未逐条采集** `usage`，以下为**估算**；真实计费以网关/账单为准。负载为 **`--payload minimal`**、默认 `--prompt`（`Reply with exactly: OK`）、**`max_tokens=64`**。

| 口径 | 单次 input（约） | 单次 output（约） | 单次合计（约） | TPM（≈ 2765 × 单次合计） |
|------|------------------|-------------------|----------------|---------------------------|
| **A 下限**（仅用户正文 tiktoken + 极短完成） | **5**（`tiktoken` `cl100k_base`，不含模板） | **3**（按仅输出 `OK` 量级） | **8** | **2765 × 8 ≈ 2.21 万** |
| **B 中位（推荐用来对齐「账单量级」粗算）** | **30**（在 5 基础上假设网关/模板等 **prompt** 侧合计） | **10**（短完成；上限仍为 64） | **40** | **2765 × 40 ≈ 11.1 万** |
| **C 宽松上沿**（与 llm.sxwl 逐模型验证里 minute 探针 **~200 token/次** 粗算口径并列，偏保守） | — | — | **200** | **2765 × 200 ≈ 55.3 万** |

**说明**：窗口内大量请求以 **超时/连接错误** 结束，未必产生完整 completion；上表按「若按发起次数 × 单次 token 假设」推算 **理论量级**，**不等同**于账单分钟窗口内实际结算 token。

**结论**：在该次 **双进程 overlap + 高 in-flight** 形态下，**首次出现大批错误时**，以 A 的失败时刻为锚，**单机双进程在该 60 秒窗口内合计发起约 2765 次**（单进程脚本字段为 **1380**）。**TPM** 粗算见上表（中位约 **11 万 TPM**、与旧文档并列的宽松口径约 **55 万 TPM**）。对外沟通时宜标明：**失败类型为连接/超时类，非 429；结论不宜单点外推为「官方 RPM/TPM 上限」**。

---

## 7. 总结

- **连通性**：四模型在目标机上 **`/v1/chat/completions`（OpenAI SDK）** 与 **`/v1/messages`（Anthropic SDK）** 均通过。  
- **吞吐 vs RPM**：§5 与 §6 的统计口径不同，勿与 4 月数值直接混比为「变差/变好」的绝对结论。  
- **RPM / TPM 窗口（§6.1）**：在 2026-05-07 双进程 overlap 加压下，进程 A 脚本字段 **`window_60s_requests_started` = 1380**；同锚点合并 A+B 日志后 **60 秒窗口内发起合计 ≈ 2765**。按 §6.1 单次 token 假设，**TPM 粗算中位约 11 万 / 分钟量级**（宽松并列口径约 **55 万**）；均为估算，非账单值。  
- **安全**：勿在聊天或文档中粘贴明文 Key；本次用于跑通的 Key 若已暴露，请**轮换**。

---

*本报告对应主机 `ubuntu@54.238.141.156`；2026-05-06 为主体验证日，§6.1 为 2026-05-07 补充加压与归档说明，输出已脱敏整理。*

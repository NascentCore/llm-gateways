# NewAPI（api.mixroute.ai）连通性与指标验证报告

**执行日期**：2026-05-06（UTC 以远程命令时间为准）  
**执行主机**：`ubuntu@54.238.141.156`（AWS，`Linux 6.17.0-1007-aws`，主机名 `ip-172-31-4-1`）  
**约束**：全部 API 调用与脚本均在上述主机通过 SSH 执行。  
**网关**：`https://api.mixroute.ai/v1`  
**API Key**：报告中不出现明文；若 Key 曾出现在聊天或其它非私密渠道，**请在 NewAPI 后台尽快轮换**。

**前置对照**：[newapi-mixroute-validation-2026-04-09.md](newapi-mixroute-validation-2026-04-09.md)

---

## 1. 环境（目标机）


| 项目                            | 结果                                   |
| ----------------------------- | ------------------------------------ |
| 代码                            | `~/llm_gateways`（与仓库同步；独立 `.venv`）   |
| Python                        | **3.12.3**                           |
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

**原始输出（`api_key` 已替换为 `*`**）**：

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

**原始输出（`api_key` 已替换为 `*`**）**：

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


| 模型                     | prompt_tokens | completion_tokens | total_tokens | 墙钟耗时 (s) |
| ---------------------- | ------------- | ----------------- | ------------ | -------- |
| claude-opus-4-6        | 23            | 45                | 68           | 2.78     |
| claude-sonnet-4-6      | 23            | 57                | 80           | 2.07     |
| gemini-3-flash-preview | 10            | 303               | 313          | 2.54     |
| gemini-3.1-pro-preview | 10            | 508               | 518          | 7.20     |


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

**结论**：**全程无 API 失败**，用尽 `max_requests` 结束；`window_60s_requests_started` 为脚本在 **无首次失败** 时以最后一次发起为锚的**参考值**，**不代表**触限 RPM（口径见 [newapi-mixroute-validation-2026-04-09.md](newapi-mixroute-validation-2026-04-09.md) §6）。**2026-05-06 当日**未再跑 4 月文档中的 `overlap` 更大档；`**overlap` 与首次失败窗口 RPM 的补充实测见 §6.1**（2026-05-07）。

### 6.1 补充（2026-05-07）：双进程 overlap 加压 —— 首次失败锚定的窗口 RPM（含服务端错误）

在一轮**刻意加压**中，将「429 以外的首次失败」（连接错误、超时等）也视为需要记录的**稳定性阈值**：仍采用技术版 §6 的定义 —— **以首次失败请求的发起时刻 t^ 为锚**，统计闭区间 [t^-60\text{s}, t^] 内**曾经发起**的请求个数（`window_60s_requests_started`）。

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

- **窗口 RPM（发起计数，脚本口径，仅进程 A）**：`window_60s_requests_started` = **1380**。含义：在锚点 t^ 前 **60 秒**内，**进程 A** 记录到的 **HTTP 发起次数**（含随后失败的一批）；**不是** HTTP 429 限流读数，失败形态以 `**APIConnectionError` / `APITimeoutError`** 为主（连接重置、请求超时等）。
- **双进程合并（同一锚点、手工统计）**：锚点仍取 **进程 A** summary 中的 `anchor_t_start`（与脚本首次失败锚一致）。对归档 `**/tmp/rpm_dual_A.out`**、`**/tmp/rpm_dual_B.out**` 中全部 `**ok` / `fail**` 行解析 `t_start`，落在闭区间 [t^-60\text{s}, t^] 内的条数分别记为 N_A, N_B（两进程为独立客户端，请求互不重复），**合并窗口内发起数**为 N_A + N_B。  
**本次实测**：N_A = 1380（与脚本字段一致），N_B = 1385（两进程启动与爬坡节奏略有差别，故与 1380 不完全相同），**合并** **N_A + N_B = 2765**。
- **整段墙钟平均完成节奏（对照）**：`approx_throughput_rpm` ≈ **88**（成功次数 ÷ `total_wall_s` × 60；与窗口发起计数 **不可混用**）。

**TPM（粗算，基于单次 input/output 假设 × 窗口内合并发起数）**：本次日志**未逐条采集** `usage`，以下为**估算**；真实计费以网关/账单为准。负载为 `**--payload minimal`**、默认 `--prompt`（`Reply with exactly: OK`）、`**max_tokens=64**`。


| 口径                                                                  | 单次 input（约）                            | 单次 output（约）        | 单次合计（约） | TPM（≈ 2765 × 单次合计）      |
| ------------------------------------------------------------------- | -------------------------------------- | ------------------- | ------- | ----------------------- |
| **A 下限**（仅用户正文 tiktoken + 极短完成）                                     | **5**（`tiktoken` `cl100k_base`，不含模板）   | **3**（按仅输出 `OK` 量级） | **8**   | **2765 × 8 ≈ 2.21 万**   |
| **B 中位（推荐用来对齐「账单量级」粗算）**                                            | **30**（在 5 基础上假设网关/模板等 **prompt** 侧合计） | **10**（短完成；上限仍为 64） | **40**  | **2765 × 40 ≈ 11.1 万**  |
| **C 宽松上沿**（与 llm.sxwl 逐模型验证里 minute 探针 **~200 token/次** 粗算口径并列，偏保守） | —                                      | —                   | **200** | **2765 × 200 ≈ 55.3 万** |


**说明**：窗口内大量请求以 **超时/连接错误** 结束，未必产生完整 completion；上表按「若按发起次数 × 单次 token 假设」推算 **理论量级**，**不等同**于账单分钟窗口内实际结算 token。

**结论**：在该次 **双进程 overlap + 高 in-flight** 形态下，**首次出现大批错误时**，以 A 的失败时刻为锚，**单机双进程在该 60 秒窗口内合计发起约 2765 次**（单进程脚本字段为 **1380**）。**TPM** 粗算见上表（中位约 **11 万 TPM**、与旧文档并列的宽松口径约 **55 万 TPM**）。对外沟通时宜标明：**失败类型为连接/超时类，非 429；结论不宜单点外推为「官方 RPM/TPM 上限」**。

### 6.2 补充（2026-05-08）：第二模型 `claude-sonnet-4-6` — 同构双进程 overlap（复现与 TPM 系数）

**目的**：在 **与 §6.1 相同** 的加压形态下，对 **另一 OpenAI 兼容模型** `claude-sonnet-4-6` 复测「首次失败锚点 + 双路合并窗口发起数」，并按 **input/output 假设** 粗算 TPM（仍无逐条 `usage`，非账单）。

**参数**：与 §6.1 完全一致（`--scheduler overlap`、`--payload minimal`、`--scale double`、`--start-concurrency 2048`、`--max-concurrency 12000`、`--ramp-interval-sec 1`、`--max-requests 2048`），仅 `**--model claude-sonnet-4-6`**。

**仓库脚本（目标机 `~/llm_gateways`、已配置 `NEWAPI_BASE_URL` / `NEWAPI_API_KEY`）**：

```bash
cd ~/llm_gateways
./scripts/run_dual_overlap_rpm_probe.sh claude-sonnet-4-6
# 合并：--log-a 须为「含首次失败锚点 summary」的那一路（本次为 B），另一路为 --log-b。
.venv/bin/python scripts/merge_dual_rpm_probe_window.py \
  --log-a /tmp/rpm_dual_sonnet_20260508T015117Z_B.out \
  --log-b /tmp/rpm_dual_sonnet_20260508T015117Z_A.out
```

合并脚本会打印 `**merged_in_window**`（记为 N_{\text{merge}}），以及 `**reported_window_60s_requests_started_from_log_a**`（此处即 B 路脚本字段）。

**本次实测（2026-05-08，`TS=20260508T015117Z`，归档 `/tmp/rpm_dual_sonnet_20260508T015117Z_{A,B}.out`）**：

- **进程 A**：**全程无 API 失败**，`stop_reason=max_requests`，**2048/2048** 成功；`approx_throughput_rpm≈80.23`，`total_wall_s≈1531.60s`；summary 中 `**reference_only_... window_60s_requests_started=1169`**（无首次失败，**非** §6 触限读数）。
- **进程 B**：首次失败为 `**APITimeoutError`**，`successful_requests=1627`，`total_attempts=2048`；`**first_failure_i=1718**`，`**anchor_t_start=1778205080.941799**`，`**window_60s_requests_started=1718**`（**60 秒窗口内发起数**，脚本口径）。
- **双进程合并**：以 **B** 的 `anchor_t_start` 为锚，对两路日志中全部 `**ok` / `fail`** 行的 `**t_start**` 落在 **anchor−60s, anchor** 内计数。执行 `**merge_dual_rpm_probe_window.py --log-a …_B.out --log-b …_A.out`**（仓库脚本）得：**B 路窗内 1718**、**A 路窗内 1711**、`**merged_in_window` = 3429**。

**窗口 RPM（合并，脚本口径）**：锚定 60 秒闭区间内**两进程发起次数之和**为 **3429**；与 §6 定义一致时，可表述为该窗口内的 **「合并窗口发起 RPM」≈ 3429**（即 **3429 次/60s** 量级；**勿**与整段墙钟 `approx_throughput_rpm` 混用）。

**TPM 粗算（N_{\text{merge}}=3429，非账单）**：负载仍为 **minimal**；系数同下表（**真实以账单为准**）。


| 口径                          | 单次 input（约） | 单次 output（约） | 单次合计（约） | TPM（3429 \times 单次合计）   |
| --------------------------- | ----------- | ------------ | ------- | ----------------------- |
| **A 下限**                    | **5**       | **3**        | **8**   | **3429 × 8 ≈ 2.74 万**   |
| **B 中位（Claude minimal 粗算）** | **35**      | **12**       | **47**  | **3429 × 47 ≈ 16.1 万**  |
| **C 宽松**                    | —           | —            | **200** | **3429 × 200 ≈ 68.6 万** |


### 6.3 补充（2026-05-08）：`claude-opus-4-6` — 同构双进程 overlap（未观测首次失败）

**参数**：与 §6.2 相同（`overlap`、`minimal`、`2048→12000`、`ramp=1s`、`max_requests=2048`），`**--model claude-opus-4-6`**。  
**归档**：`/tmp/rpm_dual_claude-opus-4-6_20260508T040445Z_A.out`、`…_B.out`。

**结果**：**两进程均为 `stop_reason=max_requests`，2048/2048 成功**，**全程无 `first_failure` / `anchor_t_start`**，故 **不适用** §6.1 / §6.2 的「首次失败锚定 + 双路合并 `**merged_in_window`**」口径（与「无触限读数」一致）。


| 进程  | `total_wall_s`（约） | `approx_throughput_rpm` | `reference_only … window_60s_requests_started` |
| --- | ----------------- | ----------------------- | ---------------------------------------------- |
| A   | 970.93            | **126.56**              | **1350**（无首次失败，**非**触限 RPM）                    |
| B   | 987.83            | **124.39**              | **1050**（同上）                                   |


**整段墙钟 TPM 粗算（单进程、与窗口锚定 TPM 不同）**：在 **minimal** 下沿用 **Claude 粗算单次合计 47**（同 §6.2 B 中位），按 `**approx_throughput_rpm × 47`** 得 **单进程** 量级：**A** ≈ **126.56×47 ≈ 0.59 万 TPM/分钟**、**B** ≈ **124.39×47 ≈ 0.58 万**；若改用 **×40**（与 §6.1 Gemini 中位假设并列）则各约 **0.51 万 / 0.50 万**。均为粗算，非账单。

### 6.4 补充（2026-05-08）：`gemini-3.1-pro-preview` — 同构双进程 overlap（未观测首次失败）

**参数**：同 §6.3，`**--model gemini-3.1-pro-preview`**。  
**归档**：`/tmp/rpm_dual_gemini-3_1-pro-preview_20260508T042115Z_A.out`、`…_B.out`。

**结果**：**两进程均为 `stop_reason=max_requests`，2048/2048 成功**，**无首次失败锚**，**无 `merged_in_window`（触限口径）**。


| 进程  | `total_wall_s`（约） | `approx_throughput_rpm` | `reference_only … window_60s_requests_started` |
| --- | ----------------- | ----------------------- | ---------------------------------------------- |
| A   | 1554.62           | **79.04**               | **1448**（参考，非触限）                               |
| B   | 1553.54           | **79.10**               | **1847**（参考，非触限）                               |


**整段墙钟 TPM 粗算（单进程）**：与 §6.1 并列，取单次合计 **40**（**input≈30 + output≈10** 假设）：**A** ≈ **79.04×40 ≈ 0.32 万 TPM/分钟**、**B** ≈ **79.10×40 ≈ 0.32 万**；下限 **×8**、宽松 **×200** 可同式类推。

### 6.5 补充：四模型 **stream** 并发 TTFT / 流式总耗时（**分四次、每次单模型**）

**目的**：在**固定一种**「长输入 + 有界输出」负载下，用 OpenAI 兼容 **`stream=True`**，分别在 **50** 与 **100** 路并发（`asyncio.Semaphore`）各跑 **`--samples`（默认 100）** 次，观察 **首 token 延迟（TTFT）** 与 **整段流式墙钟** 的均值与分位数；**与 §6.1–§6.4 的 RPM 探针（多为非流式 / 不同脚本）口径不同，勿混读**。

**仓库脚本**：[scripts/stream_concurrency_ttft_probe.py](../scripts/stream_concurrency_ttft_probe.py)（**必选** `--model`，**一次命令只跑一个模型**；四模型请依次执行 **4 条命令**，避免同进程对多模型叠加加压）。

**负载（默认，可用 CLI 覆盖）**：

- 用户正文：`openai_probe_payload.build_heavy_user_content`，**`--input-tokens 4096`**（`tiktoken` **`cl100k_base`** 目标长度）。
- **`--max-tokens 512`**（输出上界；网关返回的 `usage` 可能与 tiktoken 目标有偏差，以账单为准）。

**指标（脚本定义）**：

- **TTFT**：自发起 `chat.completions.create(..., stream=True)` 起，至首个 **非空** `delta.content`；若为空则尝试 **`delta.reasoning_content`** 等增量字段（Gemini 等可能出现「首包在 reasoning」）。
- **总处理时间（单请求）**：同一次流从发起到迭代结束的总墙钟。
- **聚合**：仅对 **成功** 请求统计 `mean` / `p50` / `p95`；另输出 **`n_fail`** 与 **`wall_s`**（该档内发完 `samples` 条并全部结束的批次墙钟，与单请求均值不同）。

**执行与归档（示例；请将 `***` 换为环境变量或密钥注入方式，勿写入仓库）**：

```bash
cd ~/llm_gateways
export NEWAPI_BASE_URL="https://api.mixroute.ai/v1"
export NEWAPI_API_KEY="***"

.venv/bin/python scripts/stream_concurrency_ttft_probe.py \
  --model claude-opus-4-6 --jsonl-out "/tmp/stream_ttft_claude-opus-4-6.jsonl"
.venv/bin/python scripts/stream_concurrency_ttft_probe.py \
  --model claude-sonnet-4-6 --jsonl-out "/tmp/stream_ttft_claude-sonnet-4-6.jsonl"
.venv/bin/python scripts/stream_concurrency_ttft_probe.py \
  --model gemini-3-flash-preview --jsonl-out "/tmp/stream_ttft_gemini-3-flash-preview.jsonl"
.venv/bin/python scripts/stream_concurrency_ttft_probe.py \
  --model gemini-3.1-pro-preview --jsonl-out "/tmp/stream_ttft_gemini-3_1-pro-preview.jsonl"
```

默认 **`--concurrency-list 50,100`**、**`--samples 100`**、**`--stream-timeout 600`**；每模型总调用 **2×100** 次流式，**费用与耗时较高**，请先在低 `samples` 下试跑。

**本次实测（2026-05-08 UTC，主机 `ubuntu@18.183.174.245`，网关 `https://api.mixroute.ai/v1`）**：

- **顺序**：`claude-opus-4-6` → `claude-sonnet-4-6` → `gemini-3-flash-preview` → `gemini-3.1-pro-preview`（各一条命令，**串行**）。
- **总日志**：`/tmp/stream_ttft_master_20260508T074327Z.log`（**ALL_DONE** 时间 **2026-05-08 07:54:31 UTC**）。
- **逐请求 jsonl**（同次时间戳）：`/tmp/stream_ttft_claude-opus-4-6_20260508T074327Z.jsonl`、`…_claude-sonnet-4-6_…`、`…_gemini-3-flash-preview_…`、`…_gemini-3_1-pro-preview_…`（路径在目标机 `/tmp`）。

**汇总表**（`mean_*` / `p50_*` / `p95_*` 仅对 **n_ok** 条成功请求；**wall_s** 为该档 **100** 条全部结束的批次墙钟）：

| 模型 | 并发 | n_ok | n_fail | wall_s | mean_ttft_s | p50_ttft | p95_ttft | mean_total_s | p50_total | p95_total |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| claude-opus-4-6 | 50 | 100 | 0 | 28.8766 | 2.0173 | 1.9027 | 2.5095 | 12.0428 | 12.0952 | 14.0417 |
| claude-opus-4-6 | 100 | 100 | 0 | 14.9484 | 2.1694 | 2.0877 | 2.6490 | 12.3043 | 12.4850 | 14.3570 |
| claude-sonnet-4-6 | 50 | 100 | 0 | 26.9269 | 1.5512 | 1.4956 | 2.1282 | 12.4985 | 12.5229 | 13.5111 |
| claude-sonnet-4-6 | 100 | 100 | 0 | 17.4801 | 1.8052 | 1.7034 | 2.7290 | 12.9543 | 12.9431 | 14.1040 |
| gemini-3-flash-preview | 50 | 100 | 0 | 11.2714 | 4.2751 | 4.1855 | 5.0813 | 4.3300 | 4.2387 | 5.1126 |
| gemini-3-flash-preview | 100 | 100 | 0 | 8.3505 | 5.7178 | 5.5252 | 7.3261 | 5.7666 | 5.5726 | 7.3562 |
| gemini-3.1-pro-preview | 50 | 100 | 0 | 349.7505 | 84.3157 | 79.9727 | 172.5677 | 84.3495 | 79.9737 | 172.5762 |
| gemini-3.1-pro-preview | 100 | 99 | 1 | 197.5230 | 78.8920 | 77.6288 | 142.1588 | 78.9316 | 77.6299 | 142.1665 |

**异常 1 条**：`gemini-3.1-pro-preview`、并发 **100** 档有 **1** 次 **`no_first_token_chunk`**（流结束但未在 chunk 中解析到脚本认定的「首 token」增量），**未计入**上表 `mean_*` / `p*`；详见该档 jsonl 中 `ok=false` 记录。

---

## 7. 总结

- **连通性**：四模型在目标机上 `**/v1/chat/completions`（OpenAI SDK）** 与 `**/v1/messages`（Anthropic SDK）** 均通过。  
- **吞吐 vs RPM**：§5 与 §6 的统计口径不同，勿与 4 月数值直接混比为「变差/变好」的绝对结论。  
- **RPM / TPM 窗口（§6.1）**：在 2026-05-07 双进程 overlap 加压下，进程 A 脚本字段 `**window_60s_requests_started` = 1380**；同锚点合并 A+B 日志后 **60 秒窗口内发起合计 ≈ 2765**。按 §6.1 单次 token 假设，**TPM 粗算中位约 11 万 / 分钟量级**（宽松并列口径约 **55 万**）；均为估算，非账单值。  
- **第二模型（§6.2）**：`claude-sonnet-4-6`（2026-05-08）双进程 overlap：**合并窗口发起 `merged_in_window` = 3429**（B 窗 1718 + A 窗 1711，锚点见 §6.2）；**TPM 粗算**中位约 **16.1 万/分钟**（见 §6.2 表）。  
- **第三、四模型（§6.3–§6.4）**：`claude-opus-4-6` 与 `**gemini-3.1-pro-preview`** 同构双进程加压下**均未出现首次失败**，**无合并锚定 RPM**；仅记录 `**approx_throughput_rpm`** 与 **reference** 窗及**整段墙钟 TPM 粗算**（见各节）。  
- **流式并发延迟（§6.5）**：四模型 **stream**、**50/100** 并发、**heavy 4096 + max_tokens 512** 的 TTFT / 流式总耗时见 **§6.5** 表（**2026-05-08 UTC** 于 **`ubuntu@18.183.174.245`** 跑批；**分四次单模型**执行；`gemini-3.1-pro-preview` 并发 **100** 有 **1** 次无首包解析失败）。  
- **安全**：勿在聊天或文档中粘贴明文 Key；本次用于跑通的 Key 若已暴露，请**轮换**。

---

*本报告主体验证主机为 `ubuntu@54.238.141.156`（2026-05-06）；§6.1–§6.4 为 2026-05-07/08 补充；**§6.5** 流式探针在 **`ubuntu@18.183.174.245`**（2026-05-08 UTC）执行。输出已脱敏整理。*
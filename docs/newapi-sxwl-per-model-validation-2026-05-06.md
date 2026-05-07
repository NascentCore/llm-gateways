# llm.sxwl.ai 逐模型用户侧全量验证报告（生成）
**生成时间（UTC）**：2026-05-06T07:36:14+00:00Z  
**网关 base_url**：`https://llm.sxwl.ai/v1`  
**原始日志目录**：`/tmp/sxwl_per_model_full`（机器本地路径，请随跑随备份）  
**说明**：本文件由 `scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py` 生成；与 `test_channel_models_compat.py`（管理端按渠道探测）口径不同，此处为用户 Key 经网关路由的 OpenAI / Anthropic 兼容路径。

### TPM 估算说明（手工增补，非网关账单）

- **heavy（`rpm_until_limit`，`payload=heavy`）**：与 mixroute 技术验证文档口径一致，假设单次请求规模约 **10 000（tiktoken 正文目标）+ 1 000（`max_tokens` 上限）= 11 000 token/次**，则  
  **TPM（heavy，估算）≈ `approx_throughput_rpm` × 11 000**。  
  真实计费以网关返回的 `usage` 为准；若本段 run 内出现部分 429，`approx_throughput_rpm` 仍为脚本按「成功次数 ÷ 整段墙钟秒数 × 60」换算，上式为**同一假设下的粗算**。

- **minute（`rpm_minute_window_probe`，`payload=minimal`，默认 `max_tokens=64`）**：单次请求 token 远低于 heavy，此处取 **约 200 token/次** 作量级粗算（非精确计费）：  
  **TPM（minute，估算）≈ `approx_throughput_rpm` × 200**。  
  与 heavy 的 TPM **不可横向对比**；若 `approx_throughput_rpm=0`（如首轮即全失败），下表 minute TPM 记为 **0**。

---
## 汇总表
| 模型 | OpenAI chat | Anthropic msg | usage (p/c/t/墙钟s) | heavy summary | minute summary |
|------|-------------|---------------|---------------------|---------------|----------------|
| `glm-5.1` | OK | OK | `model=glm-5.1	prompt_tokens=13	completion_tokens=512	total_…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `ail round=1 conc=256 i=204 t_start=1778053192.307…` |
| `glm-5` | OK | OK | `model=glm-5	prompt_tokens=13	completion_tokens=456	total_to…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `': 'upstream_error', 'param': '', 'code': '1302'}…` |
| `hunyuan-pro` | FAIL (1) | 跳过 | `—` | `—` | `—` |
| `hunyuan-standard` | FAIL (1) | 跳过 | `—` | `—` | `—` |
| `MiniMax-M2.7` | OK | OK | `model=MiniMax-M2.7	prompt_tokens=48	completion_tokens=57	to…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `778053610.691654 t_end=1778053612.981508 latency_…` |
| `MiniMax-M2.5` | OK | OK | `model=MiniMax-M2.5	prompt_tokens=48	completion_tokens=74	to…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `778053814.227874 t_end=1778053817.274310 latency_…` |
| `kimi-k2.6` | OK | OK | `model=kimi-k2.6	prompt_tokens=15	completion_tokens=124	tota…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `8054442.489213 t_end=1778054447.962801 latency_s=…` |
| `kimi-k2.5` | OK | OK | `model=kimi-k2.5	prompt_tokens=15	completion_tokens=253	tota…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `rloaded, please try again later', 'type': 'engine…` |
| `step-3.5-flash-2603` | OK | OK | `model=step-3.5-flash-2603	prompt_tokens=20	completion_token…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `y_s=5.9835 status=429 msg=Error code: 429 - {'err…` |
| `step-3.5-flash` | OK | OK | `model=step-3.5-flash	prompt_tokens=20	completion_tokens=172…` | `rpm_until_limit payload=heavy base_url=https://ll…` | `om/***/***/***/***', 'type': 'rate_limited', 'par…` |

---

## RPM / TPM 估算汇总

数值取自各模型小节内 **`--- summary ---`** 的 `approx_throughput_rpm`；TPM 按上一节公式计算（取整）。

| 模型 | heavy RPM | heavy TPM（估） | minute RPM | minute TPM（估） |
|------|-----------|-----------------|------------|------------------|
| `glm-5.1` | 8.31 | 91 410（≈9.14 万） | 126.01 | 25 202（≈2.52 万） |
| `glm-5` | 3.05 | 33 550（≈3.36 万） | 34.35 | 6 870（≈0.69 万） |
| `hunyuan-pro` | — | — | — | — |
| `hunyuan-standard` | — | — | — | — |
| `MiniMax-M2.7` | 13.46 | 148 060（≈14.81 万） | 2492.51 | 498 502（≈49.85 万） |
| `MiniMax-M2.5` | 19.66 | 216 260（≈21.63 万） | 2677.01 | 535 402（≈53.54 万） |
| `kimi-k2.6` | 4.21 | 46 310（≈4.63 万） | 1554.95 | 310 990（≈31.10 万） |
| `kimi-k2.5` | 6.55 | 72 050（≈7.21 万） | 0.00 | 0 |
| `step-3.5-flash-2603` | 22.69 | 249 590（≈24.96 万） | 48.29 | 9 658（≈0.97 万） |
| `step-3.5-flash` | 11.80 | 129 800（≈12.98 万） | 100.69 | 20 138（≈2.01 万） |

---
## `glm-5.1`（slug=`glm-5.1`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5.1/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['glm-5.1'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=glm-5.1
  [glm-5.1] OK (15.59s): (空回复)
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5.1/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['glm-5.1'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=glm-5.1
  [glm-5.1] OK (2.16s): 我是一个旨在为你提供信息、解答问题和激发灵感的人工智能助手。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5.1/usage.log`

```
model=glm-5.1	prompt_tokens=13	completion_tokens=512	total_tokens=525	wall_s=14.62
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5.1/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=glm-5.1 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=27.6998
ok round=2 conc=2 i=2 latency_s=29.5466
ok round=2 conc=2 i=3 latency_s=29.9053
ok round=3 conc=4 i=4 latency_s=39.7291
ok round=3 conc=4 i=5 latency_s=42.7210
ok round=3 conc=4 i=6 latency_s=39.7281
ok round=3 conc=4 i=7 latency_s=41.0320
ok round=4 conc=8 i=8 latency_s=39.0552
ok round=4 conc=8 i=9 latency_s=38.4587
ok round=4 conc=8 i=10 latency_s=35.9278
ok round=4 conc=8 i=11 latency_s=37.7051
ok round=4 conc=8 i=12 latency_s=39.3892
ok round=4 conc=8 i=13 latency_s=35.1226
ok round=4 conc=8 i=14 latency_s=37.3767
ok round=4 conc=8 i=15 latency_s=36.4536
ok round=5 conc=16 i=16 latency_s=40.8155
ok round=5 conc=16 i=17 latency_s=38.1612
fail round=5 conc=16 i=18 latency_s=2.6174 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=5 conc=16 i=19 latency_s=38.1220
ok round=5 conc=16 i=20 latency_s=37.4567
fail round=5 conc=16 i=21 latency_s=2.4701 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=5 conc=16 i=22 latency_s=39.2596
ok round=5 conc=16 i=23 latency_s=38.7382
fail round=5 conc=16 i=24 latency_s=2.2773 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=5 conc=16 i=25 latency_s=2.2184 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=5 conc=16 i=26 latency_s=37.9508
ok round=5 conc=16 i=27 latency_s=38.1072
ok round=5 conc=16 i=28 latency_s=38.1495
ok round=5 conc=16 i=29 latency_s=38.5160
fail round=5 conc=16 i=30 latency_s=2.3685 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=5 conc=16 i=31 latency_s=2.3156 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
--- summary ---
stop_reason=429
successful_requests=25
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=180.5390
approx_throughput_rpm=8.31
latency_s min=27.6998 p50=38.1495 max=42.7210
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5.1/rpm_minute.log`

```
ail round=1 conc=256 i=204 t_start=1778053192.307143 t_end=1778053197.114732 latency_s=4.8076 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=205 t_start=1778053192.307384 t_end=1778053198.270768 latency_s=5.9634 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=206 t_start=1778053192.307640 t_end=1778053197.682534 latency_s=5.3749 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=207 t_start=1778053192.307898 t_end=1778053197.069999 latency_s=4.7621 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=208 t_start=1778053192.308199 t_end=1778053197.980077 latency_s=5.6719 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=209 t_start=1778053192.308450 t_end=1778053199.149449 latency_s=6.8410 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=210 t_start=1778053192.308712 t_end=1778053196.941697 latency_s=4.6330 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=1 conc=256 i=211 t_start=1778053192.308969 t_end=1778053199.133663 latency_s=6.8247
fail round=1 conc=256 i=212 t_start=1778053192.309211 t_end=1778053199.374766 latency_s=7.0656 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=213 t_start=1778053192.309463 t_end=1778053197.331277 latency_s=5.0218 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=214 t_start=1778053192.309722 t_end=1778053199.444735 latency_s=7.1350 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=215 t_start=1778053192.309981 t_end=1778053197.519311 latency_s=5.2093 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=216 t_start=1778053192.310223 t_end=1778053196.385992 latency_s=4.0758 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=1 conc=256 i=217 t_start=1778053192.310586 t_end=1778053199.044649 latency_s=6.7341
fail round=1 conc=256 i=218 t_start=1778053192.310884 t_end=1778053198.149845 latency_s=5.8390 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=219 t_start=1778053192.311191 t_end=1778053198.935224 latency_s=6.6240 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=220 t_start=1778053192.311439 t_end=1778053198.538145 latency_s=6.2267 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=221 t_start=1778053192.311695 t_end=1778053195.845862 latency_s=3.5342 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=222 t_start=1778053192.311953 t_end=1778053196.797874 latency_s=4.4859 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=223 t_start=1778053192.312202 t_end=1778053198.848644 latency_s=6.5364 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=224 t_start=1778053192.312463 t_end=1778053198.702553 latency_s=6.3901 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=225 t_start=1778053192.312718 t_end=1778053196.026782 latency_s=3.7141 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=226 t_start=1778053192.312976 t_end=1778053197.982811 latency_s=5.6698 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=227 t_start=1778053192.313231 t_end=1778053198.997437 latency_s=6.6842 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=228 t_start=1778053192.313475 t_end=1778053199.081777 latency_s=6.7683 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=229 t_start=1778053192.313733 t_end=1778053197.292065 latency_s=4.9783 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=230 t_start=1778053192.314026 t_end=1778053197.136179 latency_s=4.8222 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=231 t_start=1778053192.314280 t_end=1778053198.442447 latency_s=6.1282 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=232 t_start=1778053192.314533 t_end=1778053196.629067 latency_s=4.3145 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=233 t_start=1778053192.314788 t_end=1778053198.651721 latency_s=6.3369 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=234 t_start=1778053192.315044 t_end=1778053196.627692 latency_s=4.3126 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=235 t_start=1778053192.315286 t_end=1778053196.903551 latency_s=4.5883 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=236 t_start=1778053192.315532 t_end=1778053198.231721 latency_s=5.9162 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=237 t_start=1778053192.315922 t_end=1778053199.379246 latency_s=7.0633 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=238 t_start=1778053192.316164 t_end=1778053197.578143 latency_s=5.2620 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=239 t_start=1778053192.316413 t_end=1778053197.609001 latency_s=5.2926 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=1 conc=256 i=240 t_start=1778053192.316677 t_end=1778053200.571712 latency_s=8.2550
fail round=1 conc=256 i=241 t_start=1778053192.316969 t_end=1778053198.807339 latency_s=6.4904 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=242 t_start=1778053192.317218 t_end=1778053197.031668 latency_s=4.7145 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=243 t_start=1778053192.317468 t_end=1778053198.924414 latency_s=6.6069 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=244 t_start=1778053192.317729 t_end=1778053198.936612 latency_s=6.6189 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=1 conc=256 i=245 t_start=1778053192.317987 t_end=1778053202.507107 latency_s=10.1891
fail round=1 conc=256 i=246 t_start=1778053192.318234 t_end=1778053198.272163 latency_s=5.9539 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=247 t_start=1778053192.318476 t_end=1778053197.206881 latency_s=4.8884 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=248 t_start=1778053192.318736 t_end=1778053197.626151 latency_s=5.3074 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=249 t_start=1778053192.319001 t_end=1778053199.393246 latency_s=7.0742 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=250 t_start=1778053192.319247 t_end=1778053197.779295 latency_s=5.4600 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=251 t_start=1778053192.319491 t_end=1778053199.264967 latency_s=6.9455 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=252 t_start=1778053192.319746 t_end=1778053199.377951 latency_s=7.0582 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=253 t_start=1778053192.320046 t_end=1778053198.808770 latency_s=6.4887 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=254 t_start=1778053192.320288 t_end=1778053196.877994 latency_s=4.5577 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=255 t_start=1778053192.320537 t_end=1778053197.167043 latency_s=4.8465 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=256 t_start=1778053192.320921 t_end=1778053197.480681 latency_s=5.1598 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
--- summary ---
stop_reason=429
successful_requests=30
total_attempts=256
rounds_run=1
peak_concurrency=256
total_wall_s=14.2849
approx_throughput_rpm=126.01
first_failure_i=2 anchor_t_start=1778053192.246687 window_60s_requests_started=2
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
latency_s min=2.8389 p50=6.2182 max=14.1047
```

## `glm-5`（slug=`glm-5`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['glm-5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=glm-5
  [glm-5] OK (6.64s): 我是人工智能助手，随时为你解答问题、提供各类信息和帮助。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['glm-5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=glm-5
  [glm-5] OK (3.66s): 我是由Z.ai训练的GLM大语言模型，能够为您提供专业、准确的知识解答与建议，助力您的工作与学习。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5/usage.log`

```
model=glm-5	prompt_tokens=13	completion_tokens=456	total_tokens=469	wall_s=10.69
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=glm-5 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=29.4120
ok round=2 conc=2 i=2 latency_s=46.9663
ok round=2 conc=2 i=3 latency_s=39.8363
ok round=3 conc=4 i=4 latency_s=41.7815
ok round=3 conc=4 i=5 latency_s=30.8439
fail round=3 conc=4 i=6 latency_s=2.1073 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=3 conc=4 i=7 latency_s=39.7788
--- summary ---
stop_reason=429
successful_requests=6
total_attempts=7
rounds_run=3
peak_concurrency=4
total_wall_s=118.1607
approx_throughput_rpm=3.05
latency_s min=29.4120 p50=39.8075 max=46.9663
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/glm-5/rpm_minute.log`

```
': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=206 t_start=1778053348.525424 t_end=1778053355.841936 latency_s=7.3165 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=207 t_start=1778053348.525737 t_end=1778053356.699102 latency_s=8.1734 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=208 t_start=1778053348.526052 t_end=1778053357.683619 latency_s=9.1576 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=209 t_start=1778053348.526299 t_end=1778053356.177342 latency_s=7.6510 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=210 t_start=1778053348.526546 t_end=1778053354.657137 latency_s=6.1306 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=211 t_start=1778053348.526807 t_end=1778053356.489165 latency_s=7.9624 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=212 t_start=1778053348.527050 t_end=1778053352.081657 latency_s=3.5546 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=213 t_start=1778053348.527295 t_end=1778053354.331286 latency_s=5.8040 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=214 t_start=1778053348.527544 t_end=1778053355.161103 latency_s=6.6336 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=215 t_start=1778053348.527812 t_end=1778053356.402025 latency_s=7.8742 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=216 t_start=1778053348.528057 t_end=1778053354.258709 latency_s=5.7307 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=217 t_start=1778053348.528299 t_end=1778053354.579614 latency_s=6.0513 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=218 t_start=1778053348.528538 t_end=1778053353.261117 latency_s=4.7326 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=219 t_start=1778053348.528845 t_end=1778053354.673466 latency_s=6.1446 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=220 t_start=1778053348.529254 t_end=1778053353.366702 latency_s=4.8374 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=221 t_start=1778053348.529511 t_end=1778053353.579308 latency_s=5.0498 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=222 t_start=1778053348.529783 t_end=1778053353.562994 latency_s=5.0332 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=223 t_start=1778053348.530045 t_end=1778053354.008308 latency_s=5.4783 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=224 t_start=1778053348.530302 t_end=1778053356.596104 latency_s=8.0658 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=225 t_start=1778053348.530542 t_end=1778053355.025712 latency_s=6.4952 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=226 t_start=1778053348.530810 t_end=1778053352.754835 latency_s=4.2240 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=227 t_start=1778053348.531059 t_end=1778053355.477368 latency_s=6.9463 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=228 t_start=1778053348.531301 t_end=1778053356.687473 latency_s=8.1562 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=229 t_start=1778053348.531545 t_end=1778053355.857332 latency_s=7.3258 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=230 t_start=1778053348.531851 t_end=1778053356.163531 latency_s=7.6317 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=231 t_start=1778053348.532107 t_end=1778053356.649476 latency_s=8.1174 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=232 t_start=1778053348.532371 t_end=1778053356.650790 latency_s=8.1184 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=233 t_start=1778053348.532629 t_end=1778053356.278433 latency_s=7.7458 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=234 t_start=1778053348.532887 t_end=1778053353.324910 latency_s=4.7920 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=235 t_start=1778053348.533129 t_end=1778053353.557741 latency_s=5.0246 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=236 t_start=1778053348.533377 t_end=1778053354.030883 latency_s=5.4975 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=237 t_start=1778053348.533627 t_end=1778053354.678164 latency_s=6.1445 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=238 t_start=1778053348.533883 t_end=1778053356.328825 latency_s=7.7949 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=239 t_start=1778053348.534582 t_end=1778053352.852069 latency_s=4.3175 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=240 t_start=1778053348.534890 t_end=1778053356.522853 latency_s=7.9880 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=241 t_start=1778053348.535191 t_end=1778053354.955041 latency_s=6.4199 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=242 t_start=1778053348.535436 t_end=1778053355.736490 latency_s=7.2011 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=243 t_start=1778053348.535707 t_end=1778053354.805271 latency_s=6.2696 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=244 t_start=1778053348.535969 t_end=1778053353.873530 latency_s=5.3376 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=245 t_start=1778053348.536212 t_end=1778053356.684805 latency_s=8.1486 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=246 t_start=1778053348.536450 t_end=1778053354.581115 latency_s=6.0447 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=247 t_start=1778053348.536720 t_end=1778053356.380619 latency_s=7.8439 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=248 t_start=1778053348.536979 t_end=1778053357.553194 latency_s=9.0162 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=249 t_start=1778053348.537231 t_end=1778053353.087099 latency_s=4.5499 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=250 t_start=1778053348.537485 t_end=1778053356.335233 latency_s=7.7977 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=251 t_start=1778053348.537745 t_end=1778053356.441550 latency_s=7.9038 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=252 t_start=1778053348.538040 t_end=1778053356.453870 latency_s=7.9158 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=253 t_start=1778053348.538289 t_end=1778053354.817903 latency_s=6.2796 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
fail round=1 conc=256 i=254 t_start=1778053348.538532 t_end=1778053354.992657 latency_s=6.4541 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
ok round=1 conc=256 i=255 t_start=1778053348.538802 t_end=1778053356.970123 latency_s=8.4313
fail round=1 conc=256 i=256 t_start=1778053348.539070 t_end=1778053353.969654 latency_s=5.4306 status=429 msg=Error code: 429 - {'error': {'message': '您的账户已达到速率限制，请您控制请求频率', 'type': 'upstream_error', 'param': '', 'code': '1302'}}
--- summary ---
stop_reason=429
successful_requests=8
total_attempts=256
rounds_run=1
peak_concurrency=256
total_wall_s=13.9752
approx_throughput_rpm=34.35
first_failure_i=1 anchor_t_start=1778053348.330859 window_60s_requests_started=1
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
latency_s min=3.2836 p50=7.3059 max=13.8096
```

## `hunyuan-pro`（slug=`hunyuan-pro`）
### test_chat OpenAI
- exit_code: `1`
- 完整日志：`/tmp/sxwl_per_model_full/hunyuan-pro/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['hunyuan-pro'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=hunyuan-pro
  [hunyuan-pro] FAIL: Error code: 500 - {'error': {'message': 'json: cannot unmarshal string into Go struct field ***.***.***.Code of type int', 'type': 'bad_response_body', 'param': '', 'code': 'bad_response_body'}}
0/1 passed. Exit 1.
```

### test_chat Anthropic
_跳过：previous step failed_
### Usage 采样
_跳过：previous step failed_
### rpm_until_limit heavy
_跳过：previous step failed_
### rpm_minute_window_probe batch+minimal
_跳过：previous step failed_
## `hunyuan-standard`（slug=`hunyuan-standard`）
### test_chat OpenAI
- exit_code: `1`
- 完整日志：`/tmp/sxwl_per_model_full/hunyuan-standard/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['hunyuan-standard'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=hunyuan-standard
  [hunyuan-standard] FAIL: Error code: 500 - {'error': {'message': 'json: cannot unmarshal string into Go struct field ***.***.***.Code of type int', 'type': 'bad_response_body', 'param': '', 'code': 'bad_response_body'}}
0/1 passed. Exit 1.
```

### test_chat Anthropic
_跳过：previous step failed_
### Usage 采样
_跳过：previous step failed_
### rpm_until_limit heavy
_跳过：previous step failed_
### rpm_minute_window_probe batch+minimal
_跳过：previous step failed_
## `MiniMax-M2.7`（slug=`MiniMax-M2.7`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.7/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['MiniMax-M2.7'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=MiniMax-M2.7
  [MiniMax-M2.7] OK (2.21s): 你好！我是MiniMax-M3.5，一个由MiniMax公司开发的智能AI助手，很高兴为你服务！
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.7/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['MiniMax-M2.7'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=MiniMax-M2.7
  [MiniMax-M2.7] OK (5.78s): 我是一个由MiniMax开发的人工智能助手，旨在为您提供信息、解答疑问并进行友好的对话。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.7/usage.log`

```
model=MiniMax-M2.7	prompt_tokens=48	completion_tokens=57	total_tokens=105	wall_s=2.35
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.7/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=MiniMax-M2.7 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=25.4761
ok round=2 conc=2 i=2 latency_s=19.0057
ok round=2 conc=2 i=3 latency_s=14.6789
ok round=3 conc=4 i=4 latency_s=29.4214
ok round=3 conc=4 i=5 latency_s=20.6202
ok round=3 conc=4 i=6 latency_s=13.1201
ok round=3 conc=4 i=7 latency_s=21.2787
ok round=4 conc=8 i=8 latency_s=19.5640
ok round=4 conc=8 i=9 latency_s=17.2131
ok round=4 conc=8 i=10 latency_s=30.4992
ok round=4 conc=8 i=11 latency_s=19.5044
ok round=4 conc=8 i=12 latency_s=16.0926
ok round=4 conc=8 i=13 latency_s=22.4465
ok round=4 conc=8 i=14 latency_s=23.3406
ok round=4 conc=8 i=15 latency_s=28.8858
ok round=5 conc=16 i=16 latency_s=23.6164
ok round=5 conc=16 i=17 latency_s=19.6986
ok round=5 conc=16 i=18 latency_s=33.7876
ok round=5 conc=16 i=19 latency_s=17.4018
ok round=5 conc=16 i=20 latency_s=30.8836
ok round=5 conc=16 i=21 latency_s=11.6501
ok round=5 conc=16 i=22 latency_s=28.1343
ok round=5 conc=16 i=23 latency_s=30.1635
ok round=5 conc=16 i=24 latency_s=29.8347
ok round=5 conc=16 i=25 latency_s=16.0282
ok round=5 conc=16 i=26 latency_s=17.9477
ok round=5 conc=16 i=27 latency_s=32.4569
ok round=5 conc=16 i=28 latency_s=26.1251
ok round=5 conc=16 i=29 latency_s=14.1238
ok round=5 conc=16 i=30 latency_s=23.2924
ok round=5 conc=16 i=31 latency_s=24.1562
--- summary ---
stop_reason=max_concurrency_no_limit_hit
successful_requests=31
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=138.1957
approx_throughput_rpm=13.46
latency_s min=11.6501 p50=22.4465 max=33.7876
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.7/rpm_minute.log`

```
778053610.691654 t_end=1778053612.981508 latency_s=2.2899
ok round=16 conc=256 i=3975 t_start=1778053610.693751 t_end=1778053612.500825 latency_s=1.8071
ok round=16 conc=256 i=3976 t_start=1778053610.695809 t_end=1778053612.145555 latency_s=1.4497
ok round=16 conc=256 i=3977 t_start=1778053610.697828 t_end=1778053612.961185 latency_s=2.2634
ok round=16 conc=256 i=3978 t_start=1778053610.699872 t_end=1778053612.734005 latency_s=2.0341
ok round=16 conc=256 i=3979 t_start=1778053610.701933 t_end=1778053614.926820 latency_s=4.2249
ok round=16 conc=256 i=3980 t_start=1778053610.703955 t_end=1778053614.844807 latency_s=4.1409
ok round=16 conc=256 i=3981 t_start=1778053610.706059 t_end=1778053612.278392 latency_s=1.5723
ok round=16 conc=256 i=3982 t_start=1778053610.708132 t_end=1778053613.033676 latency_s=2.3255
ok round=16 conc=256 i=3983 t_start=1778053610.710178 t_end=1778053612.727508 latency_s=2.0173
ok round=16 conc=256 i=3984 t_start=1778053610.712206 t_end=1778053612.144596 latency_s=1.4324
ok round=16 conc=256 i=3985 t_start=1778053610.714278 t_end=1778053612.133869 latency_s=1.4196
ok round=16 conc=256 i=3986 t_start=1778053610.716330 t_end=1778053612.898883 latency_s=2.1826
ok round=16 conc=256 i=3987 t_start=1778053610.718406 t_end=1778053612.930738 latency_s=2.2123
ok round=16 conc=256 i=3988 t_start=1778053610.720503 t_end=1778053612.826512 latency_s=2.1060
ok round=16 conc=256 i=3989 t_start=1778053610.722535 t_end=1778053612.948680 latency_s=2.2261
ok round=16 conc=256 i=3990 t_start=1778053610.724558 t_end=1778053612.947967 latency_s=2.2234
ok round=16 conc=256 i=3991 t_start=1778053610.726588 t_end=1778053612.208130 latency_s=1.4815
ok round=16 conc=256 i=3992 t_start=1778053610.728636 t_end=1778053613.086927 latency_s=2.3583
ok round=16 conc=256 i=3993 t_start=1778053610.730657 t_end=1778053613.201582 latency_s=2.4709
ok round=16 conc=256 i=3994 t_start=1778053610.732868 t_end=1778053612.740768 latency_s=2.0079
ok round=16 conc=256 i=3995 t_start=1778053610.734948 t_end=1778053612.222229 latency_s=1.4873
ok round=16 conc=256 i=3996 t_start=1778053610.736998 t_end=1778053612.728184 latency_s=1.9912
ok round=16 conc=256 i=3997 t_start=1778053610.739057 t_end=1778053612.527623 latency_s=1.7886
ok round=16 conc=256 i=3998 t_start=1778053610.741093 t_end=1778053612.250959 latency_s=1.5099
ok round=16 conc=256 i=3999 t_start=1778053610.743109 t_end=1778053613.089957 latency_s=2.3468
ok round=16 conc=256 i=4000 t_start=1778053610.746164 t_end=1778053612.528191 latency_s=1.7820
ok round=16 conc=256 i=4001 t_start=1778053610.748289 t_end=1778053612.300212 latency_s=1.5519
ok round=16 conc=256 i=4002 t_start=1778053610.750344 t_end=1778053612.958949 latency_s=2.2086
ok round=16 conc=256 i=4003 t_start=1778053610.752484 t_end=1778053612.974312 latency_s=2.2218
ok round=16 conc=256 i=4004 t_start=1778053610.754578 t_end=1778053612.955782 latency_s=2.2012
ok round=16 conc=256 i=4005 t_start=1778053610.756610 t_end=1778053613.079399 latency_s=2.3228
ok round=16 conc=256 i=4006 t_start=1778053610.758747 t_end=1778053613.006080 latency_s=2.2473
ok round=16 conc=256 i=4007 t_start=1778053610.760825 t_end=1778053612.727687 latency_s=1.9669
ok round=16 conc=256 i=4008 t_start=1778053610.762847 t_end=1778053615.497934 latency_s=4.7351
ok round=16 conc=256 i=4009 t_start=1778053610.764866 t_end=1778053612.832007 latency_s=2.0671
ok round=16 conc=256 i=4010 t_start=1778053610.766924 t_end=1778053613.017107 latency_s=2.2502
ok round=16 conc=256 i=4011 t_start=1778053610.768967 t_end=1778053614.630535 latency_s=3.8616
ok round=16 conc=256 i=4012 t_start=1778053610.771160 t_end=1778053612.912272 latency_s=2.1411
ok round=16 conc=256 i=4013 t_start=1778053610.773327 t_end=1778053613.028851 latency_s=2.2555
ok round=16 conc=256 i=4014 t_start=1778053610.775371 t_end=1778053612.384920 latency_s=1.6095
ok round=16 conc=256 i=4015 t_start=1778053610.777421 t_end=1778053612.734238 latency_s=1.9568
ok round=16 conc=256 i=4016 t_start=1778053610.779437 t_end=1778053612.774701 latency_s=1.9953
ok round=16 conc=256 i=4017 t_start=1778053610.781558 t_end=1778053613.131721 latency_s=2.3502
ok round=16 conc=256 i=4018 t_start=1778053610.783620 t_end=1778053613.038999 latency_s=2.2554
ok round=16 conc=256 i=4019 t_start=1778053610.785783 t_end=1778053612.855692 latency_s=2.0699
ok round=16 conc=256 i=4020 t_start=1778053610.787864 t_end=1778053612.899888 latency_s=2.1120
ok round=16 conc=256 i=4021 t_start=1778053610.789951 t_end=1778053612.733763 latency_s=1.9438
ok round=16 conc=256 i=4022 t_start=1778053610.792088 t_end=1778053612.826811 latency_s=2.0347
ok round=16 conc=256 i=4023 t_start=1778053610.794184 t_end=1778053612.563889 latency_s=1.7697
ok round=16 conc=256 i=4024 t_start=1778053610.796235 t_end=1778053612.727387 latency_s=1.9312
ok round=16 conc=256 i=4025 t_start=1778053610.798324 t_end=1778053612.942208 latency_s=2.1439
ok round=16 conc=256 i=4026 t_start=1778053610.800512 t_end=1778053612.527442 latency_s=1.7269
ok round=16 conc=256 i=4027 t_start=1778053610.802585 t_end=1778053614.088871 latency_s=3.2863
ok round=16 conc=256 i=4028 t_start=1778053610.804608 t_end=1778053612.962949 latency_s=2.1585
ok round=16 conc=256 i=4029 t_start=1778053610.806633 t_end=1778053612.527939 latency_s=1.7213
ok round=16 conc=256 i=4030 t_start=1778053610.808673 t_end=1778053612.990966 latency_s=2.1823
ok round=16 conc=256 i=4031 t_start=1778053610.810684 t_end=1778053612.912468 latency_s=2.1018
ok round=16 conc=256 i=4032 t_start=1778053610.812802 t_end=1778053613.118805 latency_s=2.3060
ok round=16 conc=256 i=4033 t_start=1778053610.814880 t_end=1778053612.983218 latency_s=2.1683
ok round=16 conc=256 i=4034 t_start=1778053610.816918 t_end=1778053613.088953 latency_s=2.2720
ok round=16 conc=256 i=4035 t_start=1778053610.818984 t_end=1778053612.942019 latency_s=2.1230
ok round=16 conc=256 i=4036 t_start=1778053610.821013 t_end=1778053613.169799 latency_s=2.3488
ok round=16 conc=256 i=4037 t_start=1778053610.823042 t_end=1778053612.956991 latency_s=2.1339
ok round=16 conc=256 i=4038 t_start=1778053610.825091 t_end=1778053612.958546 latency_s=2.1335
ok round=16 conc=256 i=4039 t_start=1778053610.827232 t_end=1778053612.727053 latency_s=1.8998
ok round=16 conc=256 i=4040 t_start=1778053610.829280 t_end=1778053612.929027 latency_s=2.0997
ok round=16 conc=256 i=4041 t_start=1778053610.831320 t_end=1778053612.995752 latency_s=2.1644
ok round=16 conc=256 i=4042 t_start=1778053610.833366 t_end=1778053612.982980 latency_s=2.1496
ok round=16 conc=256 i=4043 t_start=1778053610.835401 t_end=1778053612.994664 latency_s=2.1593
ok round=16 conc=256 i=4044 t_start=1778053610.837461 t_end=1778053612.728924 latency_s=1.8915
ok round=16 conc=256 i=4045 t_start=1778053610.839594 t_end=1778053612.774427 latency_s=1.9348
ok round=16 conc=256 i=4046 t_start=1778053610.841679 t_end=1778053612.933684 latency_s=2.0920
ok round=16 conc=256 i=4047 t_start=1778053610.843723 t_end=1778053612.929244 latency_s=2.0855
ok round=16 conc=256 i=4048 t_start=1778053610.845760 t_end=1778053612.948451 latency_s=2.1027
ok round=16 conc=256 i=4049 t_start=1778053610.847827 t_end=1778053612.912678 latency_s=2.0649
ok round=16 conc=256 i=4050 t_start=1778053610.849854 t_end=1778053612.956738 latency_s=2.1069
ok round=16 conc=256 i=4051 t_start=1778053610.851871 t_end=1778053612.959452 latency_s=2.1076
ok round=16 conc=256 i=4052 t_start=1778053610.854104 t_end=1778053613.010009 latency_s=2.1559
ok round=16 conc=256 i=4053 t_start=1778053610.856226 t_end=1778053612.981245 latency_s=2.1250
ok round=16 conc=256 i=4054 t_start=1778053610.858289 t_end=1778053613.053459 latency_s=2.1952
ok round=16 conc=256 i=4055 t_start=1778053610.860366 t_end=1778053613.039882 latency_s=2.1795
ok round=16 conc=256 i=4056 t_start=1778053610.862457 t_end=1778053613.146066 latency_s=2.2836
ok round=16 conc=256 i=4057 t_start=1778053610.864481 t_end=1778053613.078424 latency_s=2.2139
ok round=16 conc=256 i=4058 t_start=1778053610.866537 t_end=1778053613.031765 latency_s=2.1652
ok round=16 conc=256 i=4059 t_start=1778053610.868708 t_end=1778053613.116445 latency_s=2.2477
ok round=16 conc=256 i=4060 t_start=1778053610.870765 t_end=1778053613.039157 latency_s=2.1684
ok round=16 conc=256 i=4061 t_start=1778053610.872822 t_end=1778053613.008119 latency_s=2.1353
ok round=16 conc=256 i=4062 t_start=1778053610.874837 t_end=1778053612.974919 latency_s=2.1001
ok round=16 conc=256 i=4063 t_start=1778053610.876881 t_end=1778053612.985772 latency_s=2.1089
ok round=16 conc=256 i=4064 t_start=1778053610.878937 t_end=1778053613.101510 latency_s=2.2226
ok round=16 conc=256 i=4065 t_start=1778053610.881077 t_end=1778053613.066617 latency_s=2.1855
ok round=16 conc=256 i=4066 t_start=1778053610.883150 t_end=1778053613.127115 latency_s=2.2440
ok round=16 conc=256 i=4067 t_start=1778053610.885157 t_end=1778053613.085124 latency_s=2.2000
ok round=16 conc=256 i=4068 t_start=1778053610.887181 t_end=1778053615.196158 latency_s=4.3090
ok round=16 conc=256 i=4069 t_start=1778053610.889221 t_end=1778053613.061367 latency_s=2.1721
ok round=16 conc=256 i=4070 t_start=1778053610.891247 t_end=1778053613.149828 latency_s=2.2586
ok round=16 conc=256 i=4071 t_start=1778053610.893247 t_end=1778053613.172375 latency_s=2.2791
ok round=16 conc=256 i=4072 t_start=1778053610.895409 t_end=1778053613.206864 latency_s=2.3115
ok round=16 conc=256 i=4073 t_start=1778053610.897442 t_end=1778053613.179408 latency_s=2.2820
ok round=16 conc=256 i=4074 t_start=1778053610.899558 t_end=1778053613.143418 latency_s=2.2439
ok round=16 conc=256 i=4075 t_start=1778053610.901614 t_end=1778053613.182041 latency_s=2.2804
ok round=16 conc=256 i=4076 t_start=1778053610.903633 t_end=1778053613.203998 latency_s=2.3004
ok round=16 conc=256 i=4077 t_start=1778053610.905647 t_end=1778053613.122269 latency_s=2.2166
ok round=16 conc=256 i=4078 t_start=1778053610.908590 t_end=1778053613.142286 latency_s=2.2337
ok round=16 conc=256 i=4079 t_start=1778053610.910711 t_end=1778053613.191022 latency_s=2.2803
ok round=16 conc=256 i=4080 t_start=1778053610.912786 t_end=1778053613.191936 latency_s=2.2791
ok round=16 conc=256 i=4081 t_start=1778053610.914814 t_end=1778053613.171168 latency_s=2.2564
ok round=16 conc=256 i=4082 t_start=1778053610.916869 t_end=1778053613.205425 latency_s=2.2886
ok round=16 conc=256 i=4083 t_start=1778053610.918908 t_end=1778053613.136360 latency_s=2.2175
ok round=16 conc=256 i=4084 t_start=1778053610.920931 t_end=1778053613.167104 latency_s=2.2462
ok round=16 conc=256 i=4085 t_start=1778053610.923095 t_end=1778053613.147479 latency_s=2.2244
ok round=16 conc=256 i=4086 t_start=1778053610.925171 t_end=1778053613.178123 latency_s=2.2530
ok round=16 conc=256 i=4087 t_start=1778053610.927202 t_end=1778053613.153486 latency_s=2.2263
ok round=16 conc=256 i=4088 t_start=1778053610.929327 t_end=1778053613.190057 latency_s=2.2607
ok round=16 conc=256 i=4089 t_start=1778053610.931389 t_end=1778053613.149199 latency_s=2.2178
ok round=16 conc=256 i=4090 t_start=1778053610.933433 t_end=1778053613.183118 latency_s=2.2497
ok round=16 conc=256 i=4091 t_start=1778053610.935564 t_end=1778053613.183996 latency_s=2.2484
ok round=16 conc=256 i=4092 t_start=1778053610.937644 t_end=1778053613.193264 latency_s=2.2556
ok round=16 conc=256 i=4093 t_start=1778053610.939712 t_end=1778053616.164281 latency_s=5.2246
ok round=16 conc=256 i=4094 t_start=1778053610.941753 t_end=1778053613.180693 latency_s=2.2389
ok round=16 conc=256 i=4095 t_start=1778053610.943801 t_end=1778053613.186120 latency_s=2.2423
ok round=16 conc=256 i=4096 t_start=1778053610.945855 t_end=1778053613.216169 latency_s=2.2703
--- summary ---
stop_reason=max_requests
successful_requests=4096
total_attempts=4096
rounds_run=16
peak_concurrency=256
total_wall_s=98.5995
approx_throughput_rpm=2492.51
reference_only_last_start_t=1778053610.945855 window_60s_requests_started=2816 (no API failure; stop=max_requests; not a rate-limit RPM)
latency_s min=0.5511 p50=2.1575 max=8.8760
```

## `MiniMax-M2.5`（slug=`MiniMax-M2.5`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.5/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['MiniMax-M2.5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=MiniMax-M2.5
  [MiniMax-M2.5] OK (9.04s): 你好！我是一个AI助手，可以帮助你回答问题、提供信息和完成各种文字任务。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.5/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['MiniMax-M2.5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=MiniMax-M2.5
  [MiniMax-M2.5] OK (1.80s): 你好！我是 MiniMax-M2.5，由 MiniMax 公司开发的 AI 助手，可以帮助你回答问题、提供信息和进行各种文字交流。有什么我可以帮助你的吗？
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.5/usage.log`

```
model=MiniMax-M2.5	prompt_tokens=48	completion_tokens=74	total_tokens=122	wall_s=3.26
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.5/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=MiniMax-M2.5 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=17.5220
ok round=2 conc=2 i=2 latency_s=13.1572
ok round=2 conc=2 i=3 latency_s=14.5179
ok round=3 conc=4 i=4 latency_s=8.9268
ok round=3 conc=4 i=5 latency_s=17.8804
ok round=3 conc=4 i=6 latency_s=11.4105
ok round=3 conc=4 i=7 latency_s=19.5836
ok round=4 conc=8 i=8 latency_s=21.7003
ok round=4 conc=8 i=9 latency_s=21.7476
ok round=4 conc=8 i=10 latency_s=19.4881
ok round=4 conc=8 i=11 latency_s=14.5289
ok round=4 conc=8 i=12 latency_s=14.2536
ok round=4 conc=8 i=13 latency_s=20.1040
ok round=4 conc=8 i=14 latency_s=22.0231
ok round=4 conc=8 i=15 latency_s=15.7172
ok round=5 conc=16 i=16 latency_s=13.3491
ok round=5 conc=16 i=17 latency_s=19.7939
ok round=5 conc=16 i=18 latency_s=16.4945
ok round=5 conc=16 i=19 latency_s=20.9464
ok round=5 conc=16 i=20 latency_s=16.2254
ok round=5 conc=16 i=21 latency_s=14.2335
ok round=5 conc=16 i=22 latency_s=14.4957
ok round=5 conc=16 i=23 latency_s=10.6666
ok round=5 conc=16 i=24 latency_s=12.1503
ok round=5 conc=16 i=25 latency_s=20.7072
ok round=5 conc=16 i=26 latency_s=13.4863
ok round=5 conc=16 i=27 latency_s=10.5383
ok round=5 conc=16 i=28 latency_s=12.0448
ok round=5 conc=16 i=29 latency_s=12.8561
ok round=5 conc=16 i=30 latency_s=20.3394
ok round=5 conc=16 i=31 latency_s=13.6761
--- summary ---
stop_reason=max_concurrency_no_limit_hit
successful_requests=31
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=94.6063
approx_throughput_rpm=19.66
latency_s min=8.9268 p50=14.5289 max=22.0231
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/MiniMax-M2.5/rpm_minute.log`

```
778053814.227874 t_end=1778053817.274310 latency_s=3.0464
ok round=16 conc=256 i=3975 t_start=1778053814.229939 t_end=1778053817.178528 latency_s=2.9486
ok round=16 conc=256 i=3976 t_start=1778053814.232152 t_end=1778053817.393485 latency_s=3.1613
ok round=16 conc=256 i=3977 t_start=1778053814.234238 t_end=1778053817.400022 latency_s=3.1658
ok round=16 conc=256 i=3978 t_start=1778053814.236330 t_end=1778053816.533009 latency_s=2.2967
ok round=16 conc=256 i=3979 t_start=1778053814.238394 t_end=1778053819.666375 latency_s=5.4280
ok round=16 conc=256 i=3980 t_start=1778053814.240494 t_end=1778053816.891644 latency_s=2.6512
ok round=16 conc=256 i=3981 t_start=1778053814.242751 t_end=1778053817.179399 latency_s=2.9366
ok round=16 conc=256 i=3982 t_start=1778053814.244961 t_end=1778053817.569016 latency_s=3.3241
ok round=16 conc=256 i=3983 t_start=1778053814.247082 t_end=1778053815.799446 latency_s=1.5524
ok round=16 conc=256 i=3984 t_start=1778053814.249211 t_end=1778053816.348441 latency_s=2.0992
ok round=16 conc=256 i=3985 t_start=1778053814.251329 t_end=1778053817.593192 latency_s=3.3419
ok round=16 conc=256 i=3986 t_start=1778053814.253434 t_end=1778053816.099346 latency_s=1.8459
ok round=16 conc=256 i=3987 t_start=1778053814.255503 t_end=1778053817.613659 latency_s=3.3582
ok round=16 conc=256 i=3988 t_start=1778053814.257550 t_end=1778053816.904631 latency_s=2.6471
ok round=16 conc=256 i=3989 t_start=1778053814.261501 t_end=1778053815.890363 latency_s=1.6289
ok round=16 conc=256 i=3990 t_start=1778053814.263852 t_end=1778053816.598385 latency_s=2.3345
ok round=16 conc=256 i=3991 t_start=1778053814.265999 t_end=1778053817.579119 latency_s=3.3131
ok round=16 conc=256 i=3992 t_start=1778053814.268112 t_end=1778053815.911568 latency_s=1.6435
ok round=16 conc=256 i=3993 t_start=1778053814.270210 t_end=1778053817.599317 latency_s=3.3291
ok round=16 conc=256 i=3994 t_start=1778053814.272279 t_end=1778053817.423299 latency_s=3.1510
ok round=16 conc=256 i=3995 t_start=1778053814.274455 t_end=1778053816.439365 latency_s=2.1649
ok round=16 conc=256 i=3996 t_start=1778053814.276574 t_end=1778053816.575264 latency_s=2.2987
ok round=16 conc=256 i=3997 t_start=1778053814.278652 t_end=1778053817.178777 latency_s=2.9001
ok round=16 conc=256 i=3998 t_start=1778053814.280734 t_end=1778053815.979454 latency_s=1.6987
ok round=16 conc=256 i=3999 t_start=1778053814.282836 t_end=1778053817.598131 latency_s=3.3153
ok round=16 conc=256 i=4000 t_start=1778053814.285041 t_end=1778053817.274121 latency_s=2.9891
ok round=16 conc=256 i=4001 t_start=1778053814.287156 t_end=1778053816.428368 latency_s=2.1412
ok round=16 conc=256 i=4002 t_start=1778053814.289333 t_end=1778053817.885814 latency_s=3.5965
ok round=16 conc=256 i=4003 t_start=1778053814.291398 t_end=1778053817.541316 latency_s=3.2499
ok round=16 conc=256 i=4004 t_start=1778053814.293480 t_end=1778053816.115579 latency_s=1.8221
ok round=16 conc=256 i=4005 t_start=1778053814.295577 t_end=1778053817.511294 latency_s=3.2157
ok round=16 conc=256 i=4006 t_start=1778053814.297652 t_end=1778053817.273666 latency_s=2.9760
ok round=16 conc=256 i=4007 t_start=1778053814.299740 t_end=1778053816.071314 latency_s=1.7716
ok round=16 conc=256 i=4008 t_start=1778053814.301842 t_end=1778053817.425304 latency_s=3.1235
ok round=16 conc=256 i=4009 t_start=1778053814.304000 t_end=1778053819.516665 latency_s=5.2127
ok round=16 conc=256 i=4010 t_start=1778053814.306103 t_end=1778053817.557139 latency_s=3.2510
ok round=16 conc=256 i=4011 t_start=1778053814.308202 t_end=1778053816.121493 latency_s=1.8133
ok round=16 conc=256 i=4012 t_start=1778053814.310296 t_end=1778053817.405385 latency_s=3.0951
ok round=16 conc=256 i=4013 t_start=1778053814.312382 t_end=1778053816.391703 latency_s=2.0793
ok round=16 conc=256 i=4014 t_start=1778053814.314458 t_end=1778053817.395430 latency_s=3.0810
ok round=16 conc=256 i=4015 t_start=1778053814.316637 t_end=1778053817.422341 latency_s=3.1057
ok round=16 conc=256 i=4016 t_start=1778053814.318752 t_end=1778053816.210401 latency_s=1.8916
ok round=16 conc=256 i=4017 t_start=1778053814.320842 t_end=1778053817.458119 latency_s=3.1373
ok round=16 conc=256 i=4018 t_start=1778053814.322956 t_end=1778053817.394878 latency_s=3.0719
ok round=16 conc=256 i=4019 t_start=1778053814.325008 t_end=1778053817.515673 latency_s=3.1907
ok round=16 conc=256 i=4020 t_start=1778053814.327106 t_end=1778053816.740731 latency_s=2.4136
ok round=16 conc=256 i=4021 t_start=1778053814.329169 t_end=1778053817.614969 latency_s=3.2858
ok round=16 conc=256 i=4022 t_start=1778053814.331396 t_end=1778053817.014825 latency_s=2.6834
ok round=16 conc=256 i=4023 t_start=1778053814.333481 t_end=1778053816.226557 latency_s=1.8931
ok round=16 conc=256 i=4024 t_start=1778053814.335537 t_end=1778053816.945583 latency_s=2.6100
ok round=16 conc=256 i=4025 t_start=1778053814.337634 t_end=1778053816.788630 latency_s=2.4510
ok round=16 conc=256 i=4026 t_start=1778053814.339743 t_end=1778053817.600521 latency_s=3.2608
ok round=16 conc=256 i=4027 t_start=1778053814.341841 t_end=1778053818.668474 latency_s=4.3266
ok round=16 conc=256 i=4028 t_start=1778053814.343981 t_end=1778053816.726635 latency_s=2.3827
ok round=16 conc=256 i=4029 t_start=1778053814.346064 t_end=1778053817.512997 latency_s=3.1669
ok round=16 conc=256 i=4030 t_start=1778053814.348145 t_end=1778053816.389589 latency_s=2.0414
ok round=16 conc=256 i=4031 t_start=1778053814.350200 t_end=1778053817.616271 latency_s=3.2661
ok round=16 conc=256 i=4032 t_start=1778053814.352293 t_end=1778053816.994380 latency_s=2.6421
ok round=16 conc=256 i=4033 t_start=1778053814.354434 t_end=1778053817.575243 latency_s=3.2208
ok round=16 conc=256 i=4034 t_start=1778053814.356517 t_end=1778053817.962355 latency_s=3.6058
ok round=16 conc=256 i=4035 t_start=1778053814.358680 t_end=1778053817.602456 latency_s=3.2438
ok round=16 conc=256 i=4036 t_start=1778053814.360778 t_end=1778053817.274912 latency_s=2.9141
ok round=16 conc=256 i=4037 t_start=1778053814.362873 t_end=1778053817.029333 latency_s=2.6665
ok round=16 conc=256 i=4038 t_start=1778053814.365107 t_end=1778053817.571419 latency_s=3.2063
ok round=16 conc=256 i=4039 t_start=1778053814.367189 t_end=1778053816.460795 latency_s=2.0936
ok round=16 conc=256 i=4040 t_start=1778053814.369248 t_end=1778053817.623657 latency_s=3.2544
ok round=16 conc=256 i=4041 t_start=1778053814.371405 t_end=1778053816.748785 latency_s=2.3774
ok round=16 conc=256 i=4042 t_start=1778053814.373514 t_end=1778053816.845205 latency_s=2.4717
ok round=16 conc=256 i=4043 t_start=1778053814.375595 t_end=1778053817.398970 latency_s=3.0234
ok round=16 conc=256 i=4044 t_start=1778053814.377689 t_end=1778053817.486959 latency_s=3.1093
ok round=16 conc=256 i=4045 t_start=1778053814.379793 t_end=1778053817.581247 latency_s=3.2015
ok round=16 conc=256 i=4046 t_start=1778053814.381855 t_end=1778053817.408308 latency_s=3.0265
ok round=16 conc=256 i=4047 t_start=1778053814.383911 t_end=1778053816.520161 latency_s=2.1363
ok round=16 conc=256 i=4048 t_start=1778053814.386098 t_end=1778053817.627335 latency_s=3.2412
ok round=16 conc=256 i=4049 t_start=1778053814.388193 t_end=1778053816.593319 latency_s=2.2051
ok round=16 conc=256 i=4050 t_start=1778053814.390274 t_end=1778053817.526395 latency_s=3.1361
ok round=16 conc=256 i=4051 t_start=1778053814.392344 t_end=1778053816.801913 latency_s=2.4096
ok round=16 conc=256 i=4052 t_start=1778053814.394417 t_end=1778053817.609782 latency_s=3.2154
ok round=16 conc=256 i=4053 t_start=1778053814.396514 t_end=1778053817.316593 latency_s=2.9201
ok round=16 conc=256 i=4054 t_start=1778053814.398589 t_end=1778053817.318297 latency_s=2.9197
ok round=16 conc=256 i=4055 t_start=1778053814.400887 t_end=1778053817.004665 latency_s=2.6038
ok round=16 conc=256 i=4056 t_start=1778053814.403037 t_end=1778053817.577183 latency_s=3.1741
ok round=16 conc=256 i=4057 t_start=1778053814.405118 t_end=1778053817.548012 latency_s=3.1429
ok round=16 conc=256 i=4058 t_start=1778053814.407186 t_end=1778053816.648211 latency_s=2.2410
ok round=16 conc=256 i=4059 t_start=1778053814.409266 t_end=1778053816.813675 latency_s=2.4044
ok round=16 conc=256 i=4060 t_start=1778053814.411328 t_end=1778053818.938708 latency_s=4.5274
ok round=16 conc=256 i=4061 t_start=1778053814.413501 t_end=1778053816.981699 latency_s=2.5682
ok round=16 conc=256 i=4062 t_start=1778053814.415615 t_end=1778053817.589577 latency_s=3.1740
ok round=16 conc=256 i=4063 t_start=1778053814.417736 t_end=1778053817.044719 latency_s=2.6270
ok round=16 conc=256 i=4064 t_start=1778053814.419877 t_end=1778053817.178994 latency_s=2.7591
ok round=16 conc=256 i=4065 t_start=1778053814.421983 t_end=1778053816.824722 latency_s=2.4027
ok round=16 conc=256 i=4066 t_start=1778053814.424050 t_end=1778053816.766780 latency_s=2.3427
ok round=16 conc=256 i=4067 t_start=1778053814.426146 t_end=1778053817.404703 latency_s=2.9786
ok round=16 conc=256 i=4068 t_start=1778053814.429251 t_end=1778053817.461423 latency_s=3.0322
ok round=16 conc=256 i=4069 t_start=1778053814.431394 t_end=1778053816.890750 latency_s=2.4594
ok round=16 conc=256 i=4070 t_start=1778053814.433470 t_end=1778053817.318048 latency_s=2.8846
ok round=16 conc=256 i=4071 t_start=1778053814.435539 t_end=1778053817.559281 latency_s=3.1237
ok round=16 conc=256 i=4072 t_start=1778053814.437647 t_end=1778053817.501724 latency_s=3.0641
ok round=16 conc=256 i=4073 t_start=1778053814.439709 t_end=1778053818.958301 latency_s=4.5186
ok round=16 conc=256 i=4074 t_start=1778053814.441868 t_end=1778053817.608456 latency_s=3.1666
ok round=16 conc=256 i=4075 t_start=1778053814.443975 t_end=1778053816.874939 latency_s=2.4310
ok round=16 conc=256 i=4076 t_start=1778053814.446049 t_end=1778053817.398350 latency_s=2.9523
ok round=16 conc=256 i=4077 t_start=1778053814.448122 t_end=1778053817.587655 latency_s=3.1395
ok round=16 conc=256 i=4078 t_start=1778053814.450226 t_end=1778053816.887719 latency_s=2.4375
ok round=16 conc=256 i=4079 t_start=1778053814.452346 t_end=1778053817.179209 latency_s=2.7269
ok round=16 conc=256 i=4080 t_start=1778053814.454410 t_end=1778053817.617578 latency_s=3.1632
ok round=16 conc=256 i=4081 t_start=1778053814.456594 t_end=1778053817.317200 latency_s=2.8606
ok round=16 conc=256 i=4082 t_start=1778053814.458722 t_end=1778053817.221176 latency_s=2.7625
ok round=16 conc=256 i=4083 t_start=1778053814.460793 t_end=1778053817.273907 latency_s=2.8131
ok round=16 conc=256 i=4084 t_start=1778053814.462949 t_end=1778053816.957088 latency_s=2.4941
ok round=16 conc=256 i=4085 t_start=1778053814.465165 t_end=1778053816.982486 latency_s=2.5173
ok round=16 conc=256 i=4086 t_start=1778053814.467314 t_end=1778053819.108048 latency_s=4.6407
ok round=16 conc=256 i=4087 t_start=1778053814.469480 t_end=1778053817.611055 latency_s=3.1416
ok round=16 conc=256 i=4088 t_start=1778053814.471575 t_end=1778053817.032778 latency_s=2.5612
ok round=16 conc=256 i=4089 t_start=1778053814.473674 t_end=1778053817.591773 latency_s=3.1181
ok round=16 conc=256 i=4090 t_start=1778053814.475730 t_end=1778053817.415000 latency_s=2.9393
ok round=16 conc=256 i=4091 t_start=1778053814.477795 t_end=1778053817.566873 latency_s=3.0891
ok round=16 conc=256 i=4092 t_start=1778053814.479891 t_end=1778053817.454157 latency_s=2.9743
ok round=16 conc=256 i=4093 t_start=1778053814.482008 t_end=1778053817.348845 latency_s=2.8668
ok round=16 conc=256 i=4094 t_start=1778053814.484156 t_end=1778053817.594395 latency_s=3.1102
ok round=16 conc=256 i=4095 t_start=1778053814.486266 t_end=1778053817.318176 latency_s=2.8319
ok round=16 conc=256 i=4096 t_start=1778053814.488356 t_end=1778053817.527737 latency_s=3.0394
--- summary ---
stop_reason=max_requests
successful_requests=4096
total_attempts=4096
rounds_run=16
peak_concurrency=256
total_wall_s=91.8041
approx_throughput_rpm=2677.01
reference_only_last_start_t=1778053814.488356 window_60s_requests_started=2859 (no API failure; stop=max_requests; not a rate-limit RPM)
latency_s min=0.6000 p50=2.3828 max=7.2672
```

## `kimi-k2.6`（slug=`kimi-k2.6`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.6/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['kimi-k2.6'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=kimi-k2.6
  [kimi-k2.6] OK (17.27s): 我是 Kimi，由月之暗面（Moonshot AI）开发的人工智能助手，擅长长文本处理、多语言对话与复杂问题分析。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.6/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['kimi-k2.6'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=kimi-k2.6
  [kimi-k2.6] OK (2.30s): 你好，我是 Kimi，一个由月之暗面科技有限公司开发的人工智能助手。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.6/usage.log`

```
model=kimi-k2.6	prompt_tokens=15	completion_tokens=124	total_tokens=139	wall_s=10.02
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.6/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=kimi-k2.6 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=92.5751
ok round=2 conc=2 i=2 latency_s=96.3369
ok round=2 conc=2 i=3 latency_s=38.2042
ok round=3 conc=4 i=4 latency_s=51.4138
ok round=3 conc=4 i=5 latency_s=64.6102
ok round=3 conc=4 i=6 latency_s=80.4680
ok round=3 conc=4 i=7 latency_s=64.6948
ok round=4 conc=8 i=8 latency_s=60.0272
ok round=4 conc=8 i=9 latency_s=42.8824
ok round=4 conc=8 i=10 latency_s=79.4469
ok round=4 conc=8 i=11 latency_s=93.5698
ok round=4 conc=8 i=12 latency_s=95.5172
ok round=4 conc=8 i=13 latency_s=82.0283
ok round=4 conc=8 i=14 latency_s=86.5718
ok round=4 conc=8 i=15 latency_s=56.2078
ok round=5 conc=16 i=16 latency_s=51.2911
ok round=5 conc=16 i=17 latency_s=47.7692
ok round=5 conc=16 i=18 latency_s=43.2697
ok round=5 conc=16 i=19 latency_s=63.9465
ok round=5 conc=16 i=20 latency_s=76.1098
ok round=5 conc=16 i=21 latency_s=42.4242
ok round=5 conc=16 i=22 latency_s=27.4071
ok round=5 conc=16 i=23 latency_s=74.3919
ok round=5 conc=16 i=24 latency_s=39.6528
ok round=5 conc=16 i=25 latency_s=19.8315
ok round=5 conc=16 i=26 latency_s=55.8522
ok round=5 conc=16 i=27 latency_s=58.8098
ok round=5 conc=16 i=28 latency_s=48.1217
ok round=5 conc=16 i=29 latency_s=73.3271
ok round=5 conc=16 i=30 latency_s=49.1538
ok round=5 conc=16 i=31 latency_s=77.0341
--- summary ---
stop_reason=max_concurrency_no_limit_hit
successful_requests=31
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=441.9540
approx_throughput_rpm=4.21
latency_s min=19.8315 p50=60.0272 max=96.3369
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.6/rpm_minute.log`

```
8054442.489213 t_end=1778054447.962801 latency_s=5.4736
ok round=16 conc=256 i=3975 t_start=1778054442.491481 t_end=1778054450.423645 latency_s=7.9322
ok round=16 conc=256 i=3976 t_start=1778054442.493720 t_end=1778054446.627144 latency_s=4.1334
ok round=16 conc=256 i=3977 t_start=1778054442.495933 t_end=1778054448.692095 latency_s=6.1962
ok round=16 conc=256 i=3978 t_start=1778054442.498100 t_end=1778054448.177785 latency_s=5.6797
ok round=16 conc=256 i=3979 t_start=1778054442.500308 t_end=1778054448.399668 latency_s=5.8994
ok round=16 conc=256 i=3980 t_start=1778054442.502493 t_end=1778054446.235446 latency_s=3.7330
ok round=16 conc=256 i=3981 t_start=1778054442.504837 t_end=1778054446.710858 latency_s=4.2060
ok round=16 conc=256 i=3982 t_start=1778054442.507030 t_end=1778054446.501953 latency_s=3.9949
ok round=16 conc=256 i=3983 t_start=1778054442.509265 t_end=1778054446.943220 latency_s=4.4340
ok round=16 conc=256 i=3984 t_start=1778054442.511464 t_end=1778054450.435712 latency_s=7.9242
ok round=16 conc=256 i=3985 t_start=1778054442.513685 t_end=1778054448.441313 latency_s=5.9276
ok round=16 conc=256 i=3986 t_start=1778054442.515893 t_end=1778054447.947989 latency_s=5.4321
ok round=16 conc=256 i=3987 t_start=1778054442.518160 t_end=1778054446.592946 latency_s=4.0748
ok round=16 conc=256 i=3988 t_start=1778054442.520483 t_end=1778054446.562553 latency_s=4.0421
ok round=16 conc=256 i=3989 t_start=1778054442.522763 t_end=1778054448.949188 latency_s=6.4264
ok round=16 conc=256 i=3990 t_start=1778054442.525023 t_end=1778054447.794989 latency_s=5.2700
ok round=16 conc=256 i=3991 t_start=1778054442.527224 t_end=1778054447.605880 latency_s=5.0787
ok round=16 conc=256 i=3992 t_start=1778054442.529436 t_end=1778054450.463397 latency_s=7.9340
ok round=16 conc=256 i=3993 t_start=1778054442.531589 t_end=1778054446.646683 latency_s=4.1151
ok round=16 conc=256 i=3994 t_start=1778054442.533936 t_end=1778054448.687491 latency_s=6.1536
ok round=16 conc=256 i=3995 t_start=1778054442.536114 t_end=1778054448.465323 latency_s=5.9292
ok round=16 conc=256 i=3996 t_start=1778054442.538323 t_end=1778054448.719556 latency_s=6.1812
ok round=16 conc=256 i=3997 t_start=1778054442.540516 t_end=1778054446.818009 latency_s=4.2775
ok round=16 conc=256 i=3998 t_start=1778054442.542716 t_end=1778054448.617624 latency_s=6.0749
ok round=16 conc=256 i=3999 t_start=1778054442.544968 t_end=1778054446.951824 latency_s=4.4069
ok round=16 conc=256 i=4000 t_start=1778054442.547298 t_end=1778054448.757126 latency_s=6.2098
ok round=16 conc=256 i=4001 t_start=1778054442.549512 t_end=1778054446.992632 latency_s=4.4431
ok round=16 conc=256 i=4002 t_start=1778054442.551694 t_end=1778054448.220740 latency_s=5.6690
ok round=16 conc=256 i=4003 t_start=1778054442.553929 t_end=1778054446.617100 latency_s=4.0632
ok round=16 conc=256 i=4004 t_start=1778054442.556106 t_end=1778054447.610111 latency_s=5.0540
ok round=16 conc=256 i=4005 t_start=1778054442.558311 t_end=1778054448.969501 latency_s=6.4112
ok round=16 conc=256 i=4006 t_start=1778054442.560612 t_end=1778054446.598429 latency_s=4.0378
ok round=16 conc=256 i=4007 t_start=1778054442.563010 t_end=1778054447.597429 latency_s=5.0344
ok round=16 conc=256 i=4008 t_start=1778054442.565251 t_end=1778054448.159973 latency_s=5.5947
ok round=16 conc=256 i=4009 t_start=1778054442.567450 t_end=1778054447.026880 latency_s=4.4594
ok round=16 conc=256 i=4010 t_start=1778054442.569621 t_end=1778054447.194428 latency_s=4.6248
ok round=16 conc=256 i=4011 t_start=1778054442.571860 t_end=1778054450.382242 latency_s=7.8104
ok round=16 conc=256 i=4012 t_start=1778054442.574134 t_end=1778054448.350701 latency_s=5.7766
ok round=16 conc=256 i=4013 t_start=1778054442.576400 t_end=1778054446.004713 latency_s=3.4283
ok round=16 conc=256 i=4014 t_start=1778054442.578735 t_end=1778054446.865844 latency_s=4.2871
ok round=16 conc=256 i=4015 t_start=1778054442.581069 t_end=1778054446.368711 latency_s=3.7876
ok round=16 conc=256 i=4016 t_start=1778054442.583409 t_end=1778054448.585944 latency_s=6.0025
ok round=16 conc=256 i=4017 t_start=1778054442.585667 t_end=1778054446.653718 latency_s=4.0681
ok round=16 conc=256 i=4018 t_start=1778054442.588868 t_end=1778054446.950966 latency_s=4.3621
ok round=16 conc=256 i=4019 t_start=1778054442.591179 t_end=1778054447.165031 latency_s=4.5739
ok round=16 conc=256 i=4020 t_start=1778054442.593502 t_end=1778054447.235667 latency_s=4.6422
ok round=16 conc=256 i=4021 t_start=1778054442.595729 t_end=1778054448.701858 latency_s=6.1061
ok round=16 conc=256 i=4022 t_start=1778054442.597941 t_end=1778054448.062439 latency_s=5.4645
ok round=16 conc=256 i=4023 t_start=1778054442.600128 t_end=1778054447.338315 latency_s=4.7382
ok round=16 conc=256 i=4024 t_start=1778054442.602319 t_end=1778054448.325789 latency_s=5.7235
ok round=16 conc=256 i=4025 t_start=1778054442.604390 t_end=1778054450.591639 latency_s=7.9872
ok round=16 conc=256 i=4026 t_start=1778054442.606395 t_end=1778054447.819986 latency_s=5.2136
ok round=16 conc=256 i=4027 t_start=1778054442.608364 t_end=1778054447.992465 latency_s=5.3841
ok round=16 conc=256 i=4028 t_start=1778054442.610369 t_end=1778054448.700142 latency_s=6.0898
ok round=16 conc=256 i=4029 t_start=1778054442.612382 t_end=1778054448.225860 latency_s=5.6135
ok round=16 conc=256 i=4030 t_start=1778054442.614463 t_end=1778054447.712408 latency_s=5.0979
ok round=16 conc=256 i=4031 t_start=1778054442.616491 t_end=1778054450.179827 latency_s=7.5633
ok round=16 conc=256 i=4032 t_start=1778054442.618486 t_end=1778054447.779950 latency_s=5.1615
ok round=16 conc=256 i=4033 t_start=1778054442.620521 t_end=1778054451.974552 latency_s=9.3540
ok round=16 conc=256 i=4034 t_start=1778054442.622539 t_end=1778054448.103458 latency_s=5.4809
ok round=16 conc=256 i=4035 t_start=1778054442.624551 t_end=1778054447.784992 latency_s=5.1604
ok round=16 conc=256 i=4036 t_start=1778054442.626653 t_end=1778054446.820971 latency_s=4.1943
ok round=16 conc=256 i=4037 t_start=1778054442.628693 t_end=1778054451.946051 latency_s=9.3174
ok round=16 conc=256 i=4038 t_start=1778054442.630703 t_end=1778054447.955859 latency_s=5.3252
ok round=16 conc=256 i=4039 t_start=1778054442.632718 t_end=1778054447.394252 latency_s=4.7615
ok round=16 conc=256 i=4040 t_start=1778054442.634726 t_end=1778054447.873765 latency_s=5.2390
ok round=16 conc=256 i=4041 t_start=1778054442.636747 t_end=1778054449.635381 latency_s=6.9986
ok round=16 conc=256 i=4042 t_start=1778054442.638736 t_end=1778054446.828433 latency_s=4.1897
ok round=16 conc=256 i=4043 t_start=1778054442.640879 t_end=1778054449.372716 latency_s=6.7318
ok round=16 conc=256 i=4044 t_start=1778054442.643007 t_end=1778054449.066557 latency_s=6.4236
ok round=16 conc=256 i=4045 t_start=1778054442.645073 t_end=1778054448.000926 latency_s=5.3559
ok round=16 conc=256 i=4046 t_start=1778054442.647098 t_end=1778054448.328731 latency_s=5.6816
ok round=16 conc=256 i=4047 t_start=1778054442.649066 t_end=1778054449.150984 latency_s=6.5019
ok round=16 conc=256 i=4048 t_start=1778054442.651062 t_end=1778054448.419787 latency_s=5.7687
ok round=16 conc=256 i=4049 t_start=1778054442.653166 t_end=1778054447.998167 latency_s=5.3450
ok round=16 conc=256 i=4050 t_start=1778054442.655161 t_end=1778054447.630827 latency_s=4.9757
ok round=16 conc=256 i=4051 t_start=1778054442.657133 t_end=1778054448.027496 latency_s=5.3704
ok round=16 conc=256 i=4052 t_start=1778054442.659110 t_end=1778054447.111904 latency_s=4.4528
ok round=16 conc=256 i=4053 t_start=1778054442.661140 t_end=1778054448.808915 latency_s=6.1478
ok round=16 conc=256 i=4054 t_start=1778054442.663232 t_end=1778054449.566103 latency_s=6.9029
ok round=16 conc=256 i=4055 t_start=1778054442.665318 t_end=1778054449.361009 latency_s=6.6957
ok round=16 conc=256 i=4056 t_start=1778054442.667306 t_end=1778054449.844675 latency_s=7.1774
ok round=16 conc=256 i=4057 t_start=1778054442.669414 t_end=1778054447.081747 latency_s=4.4123
ok round=16 conc=256 i=4058 t_start=1778054442.671442 t_end=1778054448.997313 latency_s=6.3259
ok round=16 conc=256 i=4059 t_start=1778054442.673416 t_end=1778054448.425073 latency_s=5.7517
ok round=16 conc=256 i=4060 t_start=1778054442.675428 t_end=1778054449.594749 latency_s=6.9193
ok round=16 conc=256 i=4061 t_start=1778054442.677677 t_end=1778054447.132144 latency_s=4.4545
ok round=16 conc=256 i=4062 t_start=1778054442.679775 t_end=1778054450.566436 latency_s=7.8867
ok round=16 conc=256 i=4063 t_start=1778054442.681742 t_end=1778054448.416823 latency_s=5.7351
ok round=16 conc=256 i=4064 t_start=1778054442.683701 t_end=1778054447.151021 latency_s=4.4673
ok round=16 conc=256 i=4065 t_start=1778054442.685683 t_end=1778054448.191488 latency_s=5.5058
ok round=16 conc=256 i=4066 t_start=1778054442.687625 t_end=1778054447.729367 latency_s=5.0417
ok round=16 conc=256 i=4067 t_start=1778054442.689663 t_end=1778054446.895678 latency_s=4.2060
ok round=16 conc=256 i=4068 t_start=1778054442.691643 t_end=1778054446.874828 latency_s=4.1832
ok round=16 conc=256 i=4069 t_start=1778054442.693613 t_end=1778054448.705237 latency_s=6.0116
ok round=16 conc=256 i=4070 t_start=1778054442.695567 t_end=1778054448.234963 latency_s=5.5394
ok round=16 conc=256 i=4071 t_start=1778054442.697528 t_end=1778054450.541318 latency_s=7.8438
ok round=16 conc=256 i=4072 t_start=1778054442.699497 t_end=1778054446.312439 latency_s=3.6129
ok round=16 conc=256 i=4073 t_start=1778054442.701542 t_end=1778054446.487787 latency_s=3.7862
ok round=16 conc=256 i=4074 t_start=1778054442.703546 t_end=1778054447.841924 latency_s=5.1384
ok round=16 conc=256 i=4075 t_start=1778054442.705521 t_end=1778054448.718511 latency_s=6.0130
ok round=16 conc=256 i=4076 t_start=1778054442.707482 t_end=1778054447.018852 latency_s=4.3114
ok round=16 conc=256 i=4077 t_start=1778054442.709425 t_end=1778054446.871753 latency_s=4.1623
ok round=16 conc=256 i=4078 t_start=1778054442.711373 t_end=1778054447.154863 latency_s=4.4435
ok round=16 conc=256 i=4079 t_start=1778054442.713352 t_end=1778054447.683401 latency_s=4.9700
ok round=16 conc=256 i=4080 t_start=1778054442.715451 t_end=1778054450.781560 latency_s=8.0661
ok round=16 conc=256 i=4081 t_start=1778054442.717424 t_end=1778054447.933200 latency_s=5.2158
ok round=16 conc=256 i=4082 t_start=1778054442.719372 t_end=1778054449.990287 latency_s=7.2709
ok round=16 conc=256 i=4083 t_start=1778054442.721410 t_end=1778054448.423630 latency_s=5.7022
ok round=16 conc=256 i=4084 t_start=1778054442.723479 t_end=1778054446.797702 latency_s=4.0742
ok round=16 conc=256 i=4085 t_start=1778054442.725552 t_end=1778054447.582787 latency_s=4.8572
ok round=16 conc=256 i=4086 t_start=1778054442.727774 t_end=1778054448.077878 latency_s=5.3501
ok round=16 conc=256 i=4087 t_start=1778054442.729918 t_end=1778054449.131414 latency_s=6.4015
ok round=16 conc=256 i=4088 t_start=1778054442.732019 t_end=1778054449.411266 latency_s=6.6792
ok round=16 conc=256 i=4089 t_start=1778054442.733995 t_end=1778054448.410933 latency_s=5.6769
ok round=16 conc=256 i=4090 t_start=1778054442.735924 t_end=1778054447.530837 latency_s=4.7949
ok round=16 conc=256 i=4091 t_start=1778054442.737781 t_end=1778054446.906900 latency_s=4.1691
ok round=16 conc=256 i=4092 t_start=1778054442.740592 t_end=1778054447.150160 latency_s=4.4096
ok round=16 conc=256 i=4093 t_start=1778054442.742517 t_end=1778054446.881515 latency_s=4.1390
ok round=16 conc=256 i=4094 t_start=1778054442.744439 t_end=1778054448.838414 latency_s=6.0940
ok round=16 conc=256 i=4095 t_start=1778054442.746439 t_end=1778054448.309871 latency_s=5.5634
ok round=16 conc=256 i=4096 t_start=1778054442.748437 t_end=1778054449.357311 latency_s=6.6089
--- summary ---
stop_reason=max_requests
successful_requests=4096
total_attempts=4096
rounds_run=16
peak_concurrency=256
total_wall_s=158.0504
approx_throughput_rpm=1554.95
reference_only_last_start_t=1778054442.748437 window_60s_requests_started=1536 (no API failure; stop=max_requests; not a rate-limit RPM)
latency_s min=2.1237 p50=4.6476 max=11.1200
```

## `kimi-k2.5`（slug=`kimi-k2.5`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.5/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['kimi-k2.5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=kimi-k2.5
  [kimi-k2.5] OK (25.16s): 我是 Kimi，由月之暗面科技有限公司（Moonshot AI）开发的具备超长上下文处理、多模态理解与智能体能力的人工智能助手。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.5/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['kimi-k2.5'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=kimi-k2.5
  [kimi-k2.5] OK (16.42s): 你好，我是Claude，一个AI助手。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.5/usage.log`

```
model=kimi-k2.5	prompt_tokens=15	completion_tokens=253	total_tokens=268	wall_s=27.60
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.5/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=kimi-k2.5 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=55.0183
ok round=2 conc=2 i=2 latency_s=58.9551
ok round=2 conc=2 i=3 latency_s=51.4179
ok round=3 conc=4 i=4 latency_s=51.6770
ok round=3 conc=4 i=5 latency_s=54.2400
ok round=3 conc=4 i=6 latency_s=47.5628
ok round=3 conc=4 i=7 latency_s=59.4644
ok round=4 conc=8 i=8 latency_s=47.2541
ok round=4 conc=8 i=9 latency_s=54.0091
ok round=4 conc=8 i=10 latency_s=38.1084
ok round=4 conc=8 i=11 latency_s=47.9006
ok round=4 conc=8 i=12 latency_s=58.3170
ok round=4 conc=8 i=13 latency_s=52.4437
ok round=4 conc=8 i=14 latency_s=53.6365
ok round=4 conc=8 i=15 latency_s=56.9461
ok round=5 conc=16 i=16 latency_s=46.6830
ok round=5 conc=16 i=17 latency_s=44.2633
ok round=5 conc=16 i=18 latency_s=48.9759
ok round=5 conc=16 i=19 latency_s=33.5457
ok round=5 conc=16 i=20 latency_s=46.4291
ok round=5 conc=16 i=21 latency_s=48.9469
ok round=5 conc=16 i=22 latency_s=50.1425
ok round=5 conc=16 i=23 latency_s=47.4739
ok round=5 conc=16 i=24 latency_s=52.1710
ok round=5 conc=16 i=25 latency_s=48.9444
ok round=5 conc=16 i=26 latency_s=43.3738
ok round=5 conc=16 i=27 latency_s=48.1873
ok round=5 conc=16 i=28 latency_s=51.2121
ok round=5 conc=16 i=29 latency_s=45.9773
ok round=5 conc=16 i=30 latency_s=48.9395
ok round=5 conc=16 i=31 latency_s=41.2361
--- summary ---
stop_reason=max_concurrency_no_limit_hit
successful_requests=31
total_attempts=31
rounds_run=5
peak_concurrency=16
total_wall_s=283.9434
approx_throughput_rpm=6.55
latency_s min=33.5457 p50=48.9469 max=59.4644
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/kimi-k2.5/rpm_minute.log`

```
rloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=215 t_start=1778054808.007217 t_end=1778054846.167940 latency_s=38.1607 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=216 t_start=1778054808.007470 t_end=1778054846.178494 latency_s=38.1710 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=217 t_start=1778054808.008036 t_end=1778054845.859218 latency_s=37.8512 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=218 t_start=1778054808.008332 t_end=1778054844.886278 latency_s=36.8779 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=219 t_start=1778054808.008580 t_end=1778054846.100768 latency_s=38.0922 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=220 t_start=1778054808.008862 t_end=1778054845.902088 latency_s=37.8932 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=221 t_start=1778054808.009110 t_end=1778054845.938792 latency_s=37.9297 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=222 t_start=1778054808.009357 t_end=1778054845.910266 latency_s=37.9009 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=223 t_start=1778054808.009625 t_end=1778054846.209205 latency_s=38.1996 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=224 t_start=1778054808.009889 t_end=1778054845.895868 latency_s=37.8860 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=225 t_start=1778054808.010130 t_end=1778054845.103894 latency_s=37.0938 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=226 t_start=1778054808.010370 t_end=1778054846.353598 latency_s=38.3432 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=227 t_start=1778054808.010622 t_end=1778054845.938930 latency_s=37.9283 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=228 t_start=1778054808.010876 t_end=1778054846.215693 latency_s=38.2048 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=229 t_start=1778054808.011118 t_end=1778054846.194528 latency_s=38.1834 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=230 t_start=1778054808.011393 t_end=1778054845.926920 latency_s=37.9155 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=231 t_start=1778054808.011653 t_end=1778054845.969086 latency_s=37.9574 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=232 t_start=1778054808.011913 t_end=1778054845.926652 latency_s=37.9147 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=233 t_start=1778054808.012161 t_end=1778054845.859409 latency_s=37.8472 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=234 t_start=1778054808.012399 t_end=1778054845.949563 latency_s=37.9372 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=235 t_start=1778054808.012655 t_end=1778054846.133742 latency_s=38.1211 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=236 t_start=1778054808.012942 t_end=1778054845.969201 latency_s=37.9563 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=237 t_start=1778054808.013476 t_end=1778054844.886202 latency_s=36.8727 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=238 t_start=1778054808.013740 t_end=1778054845.940007 latency_s=37.9263 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=239 t_start=1778054808.014008 t_end=1778054844.615743 latency_s=36.6017 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=240 t_start=1778054808.014258 t_end=1778054846.126355 latency_s=38.1121 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=241 t_start=1778054808.014545 t_end=1778054846.179774 latency_s=38.1652 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=242 t_start=1778054808.014832 t_end=1778054845.939043 latency_s=37.9242 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=243 t_start=1778054808.015084 t_end=1778054845.912637 latency_s=37.8976 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=244 t_start=1778054808.015329 t_end=1778054845.896023 latency_s=37.8807 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=245 t_start=1778054808.015576 t_end=1778054846.349355 latency_s=38.3338 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=246 t_start=1778054808.015842 t_end=1778054845.844597 latency_s=37.8288 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=247 t_start=1778054808.016087 t_end=1778054845.919978 latency_s=37.9039 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=248 t_start=1778054808.016327 t_end=1778054845.969278 latency_s=37.9530 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=249 t_start=1778054808.016582 t_end=1778054846.211336 latency_s=38.1948 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=250 t_start=1778054808.016845 t_end=1778054845.872913 latency_s=37.8561 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=251 t_start=1778054808.017087 t_end=1778054844.644158 latency_s=36.6271 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=252 t_start=1778054808.017331 t_end=1778054845.959932 latency_s=37.9426 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=253 t_start=1778054808.017632 t_end=1778054846.201712 latency_s=38.1841 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=254 t_start=1778054808.017890 t_end=1778054846.198829 latency_s=38.1809 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=255 t_start=1778054808.018158 t_end=1778054845.964121 latency_s=37.9460 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
fail round=1 conc=256 i=256 t_start=1778054808.018409 t_end=1778054845.963546 latency_s=37.9451 status=429 msg=Error code: 429 - {'error': {'message': 'The engine is currently overloaded, please try again later', 'type': 'engine_overloaded_error', 'param': '', 'code': None}}
--- summary ---
stop_reason=429
successful_requests=0
total_attempts=256
rounds_run=1
peak_concurrency=256
total_wall_s=39.8923
approx_throughput_rpm=0.00
first_failure_i=1 anchor_t_start=1778054807.813430 window_60s_requests_started=1
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
```

## `step-3.5-flash-2603`（slug=`step-3.5-flash-2603`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash-2603/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['step-3.5-flash-2603'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=step-3.5-flash-2603
  [step-3.5-flash-2603] OK (3.56s): 我是Step，由阶跃星辰（StepFun）开发的大语言模型，具备多模态推理和自然语言理解能力，致力于为你提供诚实可靠、有用友善的智能帮助。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash-2603/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['step-3.5-flash-2603'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=step-3.5-flash-2603
  [step-3.5-flash-2603] OK (1.10s): 你好，我是Step，由阶跃星辰（StepFun）开发的大语言模型，具备多模态推理和知识问答能力，致力于为你提供可靠、有用、友好的帮助。
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash-2603/usage.log`

```
model=step-3.5-flash-2603	prompt_tokens=20	completion_tokens=177	total_tokens=197	wall_s=1.51
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash-2603/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=step-3.5-flash-2603 max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=7.6540
ok round=2 conc=2 i=2 latency_s=6.8697
ok round=2 conc=2 i=3 latency_s=5.3631
ok round=3 conc=4 i=4 latency_s=6.8224
ok round=3 conc=4 i=5 latency_s=6.4817
ok round=3 conc=4 i=6 latency_s=7.5846
ok round=3 conc=4 i=7 latency_s=6.6787
ok round=4 conc=8 i=8 latency_s=9.0392
ok round=4 conc=8 i=9 latency_s=8.8133
fail round=4 conc=8 i=10 latency_s=4.1979 status=429 msg=Error code: 429 - {'error': {'message': 'request limited concurrency reached, current: 6, limit: 5. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
ok round=4 conc=8 i=11 latency_s=9.3695
ok round=4 conc=8 i=12 latency_s=9.5879
fail round=4 conc=8 i=13 latency_s=4.3691 status=429 msg=Error code: 429 - {'error': {'message': 'request limited concurrency reached, current: 6, limit: 5. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=14 latency_s=4.3766 status=429 msg=Error code: 429 - {'error': {'message': 'request limited concurrency reached, current: 6, limit: 5. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
ok round=4 conc=8 i=15 latency_s=9.6083
--- summary ---
stop_reason=429
successful_requests=12
total_attempts=15
rounds_run=4
peak_concurrency=8
total_wall_s=31.7269
approx_throughput_rpm=22.69
latency_s min=5.3631 p50=7.6193 max=9.6083
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash-2603/rpm_minute.log`

```
y_s=5.9835 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 16, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=224 t_start=1778054888.557110 t_end=1778054893.763943 latency_s=5.2068 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=225 t_start=1778054888.557357 t_end=1778054893.356791 latency_s=4.7994 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=226 t_start=1778054888.557616 t_end=1778054893.912014 latency_s=5.3544 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=227 t_start=1778054888.557878 t_end=1778054894.446321 latency_s=5.8884 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=228 t_start=1778054888.558120 t_end=1778054893.757156 latency_s=5.1990 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=229 t_start=1778054888.558364 t_end=1778054893.153933 latency_s=4.5956 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=230 t_start=1778054888.558661 t_end=1778054893.911912 latency_s=5.3533 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=231 t_start=1778054888.558931 t_end=1778054894.510069 latency_s=5.9511 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=232 t_start=1778054888.559176 t_end=1778054894.518318 latency_s=5.9591 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=233 t_start=1778054888.559417 t_end=1778054894.513520 latency_s=5.9541 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 14, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=234 t_start=1778054888.559673 t_end=1778054894.404025 latency_s=5.8444 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=235 t_start=1778054888.560100 t_end=1778054894.493007 latency_s=5.9329 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=236 t_start=1778054888.560359 t_end=1778054893.885124 latency_s=5.3248 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=237 t_start=1778054888.560619 t_end=1778054894.547929 latency_s=5.9873 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=238 t_start=1778054888.560880 t_end=1778054894.380725 latency_s=5.8198 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=239 t_start=1778054888.561129 t_end=1778054894.531814 latency_s=5.9707 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 15, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=240 t_start=1778054888.561388 t_end=1778054893.741685 latency_s=5.1803 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=241 t_start=1778054888.561684 t_end=1778054894.467917 latency_s=5.9062 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 16, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=242 t_start=1778054888.561947 t_end=1778054894.517067 latency_s=5.9551 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 16, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=243 t_start=1778054888.562191 t_end=1778054894.450340 latency_s=5.8881 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 15, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=244 t_start=1778054888.562464 t_end=1778054893.879456 latency_s=5.3170 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=245 t_start=1778054888.562725 t_end=1778054894.429800 latency_s=5.8671 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=246 t_start=1778054888.562979 t_end=1778054893.242827 latency_s=4.6798 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=247 t_start=1778054888.563220 t_end=1778054893.258508 latency_s=4.6953 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=248 t_start=1778054888.563463 t_end=1778054893.357427 latency_s=4.7940 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=249 t_start=1778054888.563735 t_end=1778054893.296726 latency_s=4.7330 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=250 t_start=1778054888.564002 t_end=1778054893.298479 latency_s=4.7345 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=251 t_start=1778054888.564252 t_end=1778054893.911556 latency_s=5.3473 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=252 t_start=1778054888.564496 t_end=1778054893.426692 latency_s=4.8622 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=253 t_start=1778054888.564795 t_end=1778054894.437803 latency_s=5.8730 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 17, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=254 t_start=1778054888.565665 t_end=1778054893.762857 latency_s=5.1972 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=255 t_start=1778054888.565957 t_end=1778054894.084532 latency_s=5.5186 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=256 t_start=1778054888.566227 t_end=1778054894.416558 latency_s=5.8503 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
--- summary ---
stop_reason=429
successful_requests=5
total_attempts=256
rounds_run=1
peak_concurrency=256
total_wall_s=6.2124
approx_throughput_rpm=48.29
first_failure_i=3 anchor_t_start=1778054888.492061 window_60s_requests_started=3
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
latency_s min=1.2661 p50=1.4019 max=1.5103
```

## `step-3.5-flash`（slug=`step-3.5-flash`）
### test_chat OpenAI
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash/test_chat_openai.log`

```
Namespace(client='openai', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['step-3.5-flash'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=openai): base_url=https://llm.sxwl.ai/v1, models=step-3.5-flash
  [step-3.5-flash] OK (1.45s): 我是由阶跃星辰（StepFun）开发的大语言模型Step，具备多模态推理与知识问答能力。
1/1 passed. Exit 0.
```

### test_chat Anthropic
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash/test_chat_anthropic.log`

```
Namespace(client='anthropic', base_url='https://llm.sxwl.ai/v1', api_key='***', models_list=['step-3.5-flash'], prompt='你好，请用一句话介绍你自己。', max_tokens=512, no_thinking=False)
Testing NewAPI chat (client=anthropic): anthropic_base_url=https://llm.sxwl.ai, models=step-3.5-flash
  [step-3.5-flash] OK (2.05s): 你好！我是 **Step**，由 **阶跃星辰（StepFun）** 开发的大语言模型，具备多模态推理和知识问答能力，很高兴为你提供帮助！ 🌟
1/1 passed. Exit 0.
```

### Usage 采样
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash/usage.log`

```
model=step-3.5-flash	prompt_tokens=20	completion_tokens=172	total_tokens=192	wall_s=1.50
```

### rpm_until_limit heavy
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash/rpm_heavy.log`

```
rpm_until_limit payload=heavy base_url=https://llm.sxwl.ai/v1 model=step-3.5-flash max_tokens=1000 scale=double start_concurrency=1 max_concurrency=16 max_requests=127
  input_tiktoken_count=10000 tiktoken_encoding=cl100k_base prompt_utf8_bytes=44712
ok round=1 conc=1 i=1 latency_s=7.5956
ok round=2 conc=2 i=2 latency_s=7.6570
ok round=2 conc=2 i=3 latency_s=9.4447
ok round=3 conc=4 i=4 latency_s=7.4494
ok round=3 conc=4 i=5 latency_s=7.8205
ok round=3 conc=4 i=6 latency_s=8.1412
ok round=3 conc=4 i=7 latency_s=9.9878
fail round=4 conc=8 i=8 latency_s=6.9851 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=9 latency_s=7.5418 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=10 latency_s=8.5558 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=11 latency_s=8.2434 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=12 latency_s=7.0204 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=13 latency_s=8.2626 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=14 latency_s=7.9378 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=4 conc=8 i=15 latency_s=7.5289 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
--- summary ---
stop_reason=429
successful_requests=7
total_attempts=15
rounds_run=4
peak_concurrency=8
total_wall_s=35.5918
approx_throughput_rpm=11.80
latency_s min=7.4494 p50=7.8205 max=9.9878
```

### rpm_minute_window_probe batch+minimal
- exit_code: `0`
- 完整日志：`/tmp/sxwl_per_model_full/step-3.5-flash/rpm_minute.log`

```
om/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=222 t_start=1778054938.136385 t_end=1778054943.477214 latency_s=5.3408 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=223 t_start=1778054938.136659 t_end=1778054943.739084 latency_s=5.6024 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 17, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=224 t_start=1778054938.136936 t_end=1778054943.535549 latency_s=5.3986 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 23, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=225 t_start=1778054938.137196 t_end=1778054943.887971 latency_s=5.7508 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=226 t_start=1778054938.137456 t_end=1778054943.858253 latency_s=5.7208 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=227 t_start=1778054938.137722 t_end=1778054942.509467 latency_s=4.3717 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=228 t_start=1778054938.137990 t_end=1778054943.690111 latency_s=5.5521 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 14, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=229 t_start=1778054938.138241 t_end=1778054943.493268 latency_s=5.3550 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 14, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=230 t_start=1778054938.138629 t_end=1778054943.866470 latency_s=5.7278 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=231 t_start=1778054938.138911 t_end=1778054943.843749 latency_s=5.7048 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 16, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=232 t_start=1778054938.139178 t_end=1778054943.770950 latency_s=5.6318 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 17, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=233 t_start=1778054938.139439 t_end=1778054943.514880 latency_s=5.3754 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 19, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=234 t_start=1778054938.139708 t_end=1778054943.796938 latency_s=5.6572 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 17, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=235 t_start=1778054938.139978 t_end=1778054942.589546 latency_s=4.4496 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=236 t_start=1778054938.140235 t_end=1778054943.864890 latency_s=5.7247 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=237 t_start=1778054938.140494 t_end=1778054943.869540 latency_s=5.7290 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=238 t_start=1778054938.140765 t_end=1778054942.405149 latency_s=4.2644 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 15, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=239 t_start=1778054938.141036 t_end=1778054942.684236 latency_s=4.5432 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=240 t_start=1778054938.141299 t_end=1778054943.882959 latency_s=5.7417 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=241 t_start=1778054938.141595 t_end=1778054942.513386 latency_s=4.3718 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=242 t_start=1778054938.141879 t_end=1778054942.668222 latency_s=4.5263 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=243 t_start=1778054938.142137 t_end=1778054942.680923 latency_s=4.5388 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=244 t_start=1778054938.142394 t_end=1778054942.808066 latency_s=4.6657 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=245 t_start=1778054938.142661 t_end=1778054942.594572 latency_s=4.4519 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=246 t_start=1778054938.142925 t_end=1778054943.534117 latency_s=5.3912 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 17, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=247 t_start=1778054938.143180 t_end=1778054942.406666 latency_s=4.2635 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 14, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=248 t_start=1778054938.143585 t_end=1778054942.681423 latency_s=4.5378 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 12, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=249 t_start=1778054938.143907 t_end=1778054942.354464 latency_s=4.2106 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
ok round=1 conc=256 i=250 t_start=1778054938.144177 t_end=1778054941.206384 latency_s=3.0622
fail round=1 conc=256 i=251 t_start=1778054938.144437 t_end=1778054942.504853 latency_s=4.3604 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=252 t_start=1778054938.144762 t_end=1778054943.728008 latency_s=5.5832 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 22, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
ok round=1 conc=256 i=253 t_start=1778054938.145037 t_end=1778054941.821033 latency_s=3.6760
fail round=1 conc=256 i=254 t_start=1778054938.145295 t_end=1778054942.520838 latency_s=4.3755 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 11, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=255 t_start=1778054938.145555 t_end=1778054943.786111 latency_s=5.6406 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 21, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
fail round=1 conc=256 i=256 t_start=1778054938.145843 t_end=1778054943.802345 latency_s=5.6565 status=429 msg=Error code: 429 - {'error': {'message': 'request limited RPM reached, current: 13, limit: 10. Please top up at https://***.com/*** Rate limit rules: https://***.com/***/***/***/***', 'type': 'rate_limited', 'param': '', 'code': None}}
--- summary ---
stop_reason=429
successful_requests=10
total_attempts=256
rounds_run=1
peak_concurrency=256
total_wall_s=5.9589
approx_throughput_rpm=100.69
first_failure_i=1 anchor_t_start=1778054937.934052 window_60s_requests_started=1
note=RPM_window_counts_requests_whose_t_start_falls_in_[anchor-60s,anchor]
latency_s min=2.9022 p50=2.9907 max=3.6760
```


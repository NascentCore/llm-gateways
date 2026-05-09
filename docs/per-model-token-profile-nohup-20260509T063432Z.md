# 四模型 Token 剖面（逐模型 × 三档输入加压）

- **生成时间**：2026-05-09 07:08:33 UTC
- **执行环境**：[ubuntu@18.183.174.245](mailto:ubuntu@18.183.174.245) (nohup 默认: 并发100 1500x1000 15000x500 150000x100)
- **批次根目录（服务器）**：`/tmp/per_model_token_md_nohup_20260509T063432Z`（跑批当时；归档后本地 `tos_staging` 已删除）
- **网关**：`https://api.mixroute.ai/v1`
- **单路线并发（Semaphore）**：`100`
- **samples-by-input**：`1500:1000,15000:500,150000:100`
- **单请求 stream 超时（秒）**：`21600.0`
- **TOS 公网直链**：见文末「火山引擎 TOS 归档」中的 URL 模板与示例（需桶/对象允许匿名读或使用预签名链接）。

指标口径与 `dual_route_stream_profile_probe.py --help` 一致（RPM/TPM/TTFT/TPS）。

## `claude-opus-4-6`

- **工作目录（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6`
- **探针退出码**：0
- **summary 文件（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run_summary.jsonl`


| input_tokens | max_tokens | samples | n_ok | n_fail | RPM       | TPM         | mean_ttft_s | mean_tps  | TOS object key（逐请求 JSONL，该 case 全部行）                                                                                       |
| ------------ | ---------- | ------- | ---- | ------ | --------- | ----------- | ----------- | --------- | ----------------------------------------------------------------------------------------------------------------------- |
| 1500         | 7          | 1000    | 1000 | 0      | 1897.9379 | 3154372.75  | 2.3292      | 3668.6377 | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run/cells/claude-opus-4-6__in1500__routesingle.jsonl`   |
| 15000        | 75         | 500     | 483  | 17     | 15.91     | 254187.65   | 73.0357     | 98.7297   | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run/cells/claude-opus-4-6__in15000__routesingle.jsonl`  |
| 150000       | 750        | 100     | 100  | 0      | 235.2072  | 38783562.61 | 10.6614     | 68.2785   | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run/cells/claude-opus-4-6__in150000__routesingle.jsonl` |


失败摘要：

- input=15000: `RateLimitError: Error code: 429 - {'error': {'message': '当前分组上游负载已饱和，请稍后再试 (request id: 20260509144152861012812ETmU1TST):1; RateLimitError: Error code: 429 - {'error': {'message': '当前分组上游负载已饱和，请稍后再试 (request id: 20260509145306818608087slLPZ3f)':1; RateLimitError: Error code: 429 - {'error': {'message': '当前分组上游负载已饱和，请稍后再试 (request id: 20260509144042568668435Um3MMOeS):1; RateLimitError: Error code: 429 - {'error': {'message': '当前分组上游负载已饱和，请稍后再试 (request id: 20260509143926171341100af3roQPS):1; RateLimitError: Error code: 429 - {'error': {'message': '当前分组上游负载已饱和，请稍后再试 (request id: 20260509144441824743368k6VdS5Nw):1`

## `claude-sonnet-4-6`

- **工作目录（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-sonnet-4-6`
- **探针退出码**：1
- **summary 文件（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-sonnet-4-6/run_summary.jsonl`


| input_tokens | max_tokens | samples | n_ok | n_fail | RPM       | TPM  | mean_ttft_s | mean_tps | TOS object key（逐请求 JSONL，该 case 全部行）                                                                                       |
| ------------ | ---------- | ------- | ---- | ------ | --------- | ---- | ----------- | -------- | --------------------------------------------------------------------------------------------------------------------------- |
| 1500         | 7          | 1000    | 0    | 1000   | 3333.7327 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-sonnet-4-6/run/cells/claude-sonnet-4-6__in1500__routesingle.jsonl`   |
| 15000        | 75         | 500     | 0    | 500    | 2768.6221 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-sonnet-4-6/run/cells/claude-sonnet-4-6__in15000__routesingle.jsonl`  |
| 150000       | 750        | 100     | 0    | 100    | 2383.2388 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-sonnet-4-6/run/cells/claude-sonnet-4-6__in150000__routesingle.jsonl` |


失败摘要：

- input=1500: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.337962 (r:1000`
- input=15000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.337962 (r:500`
- input=150000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.337962 (r:100`

## `gemini-3-flash-preview`

- **工作目录（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3-flash-preview`
- **探针退出码**：1
- **summary 文件（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3-flash-preview/run_summary.jsonl`


| input_tokens | max_tokens | samples | n_ok | n_fail | RPM       | TPM  | mean_ttft_s | mean_tps | TOS object key（逐请求 JSONL，该 case 全部行）                                                                                       |
| ------------ | ---------- | ------- | ---- | ------ | --------- | ---- | ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1500         | 7          | 1000    | 0    | 1000   | 3405.7064 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3-flash-preview/run/cells/gemini-3-flash-preview__in1500__routesingle.jsonl`   |
| 15000        | 75         | 500     | 0    | 500    | 2957.9024 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3-flash-preview/run/cells/gemini-3-flash-preview__in15000__routesingle.jsonl`  |
| 150000       | 750        | 100     | 0    | 100    | 3938.8528 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3-flash-preview/run/cells/gemini-3-flash-preview__in150000__routesingle.jsonl` |


失败摘要：

- input=1500: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:737; PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.337962 (r:263`
- input=15000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:500`
- input=150000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:100`

## `gemini-3.1-pro-preview`

- **工作目录（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3.1-pro-preview`
- **探针退出码**：1
- **summary 文件（TOS）**：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3.1-pro-preview/run_summary.jsonl`


| input_tokens | max_tokens | samples | n_ok | n_fail | RPM       | TPM  | mean_ttft_s | mean_tps | TOS object key（逐请求 JSONL，该 case 全部行）                                                                                       |
| ------------ | ---------- | ------- | ---- | ------ | --------- | ---- | ----------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 1500         | 7          | 1000    | 0    | 1000   | 3191.3012 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3.1-pro-preview/run/cells/gemini-3.1-pro-preview__in1500__routesingle.jsonl`   |
| 15000        | 75         | 500     | 0    | 500    | 2863.6088 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3.1-pro-preview/run/cells/gemini-3.1-pro-preview__in15000__routesingle.jsonl`  |
| 150000       | 750        | 100     | 0    | 100    | 3037.9313 | null | null        | null     | `llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/gemini-3.1-pro-preview/run/cells/gemini-3.1-pro-preview__in150000__routesingle.jsonl` |


失败摘要：

- input=1500: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:1000`
- input=15000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:500`
- input=150000: `PermissionDeniedError: Error code: 403 - {'error': {'message': 'user quota insufficient, remaining quota: ＄-54.422158 (r:100`

---

## 分步重跑（策略与 `claude-sonnet-4-6` 仅 input=1500）

**背景**：四模型 × 三档一次跑满时容易触发网关侧配额/速率限制；后续改为 **一次只跑一个模型的一个 input 档**，跑完再合并进本文档。

**脚本能力（仓库已更新）**：

- `scripts/run_per_model_token_profiles_to_md.py`：新增 `--input-tokens`（例如仅 `1500`）；可选 `--no-abort-on-429` 传给探针（默认不传：遇 429 即停）。
- `scripts/dual_route_stream_profile_probe.py`：默认在同 cell 内 **首次出现 429 / 上游限流**（含「负载已饱和」类文案）时 **立即中止**（取消同档未完成的并发请求），**进程退出码 3**，**不做 sleep、不做自动重试**；由你判断何时再次执行脚本。若需旧行为「尽量跑满样本」可传 **`--no-abort-on-429`**。

**下一步目标**：`claude-opus-4-6` 已在上方全量批次中跑完，**不再重跑**；当前分步任务为 **`claude-sonnet-4-6`、仅 `input_tokens=1500`、样本数与全量一致 `1500:1000`**，并发略降为 **40**；遇 **429** 时脚本会立刻退出，便于你择机重跑。

**在目标机执行（须让 nohup 子进程继承 Key）**：SSH 非交互会话通常 **不会** 自动带上你在图形终端里 export 的变量；请在 **`ubuntu@18.183.174.245` 上已确认 `NEWAPI_API_KEY` 已 export 的交互 shell** 中执行（或显式写在 `nohup env NEWAPI_API_KEY=…` 中，**勿提交仓库、勿贴聊天**）：

```bash
cd ~/llm_gateways
# 确认：test -n "$NEWAPI_API_KEY" && echo key_ok
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
ROOT=/tmp/per_model_token_seq_sonnet_in1500_${STAMP}
MD=${ROOT}_brief.md
nohup env PYTHONUNBUFFERED=1 \
  ./.venv/bin/python scripts/run_per_model_token_profiles_to_md.py \
  --models claude-sonnet-4-6 \
  --input-tokens 1500 \
  --samples-by-input 1500:1000 \
  --intra-route-concurrency 40 \
  --markdown-out "$MD" \
  --output-dir "$ROOT" \
  --host-note "ubuntu@18.183.174.245; sequential sonnet in=1500 only" \
  >"${MD%.md}.out" 2>&1 &
echo "log: ${MD%.md}.out  brief: $MD  root: $ROOT"
```

**自动化尝试记录（Agent）**：曾于 2026-05-09 通过 SSH 启动上述 nohup，因非交互环境未加载到 `NEWAPI_API_KEY`，`*.out` 首行即为「请设置 NEWAPI_API_KEY」并退出，**未产生有效 `ROOT` 数据**；你本地按上式跑通后，请将 **`$MD` 中的 `claude-sonnet-4-6` 表格** 复制追加到本节下方（或 `scp` 该 md 到本仓库后再合并）。

**占位（跑完后替换）**：_（在此粘贴新批次的表格行与 `run_summary.jsonl` / `run/cells/...jsonl` 路径）_

---

## 火山引擎 TOS 归档（本批次日志与 JSONL）

**状态**：本批次数据已按 [PutObject](https://www.volcengine.com/docs/6349/74860?lang=zh) 写入 TOS；仓库内 **`tos_staging/` 已删除**，勿再依赖该本地目录。

- **对象键前缀**（上传时 `--key-prefix`；桶名以控制台为准）：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/`
- **nohup 标准输出日志**（与上传时 `--extra-file` 的文件名一致）：`llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/per_model_token_md_nohup_20260509T063432Z_brief.out`
- **服务器侧原始路径**（仅溯源；远端 `/tmp` 可能已清理）：`/tmp/per_model_token_md_nohup_20260509T063432Z`、`_brief.out` 见上文「批次根目录」。

正文各表「TOS object key」列与 **工作目录（TOS）** / **summary 文件（TOS）** 均为上述前缀下的完整 object key。取回对象可在控制台下载，或使用 Python SDK 的 **GetObject**（参见 [普通上传](https://www.volcengine.com/docs/6349/92800?lang=zh) 同文档树中的下载说明）。

### 公网 URL（虚拟主机访问）

与 [PutObject](https://www.volcengine.com/docs/6349/74860?lang=zh) 写入的 object 对应，在控制台为该桶展示的 **默认外网 Endpoint（虚拟主机风格）** 下，公网直链一般为：

`https://<桶名>.tos-cn-<地域>.volces.com/<object-key>`

其中 `<object-key>` 为正文中的完整 TOS object key（含 `llm_gateways/...` 整段，**不要**去掉前缀；路径中的 `/` 保留）。`<桶名>`、`tos-cn-<地域>.volces.com` **以控制台「桶详情 → 访问域名」为准**（各地域不同，不限于 `beijing`）；若控制台给出的是完整 host（含 CDN/自定义域），则用 `https://<控制台 host>/<object-key>`。

**示例**（将 `YOUR_BUCKET` 换成你的桶名，将 host 换成控制台实际域名；以下为北京地域默认域名的写法示例）：

- nohup 日志：  
  `https://YOUR_BUCKET.tos-cn-beijing.volces.com/llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/per_model_token_md_nohup_20260509T063432Z_brief.out`
- `claude-opus-4-6`、input=1500 逐请求 JSONL：  
  `https://YOUR_BUCKET.tos-cn-beijing.volces.com/llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run/cells/claude-opus-4-6__in1500__routesingle.jsonl`
- 同模型 `run_summary.jsonl`：  
  `https://YOUR_BUCKET.tos-cn-beijing.volces.com/llm_gateways/batches/per_model_token_md_nohup_20260509T063432Z/claude-opus-4-6/run_summary.jsonl`

若浏览器或 `curl` 返回 **403**，多为桶/对象为私有：请在控制台为该对象配置 **公共读**、桶策略放行匿名 **GetObject**，或改用控制台「文件预览 / 临时外链」与 SDK **预签名 URL**（见 [对象存储文档中心](https://www.volcengine.com/docs/6349/74820?lang=zh) 内权限与访问相关章节）。

**若需再次从服务器拉取到本机**（与 TOS 无关，自行替换 SSH 目标）：

```bash
mkdir -p ./local_backup/per_model_token_md_nohup_20260509T063432Z
scp -r ubuntu@18.183.174.245:/tmp/per_model_token_md_nohup_20260509T063432Z/. \
  ./local_backup/per_model_token_md_nohup_20260509T063432Z/
scp ubuntu@18.183.174.245:/tmp/per_model_token_md_nohup_20260509T063432Z_brief.out \
  ./local_backup/
```

**若需向 TOS 重新上传**（新桶或新前缀）：仍可用 **`scripts/tos_upload_local_tree.py`**，配置 `TOS_*` 环境变量后执行 `uv sync --extra tos` 与 `uv run --extra tos python scripts/tos_upload_local_tree.py ...`（勿将含密钥的 `.env` 提交仓库）。


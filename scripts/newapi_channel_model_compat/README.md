# NewAPI 渠道模型 OpenAI / Anthropic 兼容测试

对已**启用**的渠道，读取渠道配置的模型列表，对每个模型调用管理端 **`GET /api/channel/test/:id`**（与控制台「测试」同源实现），并分别传入 **`endpoint_type=openai`** 与 **`endpoint_type=anthropic`**，用于探测该渠道在该模型下两种中继格式是否可用。

## 与仓库根目录 `test_chat.py` 的区别

| | 本脚本 | `test_chat.py` |
|---|--------|----------------|
| 鉴权 | 管理员（Cookie 或 Token） | 用户 API Key |
| 请求路径 | `/api/channel/test/:id` | `/v1/chat/completions` 或 `/v1/messages` |
| 是否指定渠道 | 是（URL 中的渠道 id） | 否（由网关按模型与优先级路由） |

若同一模型名对应多条渠道，仅用用户 Key 测试无法保证命中某一条渠道；本脚本可逐渠道验证。

## 环境变量

| 变量 | 说明 |
|------|------|
| `NEWAPI_BASE_URL` | 根地址，如 `https://example.com`（不要末尾 `/`） |
| `NEWAPI_ADMIN_USERNAME` / `NEWAPI_ADMIN_PASSWORD` | 管理员账号密码（登录取 Cookie） |
| 或 `NEWAPI_ADMIN_TOKEN` + `NEWAPI_ADMIN_USER_ID` | 管理端 Bearer + `New-Api-User` |

## 安装

```bash
cd scripts/newapi_channel_model_compat
pip install -r requirements.txt
```

## 示例

```bash
export NEWAPI_BASE_URL=https://your-newapi.example.com
export NEWAPI_ADMIN_USERNAME=admin
export NEWAPI_ADMIN_PASSWORD='你的密码'

# 先小范围试跑（单渠道、每渠道最多 2 个模型）
python test_channel_models_compat.py --channel-ids 2 --max-models 2 --sleep 0.5

# 全量已启用渠道（耗时长、产生上游调用费用）
python test_channel_models_compat.py --sleep 0.3 --json-out /tmp/compat.json

# 只测 Anthropic 格式
python test_channel_models_compat.py --only anthropic --channel-ids 1
```

## 行为说明

- 渠道列表：`GET /api/channel/?status=enabled&p=...&page_size=...`（单页最多 100 条，与 NewAPI 一致）。
- 与上游一致，以下渠道类型**不支持**管理端 test，整渠道跳过：Midjourney、MidjourneyPlus、Suno、Kling、Jimeng、Vidu、DoubaoVideo。
- 模型名为空时，渠道未配置模型则对每个 endpoint **各测一次**不带 `model` 参数（由服务端选用默认/首个模型）。
- 非对话类模型（embedding、生图等）在 `anthropic` 下失败属常见情况，需结合业务解读。
- NewAPI 版本需支持 `TestChannel` 的 `endpoint_type` 查询参数；过旧版本可能行为不一致。

## 退出码

- `0`：已执行的探测均 `success`，且未使用 `--strict` 或不存在因类型跳过的渠道。
- `1`：任一探测失败，或 `--strict` 且存在因类型跳过的渠道。

---

## 用户 Key 逐模型全量验证（`run_per_model_user_gateway_validation.py`）

对已确认在管理端「OpenAI + Anthropic」探测均通过的模型，使用**用户 API Key**经网关依次执行：`test_chat.py`（openai / anthropic）、usage 采样、`rpm_until_limit`（heavy，峰值并发 16）、`rpm_minute_window_probe`（batch + minimal，256×4096）。与上文本脚本的差别：走 **`/v1/chat/completions` 与 `/v1/messages`**，不按渠道 ID 调用管理端 test。

**费用与耗时**：默认 **10 个模型**，每模型约 **31 + 4096** 次压力请求（另加若干次连通性调用），总调用量可达 **4 万+** 次量级；务必确认预算与配额。

**环境**（仓库根目录、已安装 `openai` / `anthropic` / `tiktoken` 的 Python 环境）：

```bash
export NEWAPI_API_KEY='...'   # 勿提交仓库、勿贴聊天
export NEWAPI_BASE_URL=https://llm.sxwl.ai/v1   # 可选，脚本有默认

# 仅打印将执行的命令，不写 docs、不写 summary
python scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py --dry-run

# 全量（自定义日志根目录，便于从跳板机 scp 拉回）
python scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py \
  --output-dir /tmp/sxwl_per_model_run

# 子集模型
python scripts/newapi_channel_model_compat/run_per_model_user_gateway_validation.py \
  --models glm-5.1,hunyuan-pro \
  --output-dir /tmp/sxwl_subset
```

**在远端执行（示例）**：先 `rsync` 本仓到目标机 `~/llm_gateways`，再经你环境中的 `ssh gateway` / `ssh -J gateway ...` 登录到能访问 `llm.sxwl.ai` 的机器，在远端 `cd ~/llm_gateways && source .venv/bin/activate`，设置 `NEWAPI_API_KEY` 后运行同上命令。原始日志在 `--output-dir` 下按模型分子目录；Markdown 默认写入仓库 `docs/newapi-sxwl-per-model-validation-<本地日期>.md`（可用 `--report` 覆盖）。

**可选**：`--skip-heavy` / `--skip-minute` 跳过对应压力段；`--continue-on-error` 在某步失败后仍尝试后续步骤。

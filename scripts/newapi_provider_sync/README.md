# NewAPI 多渠道：官网模型目录 + 导入脚本

## 文件说明

| 文件 | 作用 |
|------|------|
| `vendor_models_official_catalog.json` | 各厂商**官网文档链接**、`model_id`、`release_rank`、定价摘录或说明（**不**引用仓库内其它价格 JSON）。 |
| `import_channels.py` | 管理员登录后按目录创建渠道（`POST /api/channel/`）；可选 `--update-channels` 对已存在同名渠道 `GET`+`PUT /api/channel/` 同步 `models`/`base_url`/`type` 等；倍率见脚本 `--help`。 |
| `requirements.txt` | 仅依赖 `requests`（与 `newapi_batch_accounts` 一致）。 |

## 环境变量

### NewAPI 管理员（必填，除非使用 `--offline`）

| 变量 | 说明 |
|------|------|
| `NEWAPI_BASE_URL` | 根地址，如 `https://llm.sxwl.ai`（不要末尾 `/`） |
| `NEWAPI_ADMIN_USERNAME` | 管理员用户名 |
| `NEWAPI_ADMIN_PASSWORD` | 管理员密码 |

### 各上游密钥（缺一则跳过该厂商「新建」渠道；`--update-channels` 时仍可更新模型列表，仅在不改 key 时不必设）

| 厂商 | 变量 |
|------|------|
| MiniMax | `MINIMAX_API_KEY` |
| 月之暗面 | `MOONSHOT_API_KEY` |
| 智谱 | `ZHIPU_API_KEY` |
| 阶跃星辰 | `STEPFUN_API_KEY` |
| 火山方舟 | `VOLCENGINE_ARK_API_KEY`（即控制台 API Key，形如 `ark-...`） |
| 阿里云百炼 | `DASHSCOPE_API_KEY` |
| 百度千帆 | `BAIDU_QIANFAN_API_KEY`（如 `bce-v3/ALTAK-...` 整串） |
| 腾讯混元 | `TENCENT_HUNYUAN_KEY`，格式 **`AppId|SecretId|SecretKey`** 三段竖线分隔；若无独立 AppId，可尝试 **`0|SecretId|SecretKey`**（以腾讯云控制台与 NewAPI 版本为准，见 [NewAPI `parseTencentConfig`](https://github.com/QuantumNous/new-api/blob/main/relay/channel/tencent/relay-tencent.go)） |
| 硅基流动 | `SILICONFLOW_API_KEY` |

也可不设 `TENCENT_HUNYUAN_KEY`，改为分别设置 `TENCENT_APP_ID`、`TENCENT_SECRET_ID`、`TENCENT_SECRET_KEY`（脚本会拼为 `AppId|SecretId|SecretKey`）。

## 命令示例

```bash
cd scripts/newapi_provider_sync
pip install -r requirements.txt

# 不连网、不登录：查看将提交的渠道 JSON（打印时密钥一律占位，避免泄露）
python import_channels.py --offline

# 登录后 dry-run（打印真实请求体，不创建）
export NEWAPI_BASE_URL=https://llm.sxwl.ai
export NEWAPI_ADMIN_USERNAME=admin
export NEWAPI_ADMIN_PASSWORD='你的密码'
export MINIMAX_API_KEY=sk-...
# … 其它厂商按需 export …
python import_channels.py --dry-run

# 实际创建（已存在同名渠道则跳过，除非加 --force）
python import_channels.py

# 已存在同名渠道时：同步目录中的 models/base_url/type（先跑倍率再更新渠道；未 export 上游 key 则不改线上密钥）
python import_channels.py --update-channels
python import_channels.py --dry-run --update-channels
```

说明：`--force` 仍会尝试对已存在名再 `POST`（易失败），与「更新」场景一般二选一；`--update-channels` 使用 `PUT /api/channel/` 且以 `GET /api/channel/:id` 全量为基底合并，避免清空 `channel_info` 等字段。

## 与 NewAPI 版本的约定

- 渠道 `type` 与默认 `base_url` 对齐 [QuantumNous/new-api `constant/channel.go`](https://github.com/QuantumNous/new-api/blob/main/constant/channel.go)。
- **阶跃星辰**使用 `ChannelTypeCustom`（8），`default_base_url` 为完整 OpenAI 兼容路径 `https://api.stepfun.com/v1/chat/completions`（Custom 适配器将 `base_url` 视为**完整请求 URL**）。
- 模型名、价目以各厂商**当前官网**为准；导入前请用 `--offline` 核对 `model_id`，必要时直接改 JSON 中的 `models` / `release_rank`。

## 导入后验证

在仓库根目录使用 `test_chat.py`，将 `--base-url` 指向 `https://llm.sxwl.ai/v1`（或你的网关对外地址），`--models` 与目录中 `model_id` 一致。

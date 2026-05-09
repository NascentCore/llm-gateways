# 双路线 Token 剖面 — 简要报告

**说明**：本次在 `ubuntu@18.183.174.245` 上实际执行了探针与报告生成；因主机未配置有效 `NEWAPI_API_KEY` 时使用了**占位密钥**，网关返回 **401 invalid token**，故下表 **n_ok=0**，TPM/TTFT/TPS 为空。**不代表**四模型真实性能。配置有效密钥后，用文末「一键重跑」命令即可得到可归档的完整矩阵（四模型 × 三档输入 × 双路线）。

- **执行主机**：`ubuntu@18.183.174.245`
- **输出目录**：`/tmp`
- **run stem**：`dual_profile_run_20260509T055346Z`
- **manifest**：`/tmp/dual_profile_run_20260509T055346Z_manifest.json`
- **汇总 JSONL**：路线 A `/tmp/dual_profile_run_20260509T055346Z_A_summary.jsonl`；路线 B `/tmp/dual_profile_run_20260509T055346Z_B_summary.jsonl`
- **stdout 日志**：若使用 `nohup ... > /tmp/某文件.out`，该 `.out` 中含每 cell 的 JSON summary 行（与 `*_summary.jsonl` 重复时可任选其一归档）

## 指标说明

每行 summary 与探针 stdout 一致：**RPM**=该 cell 请求数/墙钟×60；**TPM**=Σ`usage.total_tokens`/墙钟×60；**TTFT** 为 mean/p50/p95；**TPS** 为输出阶段吞吐（见探针 `--help`）。

## 分 case 结果与原始请求数据位置

下表中 **原始数据路径** 为该 case 下**全部逐请求 JSONL**（每行一次 HTTP）；`nested` 布局下一 case 对应独立文件；`flat` 布局下多 case 共用同一文件，可按 `jq 'select(.model==... and .input_tokens_target==...)'` 过滤。

### 路线 A

| route | model | input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始数据（全部请求） |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A | `gemini-3-flash-preview` | 1500 | 7 | 1 | 0 | 1 | 96.7444 | null | null | null | `/tmp/dual_profile_run_20260509T055346Z_route_A/cells/gemini-3-flash-preview__in1500__routeA.jsonl` |

### 路线 B

| route | model | input_tokens | max_tokens | samples | n_ok | n_fail | RPM | TPM | mean_ttft_s | mean_tps | 原始数据（全部请求） |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| B | `gemini-3-flash-preview` | 1500 | 7 | 1 | 0 | 1 | 95.7679 | null | null | null | `/tmp/dual_profile_run_20260509T055346Z_route_B/cells/gemini-3-flash-preview__in1500__routeB.jsonl` |

## 附属文件

- `cells/` 目录（nested）：`/tmp/dual_profile_run_20260509T055346Z_route_A/cells/` 与 `..._route_B/cells/`

## 原始逐请求 JSONL 命名规则（`--jsonl-layout nested`）

每个 **case** = `路线 × 模型 × 输入档`。文件路径为：

`{output_dir}/{stem}_route_{A|B}/cells/{model_safe}__in{input_tokens}__route{A|B}.jsonl`

其中 `model_safe` 为模型名中的 `/`、`:`、空格等替换为 `_` 后的形式。该文件内 **每一行** 为一次请求的完整记录（成功时含 `usage`、`output_text` 等；失败时含 `error`）。

**本次 smoke 仅含 1 个模型 × 1 档输入**，故 A/B 各 1 个 cell 文件。完整四模型 × `1500,15000,150000` 时，每条约 **4×3=12** 个 cell 文件/路线（共 24 个 cell 文件，双路线并行时 A、B 各写一套相同模型矩阵）。

## 附录：原始数据行示例（路线 A，401）

以下为 `/tmp/dual_profile_run_20260509T055346Z_route_A/cells/gemini-3-flash-preview__in1500__routeA.jsonl` 中唯一一行（格式化仅便于阅读，磁盘上为单行 JSON）：

```json
{
  "ts": "2026-05-09T05:53:48Z",
  "route_id": "A",
  "i": 1,
  "model": "gemini-3-flash-preview",
  "input_tokens_target": 1500,
  "max_tokens": 7,
  "ok": false,
  "ttft_s": null,
  "total_s": 0.619916,
  "usage": null,
  "output_text": "",
  "error": "AuthenticationError: Error code: 401 - …"
}
```

## 一键重跑（四模型 × 三档输入 × 双路线 + 本报告）

在主机上已 `export NEWAPI_BASE_URL`、`NEWAPI_API_KEY` 后执行（`STEM` 可改；`150000` 档成本高，请先保守样本）：

```bash
cd ~/llm_gateways
STEM=dual_profile_full_$(date -u +%Y%m%dT%H%M%SZ)
set +e
.venv/bin/python scripts/dual_route_stream_profile_probe.py \
  --dual-mode subprocess \
  --jsonl-layout nested \
  --emit-summary-jsonl \
  --output-dir /tmp \
  --output-stem "$STEM" \
  --samples-by-input "1500:5,15000:3,150000:1" \
  --intra-route-concurrency 2 \
  --stream-timeout 3600 \
  >"/tmp/${STEM}.out" 2>&1
set -e
.venv/bin/python scripts/generate_dual_profile_report.py \
  --output-dir /tmp \
  --stem "$STEM" \
  --markdown-out "/tmp/${STEM}_brief.md" \
  --host "ubuntu@18.183.174.245"
```

完成后：`/tmp/${STEM}_brief.md` 即新的简要报告；每个 case 的原始请求仍在 `/tmp/${STEM}_route_A/cells/` 与 `_route_B/cells/` 下按上表规则命名。

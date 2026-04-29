#!/usr/bin/env bash
# 从仓库 benchmark/ 目录执行：仅打包 NewAPI 栈（无 mock/locust），适合生产或轻量网关部署
set -euo pipefail
BENCH="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$BENCH"

OUT="volc-newapi-only-$(date +%Y%m%d_%H%M%S).tar.gz"

tar czvf "$OUT" \
  --exclude='volc-standalone/.env' \
  --exclude='volc-standalone/data' \
  --exclude='volc-standalone/logs' \
  --exclude='volc-standalone/nginx/active.conf' \
  --exclude='volc-standalone/certbot/conf/archive' \
  --exclude='volc-standalone/certbot/conf/live' \
  --exclude='volc-standalone/certbot/conf/renewal' \
  --exclude='volc-standalone/certbot/conf/*.pem' \
  --exclude='__pycache__' \
  --exclude='.DS_Store' \
  VOLC_STANDALONE.md volc-standalone

echo ""
echo "已生成: $BENCH/$OUT"
echo "解压后仅含 volc-standalone/ 与 VOLC_STANDALONE.md；无需同级 mock/ 目录即可 docker compose up。"

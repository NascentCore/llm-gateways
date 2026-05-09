#!/usr/bin/env bash
# 轮询远端 nohup 跑批直至 brief.md 生成或进程消失；stdout 每轮一行摘要。
set -uo pipefail
HOST="${1:-ubuntu@18.183.174.245}"
STEM="${2:-per_model_token_md_nohup_20260509T063432Z}"
INTERVAL="${3:-120}"
MAX_ROUNDS="${4:-240}"
ROOT="/tmp/${STEM}"
PIDFILE="${ROOT}.pid"
LOG="${ROOT}_brief.out"
MD="${ROOT}_brief.md"
for i in $(seq 1 "$MAX_ROUNDS"); do
  # 路径在本地展开后注入远端；勿在远端单引号内写 '$LOG'（会按字面文件名 $LOG 导致 wc 报错）。
  msg=$(ssh -o BatchMode=yes -o ConnectTimeout=30 "$HOST" bash -lc "
set -euo pipefail
PIDFILE=\"$PIDFILE\"
LOG=\"$LOG\"
MD=\"$MD\"
if ! test -f \"\$PIDFILE\"; then echo 'NO_PIDFILE'; exit 0; fi
PID=\$(cat \"\$PIDFILE\")
if kill -0 \"\$PID\" 2>/dev/null; then
  echo \"RUNNING pid=\$PID lines=\$(wc -l < \"\$LOG\" 2>/dev/null || echo 0)\"
  tail -1 \"\$LOG\" 2>/dev/null | cut -c1-140 || true
  exit 1
fi
if test -f \"\$MD\"; then echo 'DONE'; wc -l \"\$MD\"; exit 0; fi
if grep -q '^wrote ' \"\$LOG\" 2>/dev/null; then echo 'DONE_LOG'; exit 0; fi
echo 'STOPPED_NO_MD'
tail -25 \"\$LOG\" || true
exit 2
") || true
  ec=$?
  echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] round=$i ec=$ec $msg"
  if echo "$msg" | grep -q '^DONE'; then echo ALL_DONE; exit 0; fi
  if echo "$msg" | grep -q '^NO_PIDFILE'; then echo MISSING_PIDFILE; exit 4; fi
  if echo "$msg" | grep -q '^STOPPED_NO_MD'; then echo ABNORMAL_STOP; exit 3; fi
  sleep "$INTERVAL"
done
echo POLL_TIMEOUT
exit 5

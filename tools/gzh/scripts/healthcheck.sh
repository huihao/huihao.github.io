#!/usr/bin/env bash
# 健康检查：供监控/巡检调用，异常时以非 0 退出码告警。
#
#   ./scripts/healthcheck.sh
#
# 检查项：
#   1. 调度进程是否存活（pid 文件）
#   2. 最近一次执行的状态与时间
#   3. 是否存在失败的文章
#   4. 磁盘可用空间
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname -- "$SCRIPT_DIR")"
export PYTHONPATH="${PROJECT_ROOT}/src:${PYTHONPATH:-}"
export GZH_DB="${PROJECT_ROOT}/var/state.db"

PYTHON="${GZH_PYTHON:-python3}"
MIN_FREE_MB="${GZH_MIN_FREE_MB:-512}"

problems=0

echo "== gzh 健康检查 $(date -Iseconds) =="

# 1. 调度进程
if [[ -f "${PROJECT_ROOT}/var/scheduler.pid" ]]; then
  PID="$(cat "${PROJECT_ROOT}/var/scheduler.pid")"
  if kill -0 "${PID}" 2>/dev/null; then
    echo "  [OK]   调度进程存活 (pid=${PID})"
  else
    echo "  [FAIL] 调度进程不存在 (pid=${PID})"
    problems=$((problems + 1))
  fi
else
  echo "  [WARN] 未找到 pid 文件（调度器可能未以 daemon 方式运行）"
fi

# 2. 最近一次执行
RECENT="$(${PYTHON} - <<'PY'
import json
import os
import sqlite3

try:
    conn = sqlite3.connect(os.environ.get("GZH_DB", "var/state.db"))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT status, started_at, published, failed, error FROM runs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    print(json.dumps(dict(row) if row else {}, ensure_ascii=False))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({"error": str(exc)}, ensure_ascii=False))
PY
)"
echo "  最近一次执行: ${RECENT}"

# 3. 失败文章
FAILED="$(${PYTHON} - <<'PY'
import os
import sqlite3

try:
    conn = sqlite3.connect(os.environ.get("GZH_DB", "var/state.db"))
    n = conn.execute("SELECT COUNT(*) FROM articles WHERE status = 'failed'").fetchone()[0]
    print(n)
except Exception:  # noqa: BLE001
    print("?")
PY
)"
if [[ "${FAILED}" == "?" ]]; then
  echo "  [WARN] 无法统计失败文章"
elif [[ "${FAILED}" -gt 0 ]]; then
  echo "  [WARN] 存在 ${FAILED} 篇失败文章，请执行 gzh list --status failed 查看"
fi

# 4. 磁盘
FREE_MB="$(df -Pm "${PROJECT_ROOT}" | awk 'NR==2 {print $4}')"
if [[ "${FREE_MB}" -lt "${MIN_FREE_MB}" ]]; then
  echo "  [FAIL] 磁盘剩余 ${FREE_MB}MB，低于阈值 ${MIN_FREE_MB}MB"
  problems=$((problems + 1))
else
  echo "  [OK]   磁盘剩余 ${FREE_MB}MB"
fi

echo "== 检查完成，问题数: ${problems} =="
exit $((problems > 0 ? 1 : 0))

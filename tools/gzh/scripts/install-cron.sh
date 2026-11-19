#!/usr/bin/env bash
# 把 gzh 注册为 cron 任务（适合没有 systemd 的机器）。
#
#   ./scripts/install-cron.sh            # 安装默认任务
#   ./scripts/install-cron.sh --remove   # 卸载
#
# 默认任务：
#   * * * * *  每分钟检查一次排期（由调度器内部判断是否命中时刻）
#
# 注意：如果已经用 systemd 跑 gzh daemon，请不要再装 cron，避免重复发布。
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname -- "$SCRIPT_DIR")"
GZH_BIN="${PROJECT_ROOT}/bin/gzh"
MARKER="# gzh-scheduler"

if [[ ! -x "${GZH_BIN}" ]]; then
  chmod +x "${GZH_BIN}"
fi

# 移除已有条目
( crontab -l 2>/dev/null | grep -v "${MARKER}" ) | crontab - || true

if [[ "${1:-}" == "--remove" ]]; then
  echo "已移除 gzh 的 cron 任务"
  exit 0
fi

CRON_LINE="* * * * * cd ${PROJECT_ROOT} && ${GZH_BIN} run --once >> ${PROJECT_ROOT}/logs/cron.log 2>&1 ${MARKER}"

( crontab -l 2>/dev/null; echo "${CRON_LINE}" ) | crontab -

echo "已安装 cron 任务:"
echo "  ${CRON_LINE}"
echo
echo "查看: crontab -l"
echo "卸载: $0 --remove"

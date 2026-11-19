#!/usr/bin/env bash
# 备份配置与状态数据库。
#
#   ./scripts/backup.sh              # 备份到 ./backup/YYYYmmdd-HHMMSS
#   ./scripts/backup.sh /data/backup # 备份到指定目录
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname -- "$SCRIPT_DIR")"
TARGET_ROOT="${1:-${PROJECT_ROOT}/backup}"
STAMP="$(date +%Y%m%d-%H%M%S)"
TARGET="${TARGET_ROOT}/${STAMP}"

mkdir -p "${TARGET}"

# 1. 状态数据库（用 sqlite3 的在线备份，避免拷贝到写入中的文件）
if command -v sqlite3 >/dev/null 2>&1 && [[ -f "${PROJECT_ROOT}/var/state.db" ]]; then
  sqlite3 "${PROJECT_ROOT}/var/state.db" ".backup '${TARGET}/state.db'"
else
  # 没有 sqlite3 命令时退回到文件拷贝（需先停服务，否则可能不一致）
  cp "${PROJECT_ROOT}/var/state.db"* "${TARGET}/" 2>/dev/null || true
  echo "提示: 未找到 sqlite3 命令，数据库以文件方式拷贝（建议停服后再执行）"
fi

# 2. 配置（排除凭据文件）
mkdir -p "${TARGET}/config"
for file in "${PROJECT_ROOT}"/config/*.json; do
  [[ -e "$file" ]] && cp "$file" "${TARGET}/config/"
done

# 3. 清单
{
  echo "备份时间: $(date -Iseconds)"
  echo "项目根目录: ${PROJECT_ROOT}"
  echo "文件列表:"
  find "${TARGET}" -type f -printf '  %P (%s bytes)\n' | sort
} > "${TARGET}/MANIFEST.txt"

echo "备份完成: ${TARGET}"
echo "（凭据文件 .env 不在备份中，恢复时需重新注入）"

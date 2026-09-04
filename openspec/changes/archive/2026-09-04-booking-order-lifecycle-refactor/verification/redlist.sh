#!/usr/bin/env bash
# 采集 br-server 全量测试的红名单（FAILED + ERROR 测试 ID 集合）。
# 用法: bash redlist.sh <输出前缀>   例: bash redlist.sh redlist-baseline
# 退出码 0 表示采集成功；pytest 本身退出码非 0 属预期（存在既有红灯）。
set -uo pipefail

PREFIX="${1:?用法: redlist.sh <输出前缀>}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../../../.." && pwd)"
# 输出前缀解析为绝对路径（相对调用时 CWD），避免随后 cd 到 br-server 后写错位置
case "$PREFIX" in
  /*) OUT="$PREFIX" ;;
  *)  OUT="$(pwd)/$PREFIX" ;;
esac
PY=/opt/miniconda3/envs/booking-room/bin/python
LOG="$(mktemp -t redlog.XXXXXX)"

cd "$REPO_ROOT/br-server" || exit 2
"$PY" -m pytest tests/ -q --tb=no -p no:cacheprovider > "$LOG" 2>&1

grep -E '^(FAILED|ERROR) ' "$LOG" \
  | sed -E 's/^(FAILED|ERROR) //; s/ - .*$//' \
  | sort -u > "$OUT.txt"

# 采集时刻（Asia/Shanghai），供比对脚本判定挂钟桶
TZ=Asia/Shanghai date '+%Y-%m-%dT%H:%M:%S%z' > "$OUT.ts"

echo "--- pytest 汇总 ---"
tail -1 "$LOG"
echo "--- 采集时刻 ---"
cat "$OUT.ts"
echo "--- 红名单条目数 ---"
wc -l < "$OUT.txt"
rm -f "$LOG"

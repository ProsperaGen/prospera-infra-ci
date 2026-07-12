#!/bin/sh
# Prospera dev bootstrap — 冪等安裝 pre-execution 成本閘（core.hooksPath）。
# 讓「正確的路變成容易的路」：一步設好本機成本閘，覆蓋全機 git repo + 未來 clone。
# 用法：sh bootstrap-dev.sh   （可重跑，冪等）
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PY="$(command -v python 2>/dev/null || command -v python3 2>/dev/null)"
if [ -z "$PY" ]; then
  echo "[bootstrap] ✗ 找不到 python — 請先裝 Python 3.11+"; exit 1
fi
"$PY" "$DIR/install_hooks.py"
echo "[bootstrap] 完成。反安裝：git config --global --unset core.hooksPath"

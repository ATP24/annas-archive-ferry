#!/usr/bin/env bash
# ============================================================
#   [安娜书渡 / Anna's Archive Ferry] Linux & macOS 一键配置脚本
# ============================================================

set -e

echo "============================================================"
echo "  [安娜书渡 / Anna's Archive Ferry] 环境配置工具 (macOS/Linux)"
echo "============================================================"
echo ""

# Find python3
if command -v python3 >/dev/null 2>&1; then
    PY_BIN=python3
elif command -v python >/dev/null 2>&1; then
    PY_BIN=python
else
    echo "[-] 未检测到 Python 3，请先安装 Python 3.8 或以上版本。"
    exit 1
fi

echo "[*] 使用 Python 解释器: $($PY_BIN --version)"

echo "[*] 正在安装核心依赖库..."
$PY_BIN -m pip install -r "$(dirname "$0")/requirements.txt" || \
$PY_BIN -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r "$(dirname "$0")/requirements.txt" || \
$PY_BIN -m pip install --break-system-packages -r "$(dirname "$0")/requirements.txt"

# Ensure run.sh is executable
chmod +x "$(dirname "$0")/run.sh" 2>/dev/null || true

echo ""
echo "[*] 正在执行环境健康自检..."
$PY_BIN "$(dirname "$0")/scripts/ferry_engine.py" doctor

echo ""
echo "============================================================"
echo "  配置完成！你可以直接运行 ./run.sh 启动交互式控制台。"
echo "============================================================"

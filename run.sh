#!/usr/bin/env bash
# ============================================================
#   [安娜书渡 / Anna's Archive Ferry] Linux & macOS 独立控制台
# ============================================================

# Find python3
if command -v python3 >/dev/null 2>&1; then
    PY_BIN=python3
else
    PY_BIN=python
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

while true; do
    clear
    echo "============================================================"
    echo "     [安娜书渡 / Anna's Archive Ferry] 独立控制台"
    echo "============================================================"
    echo ""
    echo "  [1] 检索书籍并选择下载"
    echo "  [2] 直接输入 MD5 码下载"
    echo "  [3] 执行环境自检 (Doctor)"
    echo "  [4] 打开下载保存目录"
    echo "  [0] 退出"
    echo ""
    echo "============================================================"
    read -p "请选择操作编号 [0-4]: " opt

    case "$opt" in
        1)
            clear
            echo "============================================================"
            echo "  【检索书籍】"
            echo "============================================================"
            read -p "请输入书名、作者或关键词: " q
            if [ -n "$q" ]; then
                $PY_BIN "$SCRIPT_DIR/scripts/ferry_engine.py" search "$q" --limit 8
                echo ""
                read -p "请输入要下载的书籍 MD5 码 (直接回车返回): " choice
                if [ -n "$choice" ]; then
                    $PY_BIN "$SCRIPT_DIR/scripts/ferry_engine.py" download --md5 "$choice"
                    read -p "按回车继续..."
                fi
            fi
            ;;
        2)
            clear
            echo "============================================================"
            echo "  【MD5 直连下载】"
            echo "============================================================"
            read -p "请输入安娜档案书籍 32 位 MD5 码: " md5code
            if [ -n "$md5code" ]; then
                $PY_BIN "$SCRIPT_DIR/scripts/ferry_engine.py" download --md5 "$md5code"
                read -p "按回车继续..."
            fi
            ;;
        3)
            clear
            $PY_BIN "$SCRIPT_DIR/scripts/ferry_engine.py" doctor
            read -p "按回车继续..."
            ;;
        4)
            DL_DIR="$HOME/Downloads/AnnasFerry"
            mkdir -p "$DL_DIR"
            if command -v open >/dev/null 2>&1; then
                open "$DL_DIR"
            elif command -v xdg-open >/dev/null 2>&1; then
                xdg-open "$DL_DIR"
            else
                echo "下载目录为: $DL_DIR"
            fi
            read -p "按回车继续..."
            ;;
        0)
            exit 0
            ;;
        *)
            ;;
    esac
done

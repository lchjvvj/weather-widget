#!/bin/bash
# ============================================================
# 天气桌面小工具 - 安装/卸载脚本
# 适用于 Deepin / UOS 桌面环境
# ============================================================
# 用法:
#   ./setup.sh          # 安装
#   ./setup.sh uninstall # 卸载
# ============================================================

set -e

APP_NAME="天气桌面小工具"
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
DESKTOP_FILE="$HOME/Desktop/天气小工具.desktop"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/weather-widget.desktop"
ICON_SRC="$APP_DIR/assets/icon.png"
ICON_DST="$HOME/.config/weather_widget_icon.png"
CONFIG_DIR="$HOME/.config/weather-widget"

# ============================================================
# 颜色定义
# ============================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_ok()   { echo -e "  ${GREEN}✅${NC} $1"; }
print_warn() { echo -e "  ${YELLOW}⚠️${NC} $1"; }
print_err()  { echo -e "  ${RED}❌${NC} $1"; }
print_info() { echo -e "  ${BLUE}ℹ️${NC} $1"; }

# ============================================================
# 卸载
# ============================================================
uninstall() {
    echo ""
    echo "=========================================="
    echo "  🗑️  $APP_NAME - 卸载"
    echo "=========================================="
    echo ""

    # 删除桌面快捷方式
    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        print_ok "已删除桌面快捷方式"
    else
        print_info "桌面快捷方式不存在，跳过"
    fi

    # 删除开机自启
    if [ -f "$AUTOSTART_FILE" ]; then
        rm -f "$AUTOSTART_FILE"
        print_ok "已删除开机自启配置"
    else
        print_info "开机自启配置不存在，跳过"
    fi

    # 删除图标
    if [ -f "$ICON_DST" ]; then
        rm -f "$ICON_DST"
        print_ok "已删除应用图标"
    fi

    # 可选：删除配置文件
    if [ -d "$CONFIG_DIR" ]; then
        echo ""
        echo -n "是否删除用户配置数据（城市列表、背景设置等）？(y/N): "
        read -r response
        if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
            rm -rf "$CONFIG_DIR"
            print_ok "已删除配置数据"
        else
            print_info "保留配置数据"
        fi
    fi

    echo ""
    echo "=========================================="
    echo -e "  ${GREEN}✅ 卸载完成！${NC}"
    echo "=========================================="
    echo ""
    exit 0
}

# ============================================================
# 安装
# ============================================================
install() {
    echo ""
    echo "=========================================="
    echo "  🌤️  $APP_NAME - 安装脚本"
    echo "=========================================="
    echo ""

    # ---- 检查 Python ----
    echo "📋 检查 Python 环境..."
    if ! command -v python3 &>/dev/null; then
        print_err "未找到 python3，请先安装 Python 3.8+"
        exit 1
    fi
    print_ok "Python: $(python3 --version 2>&1)"

    # ---- 检查 Tkinter ----
    echo "📋 检查 Tkinter..."
    if python3 -c "import tkinter" 2>/dev/null; then
        print_ok "Tkinter 已安装"
    else
        print_warn "Tkinter 未安装，尝试安装..."
        if command -v apt &>/dev/null; then
            sudo apt install -y python3-tk || {
                print_err "Tkinter 安装失败，请手动安装: sudo apt install python3-tk"
                exit 1
            }
            print_ok "Tkinter 安装成功"
        else
            print_err "请手动安装: sudo apt install python3-tk"
            exit 1
        fi
    fi

    # ---- 安装 Python 依赖 ----
    echo "📦 安装 Python 依赖..."
    if [ -f "$APP_DIR/requirements.txt" ]; then
        if pip3 install -r "$APP_DIR/requirements.txt" 2>/dev/null; then
            print_ok "Python 依赖安装成功"
        else
            print_warn "Pillow 安装失败（不影响基本功能，仅背景图不可用）"
            print_info "可手动安装: pip3 install Pillow"
        fi
    else
        print_info "无依赖文件，跳过"
    fi

    # ---- 创建桌面快捷方式 ----
    echo "📌 创建桌面快捷方式..."
    mkdir -p "$(dirname "$DESKTOP_FILE")"
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=天气小工具
Comment=多城市桌面天气小工具 - 实时天气、3天预报
Exec=python3 $APP_DIR/src/main.py
Icon=$ICON_DST
Terminal=false
Categories=Utility;Weather;
StartupNotify=true
EOF
    chmod +x "$DESKTOP_FILE"
    print_ok "桌面快捷方式: $DESKTOP_FILE"

    # ---- 创建开机自启 ----
    echo "🔄 配置开机自启..."
    mkdir -p "$AUTOSTART_DIR"
    cat > "$AUTOSTART_FILE" << EOF
[Desktop Entry]
Type=Application
Name=天气小工具
Comment=多城市桌面天气小工具
Exec=python3 $APP_DIR/src/main.py
Icon=$ICON_DST
Terminal=false
Categories=Utility;
X-GNOME-Autostart-enabled=true
X-GNOME-Autostart-Delay=10
EOF
    print_ok "开机自启: $AUTOSTART_FILE"

    # ---- 复制图标 ----
    if [ -f "$ICON_SRC" ]; then
        cp "$ICON_SRC" "$ICON_DST"
        print_ok "应用图标已安装"
    else
        print_info "未找到图标文件，使用默认图标"
    fi

    # ---- 验证安装 ----
    echo ""
    echo "🔍 验证安装..."
    if python3 -c "import sys; sys.path.insert(0, '$APP_DIR'); from src.weather_ui import WeatherWidget; print('OK')" 2>/dev/null; then
        print_ok "模块导入验证通过"
    else
        print_warn "模块导入验证失败（运行时可能仍可正常工作）"
    fi

    echo ""
    echo "=========================================="
    echo -e "  ${GREEN}✅ 安装完成！${NC}"
    echo "=========================================="
    echo ""
    echo "启动方式:"
    echo "  1. 双击桌面图标「天气小工具」"
    echo "  2. 命令行: python3 $APP_DIR/src/main.py"
    echo ""
    echo "卸载方式:"
    echo "  ./setup.sh uninstall"
    echo ""
    echo "项目目录: $APP_DIR"
    echo "配置目录: $CONFIG_DIR"
    echo "=========================================="
}

# ============================================================
# 主流程
# ============================================================
case "${1:-install}" in
    install)
        install
        ;;
    uninstall|remove)
        uninstall
        ;;
    help|--help|-h)
        echo "用法: $0 [install|uninstall|help]"
        echo ""
        echo "  install     安装天气小工具（默认）"
        echo "  uninstall   卸载天气小工具"
        echo "  help        显示此帮助信息"
        ;;
    *)
        echo "未知参数: $1"
        echo "用法: $0 [install|uninstall|help]"
        exit 1
        ;;
esac

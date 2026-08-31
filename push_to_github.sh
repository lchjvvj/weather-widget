#!/bin/bash
# ============================================================
# 天气桌面小工具 - 推送到 GitHub 脚本
# ============================================================
# 使用方法:
#   1. 在 GitHub 上创建仓库: https://github.com/new
#      仓库名: weather-widget
#      描述: 多城市同屏天气桌面插件 - 实时天气+3天预报
#      不要勾选 README/.gitignore/LICENSE（已存在）
#   2. 运行本脚本，填入你的 GitHub 用户名
# ============================================================

set -e

echo "=========================================="
echo "  🌤️  天气桌面小工具 - 推送到 GitHub"
echo "=========================================="
echo ""

# 获取 GitHub 用户名
read -p "请输入你的 GitHub 用户名: " GITHUB_USER

if [ -z "$GITHUB_USER" ]; then
    echo "❌ 用户名不能为空"
    exit 1
fi

REPO_URL="https://github.com/${GITHUB_USER}/weather-widget.git"
REPO_SSH="git@github.com:${GITHUB_USER}/weather-widget.git"

echo ""
echo "选择推送方式:"
echo "  1) HTTPS（推荐，需要输入 GitHub 密码/Token）"
echo "  2) SSH（需要配置 SSH Key）"
read -p "请选择 [1/2]: " CHOICE

case "$CHOICE" in
    1)
        echo ""
        echo "📤 正在推送到: $REPO_URL"
        echo "⚠️  需要输入 GitHub 个人访问令牌（Token）"
        echo "   生成方法: GitHub → Settings → Developer settings → Personal access tokens"
        echo ""
        git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
        git push -u origin master
        ;;
    2)
        echo ""
        echo "📤 正在推送到: $REPO_SSH"
        git remote add origin "$REPO_SSH" 2>/dev/null || git remote set-url origin "$REPO_SSH"
        git push -u origin master
        ;;
    *)
        echo "❌ 无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "  ✅ 推送完成！"
echo "=========================================="
echo ""
echo "仓库地址: https://github.com/${GITHUB_USER}/weather-widget"
echo ""
echo "现在可以去 deepin 论坛发帖提交作品了！"
echo "  → https://bbs.deepin.org"
echo "  → 论坛资源 → AI专区 → AI 开发实验室"
echo "  标题格式: 【deepin插件开发活动】+作品名称"
echo "=========================================="

#!/bin/bash
# 大麦抢票 - 抢票启动脚本
# 使用方法: ./start_ticket_grabbing.sh
#
# 可通过环境变量自定义：
#   ANDROID_HOME / ANDROID_SDK_ROOT - Android SDK 根路径，默认 ~/Library/Android/sdk
#   APPIUM_PORT                     - Appium 监听端口，默认 4723
#   DAMAI_PYTHON                    - Python 解释器路径，默认按顺序探测 poetry / python3 / python

set -e

echo "🎫 启动大麦抢票脚本..."

DEFAULT_SDK="$HOME/Library/Android/sdk"
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$DEFAULT_SDK}}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
APPIUM_PORT="${APPIUM_PORT:-4723}"

# 检查Appium服务器是否运行
if ! curl -s "http://127.0.0.1:$APPIUM_PORT/status" > /dev/null; then
    echo "❌ Appium服务器未运行（端口 $APPIUM_PORT）"
    echo "   请先运行: ./start_appium.sh"
    exit 1
fi

echo "✅ Appium服务器运行正常"

# 检查配置文件
if [ ! -f "damai_appium/config.jsonc" ]; then
    echo "❌ 配置文件不存在: damai_appium/config.jsonc"
    exit 1
fi

echo "✅ 配置文件存在"

# 显示当前配置（敏感字段截断）
echo "📋 当前配置:"
grep -E '"keyword"|"city"|"users"' damai_appium/config.jsonc | head -3 | sed 's/^/   /'

# 确认是否继续
read -p "🤔 确认开始抢票？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 1
fi

cd damai_appium

echo "🚀 开始抢票..."
echo "   请确保："
echo "   1. 大麦APP已打开"
echo "   2. 已搜索到目标演出"
echo "   3. 已进入演出详情页面"
echo ""

# Python 解释器探测顺序：DAMAI_PYTHON 环境变量 → poetry run → python3 → python
if [ -n "$DAMAI_PYTHON" ] && command -v "$DAMAI_PYTHON" &> /dev/null; then
    "$DAMAI_PYTHON" damai_app_v2.py
elif command -v poetry &> /dev/null && poetry env info -p &> /dev/null; then
    poetry run python damai_app_v2.py
elif command -v python3 &> /dev/null; then
    python3 damai_app_v2.py
elif command -v python &> /dev/null; then
    python damai_app_v2.py
else
    echo "❌ 未找到 Python 解释器，请设置 DAMAI_PYTHON 环境变量"
    exit 1
fi

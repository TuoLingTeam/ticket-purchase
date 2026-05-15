#!/bin/bash
# 大麦抢票 - Appium启动脚本
# 使用方法: ./start_appium.sh
#
# 可通过环境变量自定义：
#   ANDROID_HOME / ANDROID_SDK_ROOT - Android SDK 根路径，默认 ~/Library/Android/sdk
#   APPIUM_PORT                     - Appium 监听端口，默认 4723

set -e

echo "🚀 启动大麦抢票环境..."

# Android SDK 路径：优先使用现有环境变量，否则用默认位置
DEFAULT_SDK="$HOME/Library/Android/sdk"
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$DEFAULT_SDK}}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
APPIUM_PORT="${APPIUM_PORT:-4723}"

if [ ! -d "$ANDROID_HOME" ]; then
    echo "❌ Android SDK 路径不存在: $ANDROID_HOME"
    echo "   请设置环境变量 ANDROID_HOME 指向你的 Android SDK 安装位置"
    exit 1
fi

ADB="$(command -v adb || echo "$ANDROID_HOME/platform-tools/adb")"
if [ ! -x "$ADB" ]; then
    echo "❌ 未找到 adb，请确认 Android Platform Tools 已安装"
    exit 1
fi

echo "✅ 环境变量已设置"
echo "   ANDROID_HOME: $ANDROID_HOME"
echo "   ADB: $ADB"

# 检查Node.js版本
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version | cut -d'v' -f2)
    echo "📦 Node.js版本: $NODE_VERSION"
else
    echo "❌ 未检测到 Node.js"
    exit 1
fi

# 检查Appium是否安装
if ! command -v appium &> /dev/null; then
    echo "❌ Appium未安装，请先安装Appium"
    echo "   运行: npm install -g appium"
    exit 1
fi

# 检查Android设备
echo "📱 检查Android设备..."
DEVICES=$("$ADB" devices | grep -c "device$" || true)
if [ "$DEVICES" -eq 0 ]; then
    echo "⚠️  未检测到Android设备"
    echo "   请启动模拟器或连接真机"
    exit 1
else
    echo "✅ 检测到 $DEVICES 个Android设备"
fi

# 检查大麦APP是否安装
if ! "$ADB" shell pm list packages | grep -q "cn.damai"; then
    echo "⚠️  大麦APP未安装"
    echo "   请在设备上安装大麦APP"
    exit 1
else
    echo "✅ 大麦APP已安装"
fi

# 启动Appium服务器
echo "🚀 启动Appium服务器..."
echo "   服务器地址: http://127.0.0.1:$APPIUM_PORT"
echo "   按 Ctrl+C 停止服务器"
echo ""

appium --port "$APPIUM_PORT"

#!/bin/bash
# 大麦抢票 - 环境检查脚本
# 使用方法: ./check_environment.sh
#
# 可通过环境变量自定义：
#   ANDROID_HOME / ANDROID_SDK_ROOT - Android SDK 根路径，默认 ~/Library/Android/sdk
#   APPIUM_PORT                     - Appium 监听端口，默认 4723

DEFAULT_SDK="$HOME/Library/Android/sdk"
export ANDROID_HOME="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-$DEFAULT_SDK}}"
export ANDROID_SDK_ROOT="${ANDROID_SDK_ROOT:-$ANDROID_HOME}"
APPIUM_PORT="${APPIUM_PORT:-4723}"

echo "🔍 检查大麦抢票环境..."
echo "================================"

# 检查Python
echo "🐍 检查Python环境..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ Python: $PYTHON_VERSION"
else
    echo "❌ Python未安装"
    exit 1
fi

# 检查Node.js
echo ""
echo "📦 检查Node.js环境..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js: $NODE_VERSION"

    NODE_MAJOR=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_MAJOR" -ge 20 ]; then
        echo "✅ Node.js版本兼容"
    else
        echo "⚠️  Node.js版本可能不兼容，建议升级到20.19.0+"
    fi
else
    echo "❌ Node.js未安装"
    exit 1
fi

# 检查Appium
echo ""
echo "🤖 检查Appium..."
if command -v appium &> /dev/null; then
    APPIUM_VERSION=$(appium --version)
    echo "✅ Appium: $APPIUM_VERSION"
else
    echo "❌ Appium未安装"
    echo "   安装命令: npm install -g appium"
    exit 1
fi

# 检查Android SDK
echo ""
echo "📱 检查Android SDK..."
if [ -d "$ANDROID_HOME" ]; then
    echo "✅ Android SDK路径存在: $ANDROID_HOME"
else
    echo "❌ Android SDK路径不存在: $ANDROID_HOME"
    echo "   请安装Android Studio并设置 ANDROID_HOME 环境变量"
    exit 1
fi

# 检查ADB
echo ""
echo "🔧 检查ADB..."
ADB="$(command -v adb || echo "$ANDROID_HOME/platform-tools/adb")"
if [ -x "$ADB" ]; then
    echo "✅ ADB路径: $ADB"
else
    echo "❌ ADB未找到"
    exit 1
fi

# 检查Android设备
echo ""
echo "📱 检查Android设备..."
DEVICES=$("$ADB" devices | grep -c "device$" || true)
if [ "$DEVICES" -eq 0 ]; then
    echo "⚠️  未检测到Android设备"
    echo "   请启动模拟器或连接真机"
else
    echo "✅ 检测到 $DEVICES 个Android设备"

    if "$ADB" shell pm list packages | grep -q "cn.damai"; then
        echo "✅ 大麦APP已安装"
    else
        echo "⚠️  大麦APP未安装"
        echo "   请在设备上安装大麦APP"
    fi
fi

# 检查Appium服务器
echo ""
echo "🌐 检查Appium服务器..."
if curl -s "http://127.0.0.1:$APPIUM_PORT/status" > /dev/null; then
    echo "✅ Appium服务器正在运行（端口 $APPIUM_PORT）"
else
    echo "⚠️  Appium服务器未运行"
    echo "   启动命令: ./start_appium.sh"
fi

# 检查配置文件
echo ""
echo "📋 检查配置文件..."
if [ -f "damai_appium/config.jsonc" ]; then
    echo "✅ 配置文件存在"
    echo "   当前配置:"
    grep -E '"keyword"|"city"|"users"' damai_appium/config.jsonc | head -3 | sed 's/^/   /'
else
    echo "❌ 配置文件不存在"
    echo "   请创建 damai_appium/config.jsonc 文件"
fi

echo ""
echo "================================"
echo "🎯 环境检查完成！"
echo ""
echo "📝 使用说明:"
echo "   1. 启动Appium: ./start_appium.sh"
echo "   2. 开始抢票: ./start_ticket_grabbing.sh"
echo ""

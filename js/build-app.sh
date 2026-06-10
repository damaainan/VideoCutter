#!/bin/bash
# 将 Neutralino 构建产物打包为 macOS .app
set -e

APP_NAME="视频极简裁剪"
BUNDLE_ID="com.videocutter.app"
VERSION="1.1.2"
DIST_DIR="$(cd "$(dirname "$0")/dist/VideoCutter" && pwd)"
BINARY="$DIST_DIR/VideoCutter-mac_universal"
ICON_SRC="$(cd "$(dirname "$0")" && pwd)/resources/icon.png"
APP_DIR="$(cd "$(dirname "$0")" && pwd)/dist/${APP_NAME}.app"

echo "=== 打包 macOS .app ==="
echo "Binary: $BINARY"
echo "Icon: $ICON_SRC"
echo "Output: $APP_DIR"

# 清理旧包
rm -rf "$APP_DIR"

# 创建 .app 目录结构
mkdir -p "$APP_DIR/Contents/MacOS"
mkdir -p "$APP_DIR/Contents/Resources"
mkdir -p "$APP_DIR/Contents/Frameworks"

# 复制可执行文件
# 用启动脚本包装，确保工作目录在 Resources 下
cp "$BINARY" "$APP_DIR/Contents/MacOS/VideoCutter-bin"
chmod +x "$APP_DIR/Contents/MacOS/VideoCutter-bin"

cat > "$APP_DIR/Contents/MacOS/VideoCutter" << 'LAUNCHER'
#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"
exec "$DIR/VideoCutter-bin"
LAUNCHER
chmod +x "$APP_DIR/Contents/MacOS/VideoCutter"

# 复制 resources.neu（放到 MacOS 目录，因为 Neutralino 以二进制位置为基准）
cp "$DIST_DIR/resources.neu" "$APP_DIR/Contents/MacOS/"

# 复制 neutralino.config.json
cp "$(cd "$(dirname "$0")" && pwd)/neutralino.config.json" "$APP_DIR/Contents/MacOS/"

# 创建 .tmp 和 .storage 目录（Neutralino 运行时在二进制同级目录创建）
mkdir -p "$APP_DIR/Contents/MacOS/.tmp"
mkdir -p "$APP_DIR/Contents/MacOS/.storage"

# 生成 .icns 图标
ICONSET_DIR=$(mktemp -d)/icon.iconset
mkdir -p "$ICONSET_DIR"

if [ -f "$ICON_SRC" ]; then
  sips -z 16 16    "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16.png"      2>/dev/null
  sips -z 32 32    "$ICON_SRC" --out "$ICONSET_DIR/icon_16x16@2x.png"   2>/dev/null
  sips -z 32 32    "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32.png"      2>/dev/null
  sips -z 64 64    "$ICON_SRC" --out "$ICONSET_DIR/icon_32x32@2x.png"   2>/dev/null
  sips -z 128 128  "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128.png"    2>/dev/null
  sips -z 256 256  "$ICON_SRC" --out "$ICONSET_DIR/icon_128x128@2x.png" 2>/dev/null
  sips -z 256 256  "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256.png"    2>/dev/null
  sips -z 512 512  "$ICON_SRC" --out "$ICONSET_DIR/icon_256x256@2x.png" 2>/dev/null
  sips -z 512 512  "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512.png"    2>/dev/null
  sips -z 1024 1024 "$ICON_SRC" --out "$ICONSET_DIR/icon_512x512@2x.png" 2>/dev/null

  iconutil -c icns "$ICONSET_DIR" -o "$APP_DIR/Contents/Resources/icon.icns" 2>/dev/null || echo "⚠️ 图标转换跳过"
  rm -rf "$(dirname "$ICONSET_DIR")"
fi

# 生成 Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>VideoCutter</string>
    <key>CFBundleIdentifier</key>
    <string>$BUNDLE_ID</string>
    <key>CFBundleName</key>
    <string>$APP_NAME</string>
    <key>CFBundleDisplayName</key>
    <string>$APP_NAME</string>
    <key>CFBundleVersion</key>
    <string>$VERSION</string>
    <key>CFBundleShortVersionString</key>
    <string>$VERSION</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleIconFile</key>
    <string>icon.icns</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
</dict>
</plist>
EOF

echo ""
echo "✅ 打包完成: $APP_DIR"
echo ""
echo "使用方式:"
echo "  1. 双击 dist/${APP_NAME}.app 运行"
echo "  2. 或拖入 /Applications 目录"
echo ""
echo "⚠️  首次运行可能需要在 系统设置 > 隐私与安全 中允许运行"

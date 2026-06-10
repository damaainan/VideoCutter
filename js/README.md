
# 视频极简裁剪工具 - Neutralino.js 版本

基于 Neutralino.js 构建的视频裁剪桌面应用，功能完整，轻量高效。

## 功能特性

- ✅ 视频文件导入（拖拽/按钮添加）
- ✅ 两种时间模式：去头去尾 / 绝对起止时间
- ✅ 预设管理（保存/加载/删除）
- ✅ 无损流复制裁剪（FFmpeg -c copy）
- ✅ 精确模式（重编码）
- ✅ 批量处理和进度跟踪
- ✅ 每个文件独立时间配置
- ✅ 配置持久化保存

## 快速开始

### 1. 安装依赖

首先需要安装 Neutralino CLI：

```bash
npm install -g @neutralinojs/neu
```

### 2. 初始化项目（必需步骤！）

进入项目目录并下载依赖：

```bash
cd js
neu update
```

这会自动下载：
- `resources/js/neutralino.js` - 客户端库
- 对应平台的二进制运行时

⚠️ **重要**：首次运行 `neu build` 或 `neu run` 之前，必须先运行 `neu update`！

#### 🚫 如果 neu update 网络超时

**解决方案 1：手动下载（推荐临时方案）**

**获取 neutralino.js 客户端库**

访问 GitHub 官方发布页：
- 地址：https://github.com/neutralinojs/neutralino.js/releases
- 找到 `v3.8.0` 版本
- 下载 `neutralino.js` 文件
- 放到：`/Users/edy/work/cursor-tutor/cut/js/resources/js/neutralino.js`

**关于二进制运行时**

`neu update` 还要下载 Neutralino 的二进制可执行文件，这部分比较大。如果暂时无法下载：
- 可以先用浏览器打开 `index.html` 查看 UI（部分功能需要 Neutralino API）
- 或者网络恢复后再运行完整的 `neu update`

**解决方案 2：配置代理重试**

如果你有代理：
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
neu update
```

### 3. 开发运行

#### 推荐方案：直接运行（不带开发扩展，避免问题）
```bash
neu run -- --neu-dev-extension=false
```

#### 如果需要清理重新开始
```bash
cd js
rm -rf .neu .tmp bin dist
neu update
neu run -- --neu-dev-extension=false
```

### 4. 打包构建

先确保已运行 `neu update`，然后：

#### macOS ARM64 (Apple Silicon)

```bash
neu build
```

编译产物在 `dist/` 目录下：
- `VideoCutter-mac_arm64/` - macOS ARM64 应用文件夹
- `VideoCutter-mac_arm64.dmg` - 可选的 DMG 安装包（需额外配置）

#### Windows (x64)

在 Windows 系统上运行：

```bash
neu build
```

编译产物在 `dist/` 目录下：
- `VideoCutter-win_x64/` - Windows x64 应用文件夹
- `VideoCutter-win_x64.exe` - 可执行文件

#### 跨平台编译说明

Neutralino 支持在一个平台上为多个平台编译，需要：

1. 首先配置 `neutralino.config.json` 中的 `cli.binaryName` 等选项
2. 下载对应平台的二进制文件

完整的编译配置示例见下方。

## 系统要求

- **FFmpeg 和 FFprobe**：必须安装并配置到系统 PATH，或在应用设置中手动指定路径

安装 FFmpeg：
- macOS: `brew install ffmpeg`
- Windows: 下载并添加到 PATH
- Linux: `sudo apt install ffmpeg`

## 项目结构

```
js/
├── neutralino.config.json       # Neutralino 配置
├── package.json                 # npm 配置
├── README.md                    # 本文件
└── resources/
    ├── index.html               # 主界面
    ├── styles.css               # 样式文件
    ├── icon.png                 # 应用图标
    └── js/
        ├── app.js               # 主应用逻辑
        ├── core/                # 核心业务模块
        │   ├── time-range-calculator.js
        │   ├── overwrite-policy.js
        │   ├── preset-manager.js
        │   └── video-cutter-manager.js
        └── utils/               # 工具模块
            ├── time-parser.js
            ├── config.js
            └── ffmpeg.js
```

## 为什么放在 resources 目录？

这是 **Neutralino.js 的标准项目结构**：
- `resources/` 是 Neutralino 应用的静态资源根目录
- 所有 HTML、CSS、JS 和资源文件都应该放在这里
- 类似于 Web 应用的 `public/` 或 `dist/` 目录
- 符合 Neutralino 构建和打包的要求

## 代码说明

项目采用**传统的脚本加载方式**（而非 ES Modules），确保兼容性：

### 工具层（utils/）
- `time-parser.js` - 时间格式解析和格式化
- `config.js` - 配置管理（持久化）
- `ffmpeg.js` - FFmpeg 和 FFprobe 调用封装

### 业务层（core/）
- `time-range-calculator.js` - 时间范围逻辑计算
- `overwrite-policy.js` - 文件冲突策略处理
- `preset-manager.js` - 预设管理
- `video-cutter-manager.js` - 核心裁剪任务管理

### 应用层
- `app.js` - 主应用逻辑、UI 交互

所有脚本通过 `<script>` 标签按依赖顺序加载，无模块导入问题。

## 使用说明

### 1. 添加视频

- 点击"添加文件"按钮选择视频
- 或直接拖拽视频到左侧区域

### 2. 设置时间

两种模式：
- **去头去尾**：设置要去除的开头和结尾长度
- **绝对起止**：直接设置保留的开始和结束时间

时间格式支持：
- 纯数字（秒）：`10`
- HH:MM:SS：`00:01:30`
- HH:MM:SS.sss：`00:01:30.500`
- MM:SS：`01:30`

### 3. 开始裁剪

点击"开始裁剪"按钮，程序会批量处理所有文件

### 4. 预设管理

- 保存当前设置为预设
- 从下拉列表选择并应用预设
- 删除不需要的预设

### 5. 配置设置

点击右上角"设置"按钮可配置：
- FFmpeg 路径
- FFprobe 路径
- 输出文件后缀
- 文件冲突策略

## 技术栈

- **Neutralino.js**：轻量跨平台桌面应用框架
- **HTML5/CSS3/JavaScript**：前端技术
- **FFmpeg**：视频处理引擎

## 常见问题

### neu update 网络超时（ETIMEDOUT）？

这是非常常见的问题！解决方法：

#### 方案 1：重试几次
```bash
cd js
neu update
# 如果超时，再运行几次试试
neu update
```

#### 方案 2：手动下载（推荐临时方案）

**1. 获取 neutralino.js 客户端库**

从 GitHub 官方发布页下载：
- 访问：https://github.com/neutralinojs/neutralino.js/releases
- 找到 `v3.8.0` 版本
- 下载 `neutralino.js` 文件
- 放到：`/Users/edy/work/cursor-tutor/cut/js/resources/js/neutralino.js`

**2. 关于二进制运行时**

`neu update` 还要下载 Neutralino 的二进制可执行文件，这部分比较大。如果暂时无法下载：
- 可以先用浏览器打开 `index.html` 查看 UI（部分功能需要 Neutralino API）
- 或者网络恢复后再运行完整的 `neu update`

#### 方案 3：配置代理

如果你有代理：
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
neu update
```

---

### 编译时提示 "no such file or directory, stat './resources/js/neutralino.js'"？

这是最常见的问题！解决方法：

```bash
cd js
neu update  # 先运行这个下载依赖
neu build   # 然后再编译
```

### neu run 出现各种错误？（端口/URL/等）

开发扩展有兼容性问题，**推荐直接不带扩展运行**：

```bash
neu run -- --neu-dev-extension=false
```

如果需要完全重置：
```bash
cd js
rm -rf .neu .tmp bin dist
neu update
neu run -- --neu-dev-extension=false
```

我们已配置：
- 固定端口：`8080`
- 稳定版本：`4.15.0`
- 修复路径：`documentRoot` 改为 `/`

---

### 启动后白屏，提示找不到资源文件？

这是路径配置问题！我们已修复：
- `documentRoot` 改为 `/`（而非 `/resources`）
- `resourcesPath` 改为 `resources`（不带前导 `/`）

请重新运行：
```bash
neu run -- --neu-dev-extension=false
```

---

### 找不到 neutralino.js？

同上，运行 `neu update` 命令自动下载，或者手动下载放入目录。

### FFmpeg 路径错误？

在应用设置中手动指定 FFmpeg 和 FFprobe 的完整路径。

### 为什么没有 ui 目录？

当前版本采用单页面应用结构，UI 全部整合在 `index.html` 和 `styles.css` 中，更加简洁。

## 完整编译配置

### 1. neutralino.config.json 配置

当前项目已包含基本配置，如需更多定制可参考：

```json
{
  "applicationId": "com.videocutter.app",
  "version": "1.1.2",
  "defaultMode": "window",
  "port": 0,
  "documentRoot": "/resources",
  "url": "/resources/index.html",
  "enableServer": true,
  "enableNativeAPI": true,
  "tokenSecurity": "one-time",
  "nativeAllowList": [
    "app.*",
    "os.*",
    "filesystem.*",
    "storage.*",
    "events.*",
    "window.*"
  ],
  "modes": {
    "window": {
      "title": "视频极简裁剪工具",
      "width": 1200,
      "height": 700,
      "minWidth": 800,
      "minHeight": 600,
      "icon": "/resources/icon.png",
      "enableInspector": true,
      "borderless": false,
      "maximize": false,
      "hidden": false
    }
  },
  "cli": {
    "binaryName": "VideoCutter",
    "resourcesPath": "/resources",
    "extensionsPath": "/extensions",
    "clientLibrary": "/resources/js/neutralino.js",
    "binaryVersion": "4.15.0",
    "clientVersion": "3.8.0"
  }
}
```

### 2. 高级编译选项

#### 打包为单个可执行文件

Neutralino 支持将资源嵌入二进制，不过推荐使用文件夹分发以便调试。

#### macOS 权限配置

macOS 上打包的应用可能需要签名和公证才能正常分发。

#### Windows 图标

替换 `resources/icon.png` 或在配置中指定 Windows 图标格式（.ico）。

## 编译输出目录说明

成功运行 `neu build` 后，会生成以下结构：

```
js/
└── dist/
    ├── VideoCutter-mac_arm64/      # macOS ARM64 版本
    │   ├── VideoCutter              # 主二进制
    │   └── resources/               # 应用资源
    ├── VideoCutter-linux_x64/      # Linux 版本（如果启用）
    └── VideoCutter-win_x64/        # Windows 版本
        ├── VideoCutter.exe          # Windows 可执行文件
        └── resources/
```

## 分发建议

### macOS
1. 调试和本地使用：直接运行 `dist/VideoCutter-mac_arm64/VideoCutter`
2. 分发：可创建 `.dmg` 或 `.zip` 包

### Windows
1. 本地使用：直接运行 `dist/VideoCutter-win_x64/VideoCutter.exe`
2. 分发：可使用 NSIS 或 Inno Setup 创建安装程序

### FFmpeg 分发说明
- **推荐方案**：提示用户自行安装 FFmpeg
- **便携方案**：将 FFmpeg 二进制文件打包在应用内，在设置中默认指向该路径

### 存在问题
1. Neutralino 不支持文件拖拽，所以功能不再做细化，只满足基本使用
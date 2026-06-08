# 视频极简裁剪工具 (VideoCutter) v1.1.2

> 一款基于 Python + PySide6 + FFmpeg 的极简视频裁剪桌面工具，专注于快速去除片头片尾或按任意起止点截取视频片段，支持批量处理、每文件独立时间配置，保持原始格式无损裁剪。

---

## 开发背景

在日常使用视频素材时，经常需要去除片头片尾广告、截取特定片段等操作。市面上的视频编辑软件大多功能繁多、体积庞大，对于简单的裁剪需求来说过于笨重。

本项目旨在打造一款**极致简洁**的视频裁剪工具：
- **操作路径最短**：拖入文件 → 设置时间 → 一键裁剪
- **无损极速**：使用 FFmpeg 流复制模式（`-c copy`），秒级完成裁剪，画质零损失
- **批量处理**：一次添加多个视频，统一应用相同的裁剪参数
- **极简设计**：界面干净，没有多余的按钮和选项

---

## 功能特性

### 核心功能

| 功能 | 说明 |
|------|------|
| 视频文件导入 | 支持拖拽添加和按钮选择，自动过滤视频格式，去重处理 |
| 去头去尾模式 | 输入要去掉的开头 A 和结尾 B 时长，保留 `[A, 总时长-B]` 区间 |
| 绝对起止模式 | 直接指定保留的开始和结束时间点 |
| 批量裁剪 | 对文件列表中所有文件统一应用裁剪参数 |
| 每文件独立时间 | v1.1.2: 每个视频可设置专属裁剪时间，其余文件使用默认时间 |
| 配置持久化 | v1.1.2: 默认时间和文件自定义时间持久化保存，重启后恢复 |
| 无损裁剪 | 使用 FFmpeg `-c copy` 流复制，不重编码，极速完成 |
| 精确模式 | 可选重编码模式，精确到帧级别对齐 |
| 预设管理 | 保存/应用/删除常用裁剪参数预设，支持启动自动加载 |
| 进度追踪 | 实时显示处理进度、文件状态、日志输出 |
| 文件冲突处理 | 支持询问/自动重命名/跳过/覆盖四种策略 |

### 时间输入

支持多种时间格式，自动解析：

- **纯数字**（秒）：`110`、`50.5`
- **HH:MM:SS**：`01:30:00`
- **HH:MM:SS.sss**：`01:30:00.500`（含毫秒）
- **MM:SS**：`05:30`

输入框旁提供实时预览（如 `= 00:01:50`），非法格式红色边框提醒。

### 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+O` | 添加文件 |
| `Ctrl+S` | 保存配置（v1.1.2） |
| `Ctrl+,` | 打开设置 |
| `Enter` | 开始裁剪 |
| `Escape` | 取消当前任务 |
| `Ctrl+Q` | 退出程序 |

### 其他细节

- 智能时长探测：文件添加后自动异步获取视频时长
- 右键菜单：移除文件、打开所在目录、重试失败项、设置自定义时间、重置为默认时间
- 双击文件条目：直接打开自定义时间设置对话框
- 设置持久化：基于 QSettings 保存所有用户配置
- 配置持久化：默认时间和文件自定义时间保存到 JSON，重启后自动恢复
- 窗口状态记忆：关闭后记住窗口位置和大小

---

## 技术栈

| 组件 | 技术 |
|------|------|
| 编程语言 | Python 3.8+ |
| GUI 框架 | PySide6 (Qt for Python) |
| 视频处理 | FFmpeg / FFprobe |
| 打包工具 | PyInstaller |
| 进程管理 | QProcess（异步非阻塞） |
| 线程模型 | QThread + QThreadPool |
| 配置存储 | QSettings（跨平台原生） |
| 预设存储 | JSON 文件 |

---

## 项目结构

```
cut/
├── main.py                          # 程序入口
├── config.py                        # 全局配置管理（单例）
├── requirements.txt                 # Python 依赖
├── README.md                        # 项目说明文档
│
├── resources/                       # 资源文件
│   ├── icon.ico                     # Windows 图标
│   ├── icon.icns                    # macOS 图标
│   └── icon.png                     # 通用图标
│
├── core/                            # 应用逻辑层（业务核心）
│   ├── __init__.py
│   ├── time_range_calculator.py     # 时间范围计算器（-ss/-to 参数计算）
│   ├── preset_manager.py            # 预设管理器（增删改查 + JSON 持久化）
│   ├── overwrite_policy.py          # 文件冲突处理策略
│   └── video_cutter_manager.py      # 视频裁剪管理器（任务调度/队列/进度）
│
├── ui/                              # 表现层（PySide6 界面）
│   ├── __init__.py
│   ├── main_window.py               # 主窗口（菜单栏/状态栏/拖放/布局）
│   ├── file_list_widget.py          # 文件列表控件（表格/拖放/右键菜单/时间列）
│   ├── time_input_widget.py         # 时间输入控件（模式切换/实时预览）
│   ├── preset_widget.py             # 预设控件（下拉框/操作按钮）
│   ├── cutter_control_panel.py      # 裁剪控制面板（整合所有操作控件）
│   ├── settings_dialog.py           # 设置对话框（ffmpeg/输出/裁剪配置）
│   ├── preset_dialog.py             # 预设名称输入对话框
│   └── custom_time_dialog.py        # v1.1.2: 自定义时间设置对话框
│
└── utils/                           # 基础设施层（底层工具）
    ├── __init__.py
    ├── platform_helper.py           # 跨平台工具（平台检测/字体/图标/路径）
    ├── time_parser.py               # 时间字符串解析与格式化
    ├── config_manager.py            # QSettings 配置封装
    ├── ffmpeg_runner.py             # FFmpeg QProcess 执行封装
    └── ffprobe_helper.py            # FFprobe 视频元数据获取
```

### 架构说明

采用**分层架构 + 信号槽通信**的设计：

```
┌─────────────────────────────────────────────┐
│              表现层 (ui/)                     │
│  MainWindow → FileListWidget                │
│             → CutterControlPanel            │
│                → TimeInputWidget            │
│                → PresetWidget               │
└──────────────────┬──────────────────────────┘
                   │ Signals & Slots
┌──────────────────▼──────────────────────────┐
│             应用逻辑层 (core/)               │
│  VideoCutterManager – 任务调度              │
│  PresetManager – 预设管理                   │
│  TimeRangeCalculator – 参数计算             │
│  OverwritePolicy – 冲突处理                 │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│            基础设施层 (utils/)               │
│  FFmpegRunner – QProcess 封装               │
│  FFprobeHelper – 视频元数据                 │
│  TimeParser – 时间解析                      │
│  ConfigManager – 配置管理                   │
└─────────────────────────────────────────────┘
```

- **UI 层**只负责展示和用户交互，不包含业务逻辑
- **Core 层**处理裁剪计算、任务调度、预设管理
- **Utils 层**封装 FFmpeg 调用、时间解析等底层工具
- 层间通过 Qt 信号/槽机制通信，保证线程安全

---

## 环境要求

### 系统要求

- **操作系统**：Windows 10+、macOS 10.15+、Linux
- **Python**：3.8 或更高版本
- **FFmpeg**：需要单独安装并配置到系统 PATH，或在设置中手动指定路径

### Python 依赖

| 包名 | 版本要求 | 说明 |
|------|----------|------|
| PySide6 | >= 6.5.0 | Qt for Python GUI 框架 |
| pyinstaller | >= 5.0 | 打包工具（仅打包时需要） |

---

## 安装与运行

### 1. 安装 FFmpeg

**Windows：**
```bash
# 使用 Scoop 安装（推荐）
scoop install ffmpeg

# 或手动下载：https://ffmpeg.org/download.html
# 将 ffmpeg.exe 所在目录添加到系统 PATH
```

**macOS：**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian)：**
```bash
sudo apt update && sudo apt install ffmpeg
```

验证安装：
```bash
ffmpeg -version
ffprobe -version
```

### 2. 安装 Python 依赖

```bash
cd cut/
pip install -r requirements.txt
```

### 3. 运行程序

```bash
python main.py
```

首次启动时，程序会自动检测系统 PATH 中的 ffmpeg。如果未找到，会弹出提示引导你在设置中手动指定路径。

---

## 使用指南

### 基本操作流程

1. **添加视频文件**：拖拽视频文件到左侧列表区域，或点击「添加文件」按钮（Ctrl+O）
2. **选择时间模式**：
   - **去头去尾**：输入要去掉的开头时长（A）和结尾时长（B），留空表示不去头/不去尾
   - **绝对起止**：输入保留区间的开始和结束时间，留空表示从头/到结尾
3. **点击「开始裁剪」**（或按 Enter），程序将批量处理所有文件
4. **查看结果**：裁剪后的文件保存在原视频同目录下，文件名添加 `_1` 后缀

### 预设使用

- **保存预设**：设置好时间参数后，点击预设区域的「保存」按钮，输入名称即可
- **应用预设**：从下拉框选择预设，点击「应用」自动填入时间参数
- **默认预设**：可标记一个预设为启动时自动加载

### 设置选项

通过菜单栏「文件 → 设置」（Ctrl+,）打开设置对话框：

| 选项 | 说明 |
|------|------|
| FFmpeg 路径 | ffmpeg 可执行文件位置 |
| FFprobe 路径 | ffprobe 可执行文件位置 |
| 输出文件后缀 | 默认 `_1`，可自定义 |
| 文件冲突策略 | 询问 / 自动重命名 / 跳过 / 覆盖 |
| 精确模式 | 启用后重编码裁剪，精确到帧但速度慢 |
| faststart | MP4 文件启用，便于网络流式播放 |

---

## FFmpeg 命令说明

### 快速模式（默认）

使用流复制，不重编码，速度极快：

```bash
ffmpeg -ss {A} -i "输入.mp4" -to {总时长-B} -c copy -map 0 -avoid_negative_ts make_zero -y "输出_1.mp4"
```

> 注意：流复制时剪切点会自动对齐到最近的关键帧，因此实际裁剪时长可能有 ±几秒误差。

### 精确模式

重编码至关键帧完全对齐，速度慢但精确：

```bash
ffmpeg -i "输入.mp4" -ss {A} -to {总时长-B} -c:v libx264 -c:a aac -y "输出_1.mp4"
```

---

## 跨平台兼容性

程序内置了跨平台适配层（`utils/platform_helper.py`），自动处理以下差异：

| 平台 | 字体 | 图标格式 | 配置文件 | ffmpeg 检测路径 |
|------|------|------|------|------|
| Windows x64 | Consolas | .ico | 注册表 | C:\ffmpeg\bin, scoop, 用户目录 |
| macOS arm64 | Menlo | .icns | ~/Library/Preferences/*.plist | /opt/homebrew/bin (Homebrew) |
| macOS Intel | Menlo | .icns | ~/Library/Preferences/*.plist | /usr/local/bin (Homebrew) |
| Linux | Ubuntu Mono | .png | ~/.config | /usr/bin, /snap/bin |

**图标设置：**
- 应用程序图标和窗口图标均自动从 `resources/` 目录加载
- 打包时通过 `--icon` 参数指定平台对应的图标格式

**ffmpeg 自动检测优先级：**
1. 打包内嵌的 ffmpeg（通过 `--add-data` 放入包内）
2. 系统 PATH 中的 ffmpeg
3. 常见安装路径（按平台自动搜索）
4. 均未找到时，启动后状态栏提示用户通过设置手动配置

---

## 打包为可执行文件

### 前置准备

```bash
pip install pyinstaller
```
创建纯净虚拟环境（最关键）
```sh
# 在项目目录下
python3 -m venv venv_clean
source venv_clean/bin/activate

# 仅安装必须的依赖
pip install PySide6 pyinstaller

# 如果你用了其他库（如 Pygame 等），也在这里安装，否则不装
```

### 打包命令

#### Windows x64

```bash
cd cut/

pyinstaller ^
    --onedir ^
    --windowed ^
    --name "VideoCutter" ^
    --icon=resources/icon.ico ^
    --add-data "resources;resources" ^
    --copy-metadata PySide6 ^
    --hidden-import PySide6.QtCore ^
    --hidden-import PySide6.QtGui ^
    --hidden-import PySide6.QtWidgets ^
    --clean ^
    main.py
```

#### macOS arm64 (Apple Silicon)

```bash
cd cut/

pyinstaller \
    --onedir \
    --windowed \
    --name "VideoCutter" \
    --target-arch arm64 \
    --osx-bundle-identifier com.videocutter.app \
    --icon=resources/icon.icns \
    --add-data "resources:resources" \
    --copy-metadata PySide6 \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --clean \
    main.py
```

#### macOS Intel (x86_64)

```bash
cd cut/

pyinstaller \
    --onedir \
    --windowed \
    --name "VideoCutter" \
    --target-arch x86_64 \
    --osx-bundle-identifier com.videocutter.app \
    --icon=resources/icon.icns \
    --add-data "resources:resources" \
    --copy-metadata PySide6 \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --clean \
    main.py
```

### 打包参数说明

| 参数 | 说明 |
|------|------|
| `--onefile` | 打包为单个可执行文件 |
| `--onedir` | 打包为目录（含依赖文件） |
| `--windowed` / `-w` | 无控制台窗口（GUI 模式） |
| `--name` | 输出文件名 |
| `--icon` | 程序图标（.ico/.icns，按平台选择） |
| `--add-data` | 附加资源文件（Windows 用 `;`，macOS/Linux 用 `:`） |
| `--target-arch` | 目标架构（arm64 / x86_64） |
| `--copy-metadata PySide6` | 复制 Qt 插件元数据，解决平台插件加载问题 |
| `--hidden-import` | 确保不遗漏延迟导入的模块 |
| `--osx-bundle-identifier` | macOS Bundle ID |

> **macOS 打包注意事项：**
> - 必须使用对应架构的 Python（arm64 或 x86_64），而非 Rosetta 转译版本
> - `--target-arch` 确保生成原生二进制
> - macOS 的 `--add-data` 使用冒号 `:` 分隔（Windows 用分号 `;`）
> - `--onedir --windowed` 自动生成 `.app` 包
> - 打包后可用 `file dist/VideoCutter.app/Contents/MacOS/VideoCutter` 验证架构
> - 如需创建 DMG 分发，可使用 `hdiutil` 或 `create-dmg` 工具

### 输出位置

打包完成后，可执行文件位于：
```
# Windows
cut/dist/VideoCutter/VideoCutter.exe    # --onedir 模式
cut/dist/VideoCutter.exe                # --onefile 模式

# macOS
cut/dist/VideoCutter.app                # --onedir --windowed 模式
cut/dist/VideoCutter                    # --onefile 模式
```

### 附带 FFmpeg（可选）

为了让用户无需单独安装 FFmpeg，可以将便携版 FFmpeg 一起打包：

**Windows：**
```bash
# 将 ffmpeg.exe 和 ffprobe.exe 放在 resources/ffmpeg/ 目录下
pyinstaller ^
    --onedir ^
    --windowed ^
    --name "VideoCutter" ^
    --icon=resources/icon.ico ^
    --add-data "resources;resources" ^
    --add-data "resources/ffmpeg;ffmpeg" ^
    --copy-metadata PySide6 ^
    --clean ^
    main.py
```

**macOS：**
```bash
# 将 ffmpeg 和 ffprobe 放在 resources/ffmpeg/ 目录下
python3 -m PyInstaller  --onedir --windowed --name "VideoCutter" --target-arch arm64 --osx-bundle-identifier com.videocutter.app --icon=resources/icon.icns --add-data "resources:resources" --copy-metadata PySide6 --upx-dir /opt/homebrew/bin  --exclude-module tkinter --exclude-module matplotlib --exclude-module numpy --exclude-module pandas --exclude-module scipy --exclude-module PIL --exclude-module cv2 --exclude-module pytest --exclude-module setuptools --exclude-module pip --exclude-module tkinter  --clean main.py

pyinstaller \
    --onedir \
    --windowed \
    --name "VideoCutter" \
    --target-arch arm64 \
    --osx-bundle-identifier com.videocutter.app \
    --icon=resources/icon.icns \
    --add-data "resources:resources" \
    --add-data "resources/ffmpeg:ffmpeg" \
    --copy-metadata PySide6 \
    --upx-dir /opt/homebrew/bin \
    --clean \
    --exclude-module tkinter \
    --exclude-module matplotlib \
    --exclude-module numpy \
    --exclude-module pandas \
    --exclude-module scipy \
    --exclude-module PIL \
    --exclude-module cv2 \
    --exclude-module pytest \
    --exclude-module setuptools \
    --exclude-module pip \
    --exclude-module tkinter \
    main.py
```


> 便携版 FFmpeg 下载：
> - Windows: https://www.gyan.dev/ffmpeg/builds/ （`ffmpeg-release-essentials.zip`）
> - macOS: `brew install ffmpeg` 后复制 `/opt/homebrew/bin/ffmpeg`

---

## 开发指南

### 开发环境搭建

```bash
# 克隆项目后安装依赖
pip install PySide6

# 可选：安装开发辅助工具
pip install flake8 black pylint
```

### 运行调试

```bash
# 直接运行（带控制台输出）
python main.py
```

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解（Type Hints）
- 类和公共方法必须有文档字符串
- 信号命名使用小写 + 下划线
- UI 类私有成员使用 `_` 前缀

---

## 常见问题

### Q: 启动提示 "ffmpeg 未找到"
程序会自动在常见路径中搜索 ffmpeg，如仍未找到：
- **Windows**：在「设置」中指定 `ffmpeg.exe` 完整路径，或将 ffmpeg 所在目录添加到系统 PATH
- **macOS**：点击状态栏红色提示或在「设置」中指定路径（如 `/opt/homebrew/bin/ffmpeg`）
- **Linux**：确保已安装 `sudo apt install ffmpeg`

### Q: 裁剪后视频时长与预期有偏差
这是快速模式（流复制）的正常现象。FFmpeg 在流复制时会将剪切点对齐到最近的关键帧。如需精确裁剪，请勾选「精确到帧（慢）」选项。

### Q: 某些视频格式裁剪失败
确保 FFmpeg 版本较新（建议 4.4+），部分容器格式可能需要特定版本的 FFmpeg 支持。

### Q: 打包后 exe 文件过大
PySide6 本身较大（约 200MB+），可考虑：
- 使用 `--onedir` 模式并配合 UPX 压缩
- 仅导入需要的 PySide6 模块
- 使用 Nuitka 替代 PyInstaller

### Q: macOS arm64 打包后无法运行
检查以下几点：
- 确认使用的 Python 是 arm64 版本：`python3 -c "import platform; print(platform.machine())"` 应输出 `arm64`
- 确认 PySide6 也是 arm64 版本
- 若提示"无法验证开发者"，在系统设置 > 隐私与安全中点击"仍然允许"
- 如需分发给其他用户，建议使用 `codesign` 签名或创建 DMG

### Q: 排查方法

1. 从终端运行查看报错
```bash
# 如果是 .app 包，直接运行内部的可执行文件
./dist/VideoCutter.app/Contents/MacOS/VideoCutter

# 如果是单文件
./dist/VideoCutter
```

---

## 许可证

本项目仅供学习参考使用。

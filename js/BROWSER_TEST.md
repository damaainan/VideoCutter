
# 浏览器测试方案

如果 neu update 网络超时，可以先用浏览器查看 UI 效果！

## 快速查看 UI

直接在浏览器中打开：

```
/Users/edy/work/cursor-tutor/cut/js/resources/index.html
```

⚠️ **注意**：
- 浏览器中无法使用 Neutralino 原生 API（文件操作、FFmpeg调用等）
- 但可以查看界面布局和交互效果

## 需要 Neutralino 功能时

请尝试以下方法：

1. 重试 `neu update` 几次
2. 配置网络代理
3. 等待网络恢复
4. 或手动从 GitHub 下载 Neutralino 二进制文件

## 项目文件说明

所有代码已经完成：
- `resources/index.html` - 界面
- `resources/styles.css` - 样式
- `resources/js/app.js` - 主逻辑
- `resources/js/core/*.js` - 业务逻辑
- `resources/js/utils/*.js` - 工具模块

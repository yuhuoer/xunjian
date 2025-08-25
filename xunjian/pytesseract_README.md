# pytesseract 验证码识别功能使用指南

## 安装依赖

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 安装 Tesseract OCR 引擎

#### Windows:
1. 下载并安装 Tesseract: https://github.com/UB-Mannheim/tesseract/wiki
2. 将安装路径添加到系统环境变量 PATH
3. 或者设置环境变量：
```bash
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

#### macOS:
```bash
brew install tesseract
```

#### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr
```

### 3. 安装中文语言包（可选）
```bash
# Windows: 下载时选择中文包
# macOS:
brew install tesseract-lang

# Ubuntu:
sudo apt-get install tesseract-ocr-chi-sim
```

## 使用方法

### 1. 基本 OCR 识别
```json
{
  "action": "ocr_captcha",
  "selector": "#captcha-img",
  "name": "captcha_text",
  "preprocessing": "binary"
}
```

### 2. 自动解决验证码
```json
{
  "action": "solve_captcha",
  "captcha_selector": "#captcha-img",
  "input_selector": "#captcha-input",
  "submit_selector": "#submit-btn",
  "max_attempts": 3
}
```

### 3. 图像预处理选项
- `"default"`: 默认灰度处理
- `"binary"`: 二值化处理（推荐用于简单验证码）
- `"grayscale"`: 纯灰度处理
- `"denoise"`: 去噪处理（推荐用于有干扰线的验证码）

### 4. 处理 iframe 中的验证码
```json
{ "action": "switch_to_frame", "selector": "xpath=//iframe[@title='reCAPTCHA']" },
{ "action": "wait_user", "text": "请在iframe中完成验证码后按回车..." },
{ "action": "switch_to_default_content" }
```

### 5. Cookie 复用（跳过验证码）
```json
# 首次登录保存 cookie
{ "action": "save_cookies", "path": "artifacts/login_cookies.json" }

# 后续访问加载 cookie
{ "action": "load_cookies", "path": "artifacts/login_cookies.json" }
```

## 运行示例

```bash
# 运行包含验证码识别的测试
python xunjian/selenium_flow_suite.py --suite xunjian/pytesseract_captcha_example.json --default-timeout 30

# 非无头模式（可以看到验证码识别过程）
python xunjian/selenium_flow_suite.py --suite xunjian/pytesseract_captcha_example.json --default-timeout 30
```

## 常见问题

### 1. OCR 识别率低
- 尝试不同的预处理方式：`binary`, `denoise`
- 检查验证码图片是否清晰
- 调整 Tesseract 配置参数

### 2. 验证码在 iframe 中
- 使用 `switch_to_frame` 切换到 iframe
- 完成验证后使用 `switch_to_default_content` 切换回主文档

### 3. 复杂验证码（如 reCAPTCHA）
- 使用 `wait_user` 等待手动完成
- 或使用 `save_cookies`/`load_cookies` 复用登录状态

### 4. 网络问题导致验证码加载失败
- 增加 `timeout` 值
- 添加 `wait_visible` 等待验证码图片加载完成

## 高级配置

### 自定义 Tesseract 配置
在 `_ocr_captcha` 函数中修改 `config` 参数：
```python
config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
```

### 添加更多预处理方式
在 `_ocr_captcha` 函数中添加新的预处理选项。

### 集成第三方验证码识别服务
可以修改 `_ocr_captcha` 函数，调用在线验证码识别 API。

## 实际使用示例

### 示例1：简单验证码识别
```json
{
  "name": "simple-captcha",
  "steps": [
    { "action": "goto", "url": "https://example.com/login" },
    { "action": "type", "selector": "#username", "text": "user" },
    { "action": "type", "selector": "#password", "text": "pass" },
    { "action": "ocr_captcha", "selector": "#captcha-img", "name": "captcha", "preprocessing": "binary" },
    { "action": "type", "selector": "#captcha-input", "text": "${captcha}" },
    { "action": "click", "selector": "#login-btn" }
  ]
}
```

### 示例2：自动重试验证码
```json
{
  "name": "auto-retry-captcha",
  "steps": [
    { "action": "goto", "url": "https://example.com/login" },
    { "action": "type", "selector": "#username", "text": "user" },
    { "action": "type", "selector": "#password", "text": "pass" },
    { "action": "solve_captcha", "captcha_selector": "#captcha-img", "input_selector": "#captcha-input", "max_attempts": 5 },
    { "action": "click", "selector": "#login-btn" }
  ]
}
```

### 示例3：手动输入验证码
```json
{
  "name": "manual-captcha",
  "steps": [
    { "action": "goto", "url": "https://example.com/login" },
    { "action": "type", "selector": "#username", "text": "user" },
    { "action": "type", "selector": "#password", "text": "pass" },
    { "action": "prompt", "name": "captcha", "text": "请输入验证码: " },
    { "action": "type", "selector": "#captcha-input", "text": "${captcha}" },
    { "action": "click", "selector": "#login-btn" }
  ]
}
```

# pytesseract 验证码识别完整指南

## 功能概述

你的 `selenium_flow_suite.py` 现在已经支持使用 pytesseract 进行验证码识别。这个功能可以：

1. **自动识别验证码图片**：使用 OCR 技术识别验证码文字
2. **多种预处理方式**：支持不同的图像预处理方法提高识别率
3. **自动重试机制**：识别失败时自动重试
4. **交互式处理**：支持手动输入和 iframe 处理
5. **Cookie 复用**：保存登录状态跳过验证码

## 安装步骤

### 1. 安装 Python 依赖
```bash
pip install -r requirements.txt
```

### 2. 安装 Tesseract OCR 引擎

#### Windows:
1. 访问 https://github.com/UB-Mannheim/tesseract/wiki
2. 下载并安装最新版本
3. 将安装路径添加到系统环境变量 PATH
4. 或者设置环境变量：
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

### 3. 验证安装
```bash
python xunjian/test_pytesseract.py
```

## 使用方法

### 方法1：仅识别验证码
```json
{
  "action": "ocr_captcha",
  "selector": "#captcha-img",
  "name": "captcha_text",
  "preprocessing": "binary"
}
```

### 方法2：自动解决验证码
```json
{
  "action": "solve_captcha",
  "captcha_selector": "#captcha-img",
  "input_selector": "#captcha-input",
  "submit_selector": "#submit-btn",
  "max_attempts": 3
}
```

### 方法3：手动输入验证码
```json
{
  "action": "prompt",
  "name": "manual_captcha",
  "text": "请输入验证码: "
}
```

### 方法4：处理 iframe 验证码
```json
{ "action": "switch_to_frame", "selector": "xpath=//iframe[@title='reCAPTCHA']" },
{ "action": "wait_user", "text": "请在iframe中完成验证码后按回车..." },
{ "action": "switch_to_default_content" }
```

### 方法5：Cookie 复用
```json
# 首次登录保存 cookie
{ "action": "save_cookies", "path": "artifacts/login_cookies.json" }

# 后续访问加载 cookie
{ "action": "load_cookies", "path": "artifacts/login_cookies.json" }
```

## 图像预处理选项

- `"default"`: 默认灰度处理
- `"binary"`: 二值化处理（推荐用于简单验证码）
- `"grayscale"`: 纯灰度处理
- `"denoise"`: 去噪处理（推荐用于有干扰线的验证码）

## 完整示例

### 示例1：简单验证码识别
```json
{
  "name": "simple-captcha-login",
  "variables": {
    "base": "https://example.com",
    "username": "testuser",
    "password": "testpass"
  },
  "steps": [
    { "action": "goto", "url": "${base}/login" },
    { "action": "type", "selector": "#username", "text": "${username}" },
    { "action": "type", "selector": "#password", "text": "${password}" },
    { "action": "ocr_captcha", "selector": "#captcha-img", "name": "captcha", "preprocessing": "binary" },
    { "action": "type", "selector": "#captcha-input", "text": "${captcha}" },
    { "action": "click", "selector": "#login-btn" },
    { "action": "wait_visible", "selector": ".dashboard" },
    { "action": "check_error_keyword" }
  ]
}
```

### 示例2：自动重试验证码
```json
{
  "name": "auto-retry-captcha",
  "variables": {
    "base": "https://example.com",
    "username": "testuser",
    "password": "testpass"
  },
  "steps": [
    { "action": "goto", "url": "${base}/login" },
    { "action": "type", "selector": "#username", "text": "${username}" },
    { "action": "type", "selector": "#password", "text": "${password}" },
    { "action": "solve_captcha", "captcha_selector": "#captcha-img", "input_selector": "#captcha-input", "max_attempts": 5 },
    { "action": "click", "selector": "#login-btn" },
    { "action": "wait_visible", "selector": ".dashboard" },
    { "action": "check_error_keyword" }
  ]
}
```

### 示例3：Cookie 复用登录
```json
{
  "name": "cookie-reuse-login",
  "variables": {
    "base": "https://example.com",
    "username": "testuser",
    "password": "testpass"
  },
  "steps": [
    # 首次登录
    { "action": "goto", "url": "${base}/login" },
    { "action": "type", "selector": "#username", "text": "${username}" },
    { "action": "type", "selector": "#password", "text": "${password}" },
    { "action": "wait_user", "text": "请手动完成验证码后按回车保存cookie..." },
    { "action": "save_cookies", "path": "artifacts/login_cookies.json" },
    
    # 后续访问
    { "action": "goto", "url": "${base}" },
    { "action": "load_cookies", "path": "artifacts/login_cookies.json" },
    { "action": "goto", "url": "${base}/dashboard" },
    { "action": "wait_visible", "selector": ".dashboard" },
    { "action": "check_error_keyword" }
  ]
}
```

## 运行命令

```bash
# 运行验证码识别测试
python xunjian/selenium_flow_suite.py --suite xunjian/pytesseract_captcha_example.json --default-timeout 30

# 非无头模式（可以看到验证码识别过程）
python xunjian/selenium_flow_suite.py --suite xunjian/pytesseract_captcha_example.json --default-timeout 30

# 使用本地 ChromeDriver
python xunjian/selenium_flow_suite.py --suite xunjian/pytesseract_captcha_example.json --chromedriver-path "C:\tools\chromedriver.exe"
```

## 常见问题解决

### 1. OCR 识别率低
- 尝试不同的预处理方式：`binary`, `denoise`
- 检查验证码图片是否清晰
- 调整 Tesseract 配置参数

### 2. Tesseract 未找到
```bash
# Windows 设置环境变量
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe

# 或在代码中设置
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### 3. 验证码在 iframe 中
- 使用 `switch_to_frame` 切换到 iframe
- 完成验证后使用 `switch_to_default_content` 切换回主文档

### 4. 复杂验证码（如 reCAPTCHA）
- 使用 `wait_user` 等待手动完成
- 或使用 `save_cookies`/`load_cookies` 复用登录状态

### 5. 网络问题导致验证码加载失败
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

## 文件说明

- `selenium_flow_suite.py`: 主要的测试套件运行器，包含 OCR 功能
- `pytesseract_captcha_example.json`: 验证码识别示例配置
- `pytesseract_README.md`: 详细的使用说明
- `test_pytesseract.py`: OCR 功能测试脚本
- `requirements.txt`: Python 依赖列表

## 注意事项

1. **Tesseract 安装**：必须手动安装 Tesseract OCR 引擎
2. **图像质量**：验证码图片质量直接影响识别率
3. **预处理选择**：根据验证码类型选择合适的预处理方式
4. **重试机制**：复杂验证码可能需要多次重试
5. **Cookie 复用**：对于频繁访问的站点，建议使用 Cookie 复用

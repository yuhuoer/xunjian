# OCR 测试网站推荐

## 🎯 推荐的OCR测试网站

### 1. **简单文本验证码测试网站**

#### A. The Internet - Herokuapp
- **URL**: https://the-internet.herokuapp.com/
- **特点**: 提供各种Web自动化测试场景
- **验证码类型**: 基础登录表单（无验证码，适合基础测试）
- **推荐理由**: 稳定、免费、专门用于自动化测试

#### B. Dummy JSON API
- **URL**: https://dummyjson.com/
- **特点**: 提供测试用的API和表单
- **验证码类型**: 模拟登录场景
- **推荐理由**: 简单、稳定、适合开发测试

### 2. **验证码识别服务演示**

#### A. CapMonster Cloud 演示
- **URL**: https://capmonster.cloud/zh/Demo
- **特点**: 专业验证码识别服务的演示
- **验证码类型**: 多种类型验证码
- **推荐理由**: 真实验证码、多种类型

#### B. 土薯在线工具
- **URL**: https://toolshu.com/imgcode
- **特点**: 图形验证码识别工具
- **验证码类型**: 简单文本验证码
- **推荐理由**: 中文界面、简单易用

#### C. 超级鹰验证码识别
- **URL**: https://www.chaojiying.com/demo.html
- **特点**: 老牌验证码识别服务
- **验证码类型**: 各种复杂验证码
- **推荐理由**: 种类丰富、难度各异

### 3. **自建测试环境推荐**

#### A. 简单HTML验证码生成器
```html
<!DOCTYPE html>
<html>
<head>
    <title>验证码测试</title>
</head>
<body>
    <h2>验证码测试页面</h2>
    <form>
        <div>
            <label>用户名:</label>
            <input type="text" id="username" name="username">
        </div>
        <div>
            <label>密码:</label>
            <input type="password" id="password" name="password">
        </div>
        <div>
            <label>验证码:</label>
            <img id="captcha-img" src="https://dummyimage.com/120x40/000/fff&text=ABC123" alt="验证码">
            <input type="text" id="captcha-input" name="captcha">
        </div>
        <button type="submit" id="submit-btn">提交</button>
    </form>
</body>
</html>
```

## 🧪 测试配置文件

### 基础测试配置
我已经为你创建了以下测试配置文件：

1. **ocr_test_sites.json** - 包含多个验证码网站的测试流程
2. **simple_captcha_test.json** - 简单的登录表单测试

### 使用方法

#### 1. 测试基础功能
```bash
python xunjian/selenium_flow_suite.py --suite xunjian/simple_captcha_test.json --default-timeout 30
```

#### 2. 测试OCR功能
```bash
python xunjian/selenium_flow_suite.py --suite xunjian/ocr_test_sites.json --default-timeout 30
```

#### 3. 直接使用OCR模块测试
```python
from xunjian.selenium_ocr import ocr_captcha, CaptchaSolver
from xunjian.selenium_check import create_webdriver

# 创建浏览器实例
driver = create_webdriver(headless=False)

try:
    # 访问测试网站
    driver.get("https://capmonster.cloud/zh/Demo")
    
    # 等待页面加载
    time.sleep(3)
    
    # 尝试识别验证码
    captcha_text = ocr_captcha(driver, "img[alt*='captcha']", preprocessing="binary")
    print(f"识别结果: {captcha_text}")
    
finally:
    driver.quit()
```

## 📝 测试建议

### 1. **渐进式测试**
- 先测试简单的文本识别
- 再测试带干扰的验证码
- 最后测试复杂的图形验证码

### 2. **多种预处理方式**
```json
{
  "action": "ocr_captcha",
  "selector": "#captcha-img",
  "name": "captcha_text",
  "preprocessing": "binary"  // 尝试: "default", "binary", "grayscale", "denoise"
}
```

### 3. **截图对比**
在每个测试步骤中添加截图，便于调试：
```json
{
  "action": "screenshot",
  "path": "screenshots/before_ocr.png"
}
```

### 4. **错误处理测试**
测试OCR识别失败的情况：
```json
{
  "action": "solve_captcha",
  "captcha_selector": "#captcha-img",
  "input_selector": "#captcha-input",
  "max_attempts": 3
}
```

## ⚠️ 注意事项

1. **合法使用**: 仅用于学习和测试目的
2. **频率限制**: 避免过于频繁的请求
3. **网站变化**: 测试网站可能会更新，需要适时调整选择器
4. **依赖安装**: 确保已安装所有OCR依赖
5. **浏览器驱动**: 确保ChromeDriver版本匹配

## 🔧 故障排除

### 常见问题

1. **找不到验证码元素**
   - 检查选择器是否正确
   - 等待页面完全加载
   - 使用浏览器开发者工具确认元素

2. **OCR识别率低**
   - 尝试不同的预处理方式
   - 检查图片清晰度
   - 调整OCR配置参数

3. **网站访问失败**
   - 检查网络连接
   - 尝试其他测试网站
   - 使用代理或VPN

### 调试技巧

1. **启用详细日志**
2. **保存中间截图**
3. **逐步执行测试**
4. **对比不同预处理效果**

## 📚 扩展资源

- [Tesseract OCR 文档](https://tesseract-ocr.github.io/)
- [OpenCV 图像处理教程](https://opencv.org/courses/)
- [Selenium WebDriver 文档](https://selenium.dev/documentation/)
- [pytesseract 使用指南](https://pypi.org/project/pytesseract/)
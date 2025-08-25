# 🎯 Selenium 测试网站大全

## 🌟 专业测试网站推荐

### 1. **The Internet (Herokuapp)** ⭐⭐⭐⭐⭐
- **URL**: https://the-internet.herokuapp.com/
- **特点**: 专门为自动化测试设计的网站
- **测试场景**: 
  - 登录表单 (`/login`)
  - 动态加载 (`/dynamic_loading`)
  - 文件上传 (`/upload`)
  - 下拉菜单 (`/dropdown`)
  - 复选框 (`/checkboxes`)
  - 拖拽 (`/drag_and_drop`)
  - iframe (`/iframe`)
  - JavaScript 警告框 (`/javascript_alerts`)
- **推荐理由**: 功能全面、稳定可靠、免费使用

### 2. **Sauce Demo** ⭐⭐⭐⭐⭐
- **URL**: https://www.saucedemo.com/
- **特点**: 电商网站演示
- **测试场景**:
  - 用户登录
  - 商品浏览
  - 购物车操作
  - 结账流程
- **登录信息**: 
  - 用户名: `standard_user`
  - 密码: `secret_sauce`

### 3. **DemoQA** ⭐⭐⭐⭐
- **URL**: https://demoqa.com/
- **特点**: 丰富的UI元素测试
- **测试场景**:
  - 表单元素 (`/elements`)
  - 交互操作 (`/interaction`)
  - 弹窗处理 (`/alerts`)
  - 拖拽操作 (`/droppable`)
  - 表格操作 (`/webtables`)

### 4. **WebDriver University** ⭐⭐⭐⭐
- **URL**: http://www.webdriveruniversity.com/
- **特点**: 教育性测试网站
- **测试场景**:
  - 联系表单 (`/Contact-Us/contactus.html`)
  - 登录页面 (`/Login-Portal/index.html`)
  - 按钮点击 (`/Click-Buttons/index.html`)
  - 下拉菜单 (`/Dropdown-Checkboxes-RadioButtons/index.html`)

### 5. **Automation Practice** ⭐⭐⭐
- **URL**: http://automationpractice.com/
- **特点**: 完整的电商网站
- **测试场景**:
  - 用户注册登录
  - 商品搜索
  - 购物流程
  - 用户账户管理

### 6. **OrangeHRM Demo** ⭐⭐⭐⭐
- **URL**: https://opensource-demo.orangehrmlive.com/
- **特点**: 企业级HR管理系统
- **测试场景**:
  - 员工管理
  - 系统管理
  - 报表功能
- **登录信息**:
  - 用户名: `Admin`
  - 密码: `admin123`

### 7. **ParaBank** ⭐⭐⭐
- **URL**: https://parabank.parasoft.com/
- **特点**: 银行业务演示网站
- **测试场景**:
  - 账户管理
  - 转账操作
  - 贷款申请

## 🧪 测试配置文件

我已经为你创建了两个测试配置文件：

### 1. `selenium_test_sites.json` - 基础测试
包含以下测试流程：
- The Internet 登录测试
- Sauce Demo 登录和购物车测试
- DemoQA 元素交互测试
- WebDriver University 联系表单测试
- Automation Practice 搜索测试

### 2. `advanced_selenium_tests.json` - 高级测试
包含以下高级场景：
- 动态内容加载
- 文件上传
- 下拉菜单操作
- 复选框操作
- 拖拽操作
- 弹窗处理

## 🚀 使用方法

### 运行基础测试
```bash
python xunjian/selenium_flow_suite.py --suite xunjian/selenium_test_sites.json --default-timeout 20
```

### 运行高级测试
```bash
python xunjian/selenium_flow_suite.py --suite xunjian/advanced_selenium_tests.json --default-timeout 30
```

### 单独测试某个网站
```bash
# 只测试 The Internet 网站
python xunjian/selenium_flow_suite.py --suite xunjian/selenium_test_sites.json --stop-on-fail
```

## 📋 测试场景分类

### 🔰 **初学者推荐**
1. **The Internet - Login**: 基础登录表单
2. **Sauce Demo**: 简单电商操作
3. **DemoQA - Text Box**: 表单填写

### 🔥 **中级练习**
1. **The Internet - Dynamic Loading**: 等待动态内容
2. **DemoQA - Drag Drop**: 拖拽操作
3. **WebDriver University**: 多种表单元素

### 💪 **高级挑战**
1. **OrangeHRM**: 企业级应用测试
2. **ParaBank**: 复杂业务流程
3. **Automation Practice**: 完整电商流程

## 🎨 自定义测试场景

### 基础模板
```json
{
  "name": "custom-test",
  "variables": {
    "base_url": "https://example.com",
    "username": "testuser"
  },
  "steps": [
    { "action": "goto", "url": "${base_url}" },
    { "action": "wait_visible", "selector": "#element", "timeout": 10 },
    { "action": "type", "selector": "#input", "text": "${username}" },
    { "action": "click", "selector": "#submit" },
    { "action": "screenshot", "path": "screenshots/result.png" }
  ]
}
```

### 常用选择器
```json
{
  "登录表单": {
    "用户名": "#username, input[name='username'], input[type='email']",
    "密码": "#password, input[name='password'], input[type='password']",
    "提交": "#submit, button[type='submit'], input[type='submit']"
  },
  "搜索功能": {
    "搜索框": "#search, input[name='search'], .search-input",
    "搜索按钮": ".search-btn, button[type='submit'], #search-submit"
  }
}
```

## ⚠️ 注意事项

### 网站可用性
- ✅ **The Internet**: 高可用性，推荐首选
- ✅ **Sauce Demo**: 稳定可靠
- ✅ **DemoQA**: 功能丰富
- ⚠️ **Automation Practice**: 偶尔不稳定
- ⚠️ **WebDriver University**: 加载较慢

### 使用建议
1. **从简单开始**: 先用 The Internet 练习基础操作
2. **渐进学习**: 逐步尝试更复杂的场景
3. **保存截图**: 便于调试和验证结果
4. **合理等待**: 设置适当的超时时间
5. **错误处理**: 准备好处理网络问题

### 最佳实践
```json
{
  "steps": [
    { "action": "goto", "url": "https://example.com" },
    { "action": "wait_visible", "selector": "#element", "timeout": 10 },
    { "action": "screenshot", "path": "screenshots/before_action.png" },
    { "action": "click", "selector": "#element" },
    { "action": "wait_visible", "selector": "#result", "timeout": 15 },
    { "action": "screenshot", "path": "screenshots/after_action.png" },
    { "action": "assert_page_contains", "text": "Expected Result" }
  ]
}
```

## 🔗 扩展资源

- [Selenium 官方文档](https://selenium.dev/documentation/)
- [WebDriver 规范](https://w3c.github.io/webdriver/)
- [CSS 选择器参考](https://www.w3schools.com/cssref/css_selectors.asp)
- [XPath 教程](https://www.w3schools.com/xml/xpath_intro.asp)

这些网站为你提供了从基础到高级的完整 Selenium 测试练习环境！
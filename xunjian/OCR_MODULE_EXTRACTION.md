# OCR 模块提取说明

## 概述

已成功将 `selenium_flow_suite.py` 中的 OCR 相关功能提取到独立的 `selenium_ocr.py` 模块中，实现了代码的模块化和解耦。

## 文件结构

### 新增文件
- `selenium_ocr.py` - 独立的 OCR 功能模块

### 修改文件
- `selenium_flow_suite.py` - 移除 OCR 代码，导入新模块

## selenium_ocr.py 模块详情

### 主要功能

#### 1. **依赖检查**
```python
def is_ocr_available() -> bool
def get_ocr_dependencies_error() -> str
```

#### 2. **图像处理**
```python
def preprocess_image(img_cv: np.ndarray, preprocessing: str = "default") -> np.ndarray
def ocr_recognize_text(img_cv: np.ndarray, config: Optional[str] = None) -> str
def extract_captcha_image(driver, captcha_selector: str, timeout: int = 10) -> Image.Image
```

#### 3. **验证码识别**
```python
def ocr_captcha(driver, captcha_selector: str, preprocessing: str = "default", 
                timeout: int = 10, config: Optional[str] = None) -> str
```

#### 4. **自动验证码解决**
```python
def solve_simple_captcha(driver, captcha_selector: str, input_selector: str, 
                        submit_selector: Optional[str] = None, max_attempts: int = 3,
                        preprocessing: str = "default", from_selenium_check=None) -> bool
```

#### 5. **验证码解决器类**
```python
class CaptchaSolver:
    def __init__(self, driver, selenium_check_funcs=None)
    def recognize(self, captcha_selector: str, ...) -> str
    def solve(self, captcha_selector: str, input_selector: str, ...) -> bool
    def extract_image(self, captcha_selector: str, ...) -> Image.Image
    def preprocess(self, img_cv: np.ndarray, method: str = "default") -> np.ndarray
```

### 支持的预处理方式
- `"default"` - 默认灰度处理
- `"binary"` - 二值化处理
- `"grayscale"` - 灰度处理
- `"denoise"` - 去噪处理

## selenium_flow_suite.py 修改

### 移除的代码
- OCR 库导入 (`cv2`, `numpy`, `PIL`, `pytesseract`)
- `_ocr_captcha()` 函数
- `_solve_simple_captcha()` 函数

### 新增的导入
```python
from selenium_ocr import (
    is_ocr_available,
    ocr_captcha,
    solve_simple_captcha,
    CaptchaSolver
)
```

### 修改的操作
- `ocr_captcha` 操作：调用新模块的 `ocr_captcha` 函数
- `solve_captcha` 操作：调用新模块的 `solve_simple_captcha` 函数，并传递必要的函数引用

## 使用方式

### 1. 在 selenium_flow_suite.py 中使用（无变化）
JSON 配置文件的使用方式完全不变：

```json
{
  "steps": [
    {
      "action": "ocr_captcha",
      "selector": "#captcha-img",
      "name": "captcha_text",
      "preprocessing": "binary"
    },
    {
      "action": "solve_captcha",
      "captcha_selector": "#captcha-img",
      "input_selector": "#captcha-input",
      "submit_selector": "#submit-btn",
      "max_attempts": 3,
      "preprocessing": "binary"
    }
  ]
}
```

### 2. 直接使用 OCR 模块
```python
from xunjian.selenium_ocr import ocr_captcha, CaptchaSolver

# 方式1：直接调用函数
captcha_text = ocr_captcha(driver, "#captcha-img", preprocessing="binary")

# 方式2：使用类
solver = CaptchaSolver(driver, selenium_check_funcs)
captcha_text = solver.recognize("#captcha-img", preprocessing="binary")
success = solver.solve("#captcha-img", "#captcha-input", "#submit-btn")
```

## 依赖要求

### OCR 功能依赖
```bash
pip install pillow pytesseract opencv-python numpy
```

### 系统依赖
- Tesseract OCR 引擎需要单独安装

## 兼容性

### 向后兼容
- 所有原有的 JSON 配置文件无需修改
- 所有原有的功能接口保持不变
- 原有的命令行参数和使用方式完全兼容

### 新功能
- 可以独立使用 OCR 模块
- 支持更灵活的验证码处理
- 便于扩展和维护

## 优势

1. **模块化设计** - OCR 功能独立，便于维护和测试
2. **代码复用** - OCR 模块可在其他项目中使用
3. **职责分离** - 主流程和 OCR 功能解耦
4. **易于扩展** - 新的 OCR 功能可以独立添加
5. **向后兼容** - 现有使用方式无需改变

## 测试验证

使用提供的测试脚本验证提取是否成功：
```bash
python3 test_ocr_structure.py
```

测试内容包括：
- 语法检查
- 模块结构验证
- 函数和类存在性检查
- 导入关系验证

## 注意事项

1. **函数引用传递** - `solve_simple_captcha` 需要传递 `selenium_check` 模块的函数引用
2. **错误处理** - 保持了原有的错误处理逻辑
3. **日志输出** - 保持了原有的日志输出格式
4. **超时设置** - 保持了原有的超时机制
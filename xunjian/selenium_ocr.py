"""
Selenium OCR 模块
提供验证码识别和自动处理功能

依赖:
- pip install pillow pytesseract opencv-python numpy
- 需要安装 Tesseract OCR 引擎
"""

import base64
import io
import re
import time
from typing import Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_check import _resolve_locator

# OCR imports with availability check
try:
    import cv2
    import numpy as np
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def is_ocr_available() -> bool:
    """检查OCR依赖是否可用"""
    return OCR_AVAILABLE


def get_ocr_dependencies_error() -> str:
    """获取OCR依赖缺失的错误信息"""
    return "OCR libraries not available. Install: pip install pillow pytesseract opencv-python numpy"


def preprocess_image(img_cv: np.ndarray, preprocessing: str = "default") -> np.ndarray:
    """图像预处理
    
    Args:
        img_cv: OpenCV格式的图像数组
        preprocessing: 预处理方式 ("default", "binary", "grayscale", "denoise")
        
    Returns:
        np.ndarray: 预处理后的图像
    """
    if preprocessing == "binary":
        # 二值化处理
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary
    elif preprocessing == "grayscale":
        # 灰度处理
        return cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    elif preprocessing == "denoise":
        # 去噪处理
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        return cv2.fastNlMeansDenoising(gray)
    else:
        # 默认处理：转灰度
        return cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)


def ocr_recognize_text(img_cv: np.ndarray, config: Optional[str] = None) -> str:
    """使用pytesseract识别图像中的文本
    
    Args:
        img_cv: OpenCV格式的图像数组
        config: pytesseract配置字符串
        
    Returns:
        str: 识别出的文本
    """
    if config is None:
        config = '--oem 3 --psm 8 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    
    result = pytesseract.image_to_string(img_cv, config=config)
    # 清理结果，只保留字母和数字
    return re.sub(r'[^a-zA-Z0-9]', '', result.strip())


def extract_captcha_image(driver, captcha_selector: str, timeout: int = 10) -> Image.Image:
    """从网页元素提取验证码图片
    
    Args:
        driver: WebDriver实例
        captcha_selector: 验证码图片的选择器
        timeout: 等待超时时间
        
    Returns:
        PIL.Image: 验证码图片对象
        
    Raises:
        Exception: 当找不到元素或提取图片失败时
    """
    # 找到验证码图片元素
    by, value = _resolve_locator(captcha_selector)
    captcha_element = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )
    
    # 获取图片的base64数据或截图
    img_src = captcha_element.get_attribute("src")
    if img_src and img_src.startswith("data:image"):
        # 处理base64图片
        img_data = base64.b64decode(img_src.split(",")[1])
        return Image.open(io.BytesIO(img_data))
    else:
        # 截图验证码区域
        return Image.open(io.BytesIO(captcha_element.screenshot_as_png))


def ocr_captcha(driver, captcha_selector: str, preprocessing: str = "default", 
                timeout: int = 10, config: Optional[str] = None) -> str:
    """使用 pytesseract 识别验证码
    
    Args:
        driver: WebDriver实例
        captcha_selector: 验证码图片的选择器
        preprocessing: 图像预处理方式 ("default", "binary", "grayscale", "denoise")
        timeout: 等待元素超时时间
        config: pytesseract配置字符串
        
    Returns:
        str: 识别出的验证码文本
        
    Raises:
        RuntimeError: 当OCR库不可用时
    """
    if not OCR_AVAILABLE:
        raise RuntimeError(get_ocr_dependencies_error())
    
    try:
        # 提取验证码图片
        img = extract_captcha_image(driver, captcha_selector, timeout)
        
        # 转换为OpenCV格式
        img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        
        # 图像预处理
        processed_img = preprocess_image(img_cv, preprocessing)
        
        # OCR识别
        captcha_text = ocr_recognize_text(processed_img, config)
        
        print(f"pytesseract 识别验证码: {captcha_text}")
        return captcha_text
        
    except Exception as e:
        print(f"OCR识别失败: {e}")
        return ""


def solve_simple_captcha(driver, captcha_selector: str, input_selector: str, 
                        submit_selector: Optional[str] = None, max_attempts: int = 3,
                        preprocessing: str = "default", from_selenium_check=None) -> bool:
    """自动解决简单验证码
    
    Args:
        driver: WebDriver实例
        captcha_selector: 验证码图片选择器
        input_selector: 验证码输入框选择器
        submit_selector: 提交按钮选择器（可选）
        max_attempts: 最大尝试次数
        preprocessing: 图像预处理方式
        from_selenium_check: selenium_check模块的函数引用 (get_body_text, _type, _click)
        
    Returns:
        bool: 是否成功解决验证码
    """
    if from_selenium_check is None:
        raise ValueError("需要提供selenium_check模块的函数引用")
    
    get_body_text, _type, _click = from_selenium_check
    
    for attempt in range(max_attempts):
        try:
            # 识别验证码
            captcha_text = ocr_captcha(driver, captcha_selector, preprocessing)
            if not captcha_text:
                print(f"第{attempt + 1}次尝试：无法识别验证码")
                continue
            
            # 输入验证码
            _type(driver, input_selector, captcha_text, 10)
            
            # 如果有提交按钮，点击提交
            if submit_selector:
                _click(driver, submit_selector, 10)
            
            # 等待一下看是否成功
            time.sleep(2)
            
            # 检查是否还有验证码错误提示
            page_text = get_body_text(driver)
            if "验证码" in page_text and ("错误" in page_text or "invalid" in page_text.lower()):
                print(f"第{attempt + 1}次尝试：验证码错误，重试")
                continue
            
            print(f"验证码识别成功：{captcha_text}")
            return True
            
        except Exception as e:
            print(f"第{attempt + 1}次尝试失败：{e}")
            continue
    
    print("验证码识别失败，达到最大尝试次数")
    return False


class CaptchaSolver:
    """验证码解决器类，提供更高级的验证码处理功能"""
    
    def __init__(self, driver, selenium_check_funcs=None):
        """初始化验证码解决器
        
        Args:
            driver: WebDriver实例
            selenium_check_funcs: selenium_check模块的函数引用
        """
        self.driver = driver
        self.selenium_check_funcs = selenium_check_funcs
        
        if not OCR_AVAILABLE:
            raise RuntimeError(get_ocr_dependencies_error())
    
    def recognize(self, captcha_selector: str, preprocessing: str = "default", 
                  timeout: int = 10, config: Optional[str] = None) -> str:
        """识别验证码"""
        return ocr_captcha(self.driver, captcha_selector, preprocessing, timeout, config)
    
    def solve(self, captcha_selector: str, input_selector: str, 
              submit_selector: Optional[str] = None, max_attempts: int = 3,
              preprocessing: str = "default") -> bool:
        """自动解决验证码"""
        if self.selenium_check_funcs is None:
            raise ValueError("需要提供selenium_check模块的函数引用")
        
        return solve_simple_captcha(
            self.driver, captcha_selector, input_selector, submit_selector,
            max_attempts, preprocessing, self.selenium_check_funcs
        )
    
    def extract_image(self, captcha_selector: str, timeout: int = 10) -> Image.Image:
        """提取验证码图片"""
        return extract_captcha_image(self.driver, captcha_selector, timeout)
    
    def preprocess(self, img_cv: np.ndarray, method: str = "default") -> np.ndarray:
        """预处理图像"""
        return preprocess_image(img_cv, method)
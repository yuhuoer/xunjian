#!/usr/bin/env python3
"""
测试 pytesseract OCR 功能是否正常工作
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from selenium_flow_suite import OCR_AVAILABLE, _ocr_captcha
    print("✓ OCR 功能已成功导入")
    
    if OCR_AVAILABLE:
        print("✓ 所有 OCR 依赖库已安装")
        print("  - OpenCV (cv2): ✓")
        print("  - NumPy: ✓") 
        print("  - Pillow (PIL): ✓")
        print("  - pytesseract: ✓")
        
        # 测试 pytesseract 是否可用
        try:
            import pytesseract
            version = pytesseract.get_tesseract_version()
            print(f"✓ Tesseract 版本: {version}")
        except Exception as e:
            print(f"✗ Tesseract 不可用: {e}")
            print("  请安装 Tesseract OCR 引擎:")
            print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("  macOS: brew install tesseract")
            print("  Ubuntu: sudo apt-get install tesseract-ocr")
            
    else:
        print("✗ OCR 依赖库未安装")
        print("请运行: pip install pillow pytesseract opencv-python numpy")
        
except ImportError as e:
    print(f"✗ 导入错误: {e}")
    print("请确保所有依赖已正确安装")

if __name__ == "__main__":
    print("pytesseract OCR 功能测试完成")

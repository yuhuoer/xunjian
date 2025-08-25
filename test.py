from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time
import json
from datetime import datetime

class SeleniumMonitor:
    def __init__(self, headless=True):
        self.setup_driver(headless)
        # self.results = []
    
    def setup_driver(self, headless):
        """设置浏览器驱动"""
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
    
    def check_login_flow(self, login_url, username, password, success_indicator):
        """检查登录流程"""
        result = {
            'test': 'login_flow',
            'url': login_url,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'error': None
        }
        
        try:
            # 访问登录页面
            self.driver.get(login_url)
            
            # 等待页面加载
            time.sleep(2)
            
            # 查找并填写用户名
            username_input = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_input.send_keys(username)
            
            # 查找并填写密码
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)
            
            # 点击登录按钮
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # 等待并检查登录结果
            time.sleep(3)
            
            if success_indicator in self.driver.page_source:
                result['status'] = 'success'
            else:
                result['status'] = 'login_failed'
                result['error'] = 'Login success indicator not found'
                
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def check_form_submission(self, form_url, form_data):
        """检查表单提交"""
        result = {
            'test': 'form_submission',
            'url': form_url,
            'timestamp': datetime.now().isoformat(),
            'status': 'unknown',
            'error': None
        }
        
        try:
            self.driver.get(form_url)
            time.sleep(2)
            
            # 填写表单
            for field_name, value in form_data.items():
                field = self.driver.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
            
            # 提交表单
            submit_button = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            submit_button.click()
            
            time.sleep(3)
            result['status'] = 'success'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def run_checks(self, test_cases):
        """运行所有检查"""
        for test_case in test_cases:
            test_type = test_case['type']
            
            if test_type == 'login':
                result = self.check_login_flow(
                    test_case['url'],
                    test_case['username'],
                    test_case['password'],
                    test_case['success_indicator']
                )
            elif test_type == 'form':
                result = self.check_form_submission(
                    test_case['url'],
                    test_case['form_data']
                )
            
            self.results.append(result)
            
            # 打印结果
            status_color = "✅" if result['status'] == 'success' else "❌"
            print(f"{status_color} {result['test']} - {result['status']}")
            
            if result['error']:
                print(f"   错误: {result['error']}")
    
    def close(self):
        """关闭浏览器"""
        self.driver.quit()
    
    def save_results(self, filename='selenium_results.json'):
        """保存结果"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

# 使用示例
if __name__ == "__main__":
    test_cases = [
        {
            'type': 'login',
            'url': 'https://walkthrough.mabl.com/',
            'username': 'QUALITY',
            'password': 'demo123',
            'success_indicator': 'Dashboard'
        }
    ]
    
    monitor = SeleniumMonitor(headless=False)
    try:
        monitor.run_checks(test_cases)
        monitor.save_results()
    finally:
        monitor.close()
import sys
import re
import os
import argparse
import time
from typing import Optional, Tuple, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


def _create_webdriver(headless: bool, chromedriver_path: Optional[str] = None) -> webdriver.Chrome:

    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Prefer a locally provided chromedriver path (works offline)
    if chromedriver_path and os.path.exists(chromedriver_path):
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(60)
        return driver

    # Use Selenium Manager (Chrome must be installed)
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)
    return driver


def _resolve_locator(selector: str) -> Tuple[str, str]:
    """Infer locator strategy from the selector string.

    - If starts with 'xpath=' use XPath after '='
    - If starts with 'css=' use CSS after '='
    - If starts with '//' or './/' treat as XPath
    - Otherwise default to CSS selector
    """
    if not selector:
        raise ValueError("Empty selector is not allowed")
    sel = selector.strip()
    lower = sel.lower()
    if lower.startswith("xpath="):
        return By.XPATH, sel.split("=", 1)[1]
    if lower.startswith("css="):
        return By.CSS_SELECTOR, sel.split("=", 1)[1]
    if sel.startswith("//") or sel.startswith(".//"):
        return By.XPATH, sel
    return By.CSS_SELECTOR, sel

def _get_body_text(driver: webdriver.Chrome) -> str:

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text or ""
    except Exception:
        return driver.page_source or ""

def _contains_error_keyword(text: str) -> bool:

    if not text:
        return False
    # Case-insensitive search for the keyword 'ERROR'
    return re.search(r"\berror\b", text, flags=re.IGNORECASE) is not None

def _wait_presence(driver, selector: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def _wait_visible(driver, selector: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))


def _wait_clickable(driver, selector: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))

def _type(driver, selector: str, text: str, timeout: int) -> None:

	by, value = _resolve_locator(selector)
	element = WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, value)))
	element.clear()
	element.send_keys(text)

def _click(driver, selector: str, timeout: int) -> None:

	by, value = _resolve_locator(selector)
	element = WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((by, value)))
	element.click()

def _interpolate(text: str, variables: Dict[str, Any]) -> str:

	if text is None:
		return text

	def repl(match: re.Match) -> str:
		key = match.group(1)
		value = variables.get(key, "")
		return str(value)

	return re.sub(r"\$\{([^}]+)\}", repl, text)

def _wait_user(msg: str, step):
    msg = "请在浏览器内完成验证码后按回车继续..."
    try:
        input(msg)
    except EOFError:
        # 在CI环境中回退为固定等待
        time.sleep(float(step.get("seconds", 30)))
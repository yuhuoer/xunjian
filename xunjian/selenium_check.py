import sys
import re
import os
import argparse
import time
from typing import Optional, Tuple
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException


def create_webdriver(headless: bool, chromedriver_path: Optional[str] = None) -> webdriver.Chrome:

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


def wait_and_type(driver: webdriver.Chrome, selector: str, text: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    element = WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((by, value))
    )
    element.clear()
    element.send_keys(text)


def wait_and_click(driver: webdriver.Chrome, selector: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )
    element.click()


def wait_for_presence(driver: webdriver.Chrome, selector: str, timeout: int) -> None:

    by, value = _resolve_locator(selector)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def get_body_text(driver: webdriver.Chrome) -> str:

    try:
        body = driver.find_element(By.TAG_NAME, "body")
        return body.text or ""
    except Exception:
        return driver.page_source or ""


def contains_error_keyword(text: str) -> bool:

    if not text:
        return False
    # Case-insensitive search for the keyword 'ERROR'
    return re.search(r"\berror\b", text, flags=re.IGNORECASE) is not None


def run_flow(
    url: str,
    username: str,
    password: str,
    username_selector: str,
    password_selector: str,
    submit_selector: str,
    feature_selector: str,
    after_login_wait_selector: Optional[str],
    post_click_wait_selector: Optional[str],
    timeout: int,
    headless: bool,
    chromedriver_path: Optional[str] = None,
) -> int:

    driver: Optional[webdriver.Chrome] = None
    try:
        driver = create_webdriver(headless=headless, chromedriver_path=chromedriver_path)
        driver.get(url)

        wait_and_type(driver, username_selector, username, timeout)
        wait_and_type(driver, password_selector, password, timeout)
        wait_and_click(driver, submit_selector, timeout)

        if after_login_wait_selector:
            wait_for_presence(driver, after_login_wait_selector, timeout)

        if feature_selector:
            wait_and_click(driver, feature_selector, timeout)

        if post_click_wait_selector:
            wait_for_presence(driver, post_click_wait_selector, timeout)

        page_text = get_body_text(driver)
        if contains_error_keyword(page_text):
            print("Found ERROR keyword on the page.")
            return 1
        else:
            print("No ERROR keyword found on the page.")
            return 0

    except (TimeoutException, NoSuchElementException) as sel_err:
        print(f"Selenium element/timeout error: {sel_err}", file=sys.stderr)
        return 2
    except WebDriverException as wd_err:
        print(f"WebDriver error: {wd_err}", file=sys.stderr)
        return 3
    except Exception as unexpected:
        print(f"Unexpected error: {unexpected}", file=sys.stderr)
        return 4
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:
                pass


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Use Selenium to login, navigate by clicking a specific element, and check the page for the keyword 'ERROR'."
        )
    )

    parser.add_argument("--url", required=True, help="Login page URL")
    parser.add_argument("--username", required=True, help="Login username")
    parser.add_argument("--password", required=True, help="Login password")

    parser.add_argument(
        "--username-selector",
        required=True,
        help="CSS selector for the username input",
    )
    parser.add_argument(
        "--password-selector",
        required=True,
        help="CSS selector for the password input",
    )
    parser.add_argument(
        "--submit-selector",
        required=True,
        help="CSS selector for the login submit button",
    )

    parser.add_argument(
        "--feature-selector",
        required=True,
        help=(
            "CSS selector for the element to click after logging in (navigates to the target feature)"
        ),
    )

    parser.add_argument(
        "--after-login-wait-selector",
        required=False,
        default=None,
        help="Optional CSS selector to wait for after successful login",
    )
    parser.add_argument(
        "--post-click-wait-selector",
        required=False,
        default=None,
        help="Optional CSS selector to wait for after clicking the feature element",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=20,
        help="Max wait time in seconds for each step (default: 20)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chrome in headless mode",
    )

    parser.add_argument(
        "--chromedriver-path",
        required=False,
        default=os.environ.get("CHROMEDRIVER"),
        help="Path to local chromedriver executable (useful for offline environments)",
    )

    return parser.parse_args()


def main() -> None:

    url = "https://www.saucedemo.com/"
    username = "standard_user"
    password = "secret_sauce"
    username_selector = "#user-name"
    password_selector = "#password"
    submit_selector = "#login-button"
    feature_selector = "#add-to-cart-sauce-labs-backpack"
    after_login_wait_selector = ""
    post_click_wait_selector = ""
    timeout = 20
    headless = False
    exit_code = run_flow(
        url=url,
        username=username,
        password=password,
        username_selector=username_selector,
        password_selector=password_selector,
        submit_selector=submit_selector,
        feature_selector=feature_selector, 
        after_login_wait_selector=after_login_wait_selector,
        post_click_wait_selector=post_click_wait_selector,
        timeout=timeout,
        headless=headless,
    )
    sys.exit(exit_code)

    #args = parse_args()
    #exit_code = run_flow(
    #    url=args.url,
    #    username=args.username,
    #    password=args.password,
    #    username_selector=args.username_selector,
    #    password_selector=args.password_selector,
    #    submit_selector=args.submit_selector,
    #    feature_selector=args.feature_selector,
    #    after_login_wait_selector=args.after_login_wait_selector,
    #    post_click_wait_selector=args.post_click_wait_selector,
    #    timeout=args.timeout,
    #    headless=args.headless,
    #)
    #sys.exit(exit_code)


if __name__ == "__main__":

    main()



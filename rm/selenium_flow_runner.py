import argparse
import json
import os
import re
import sys
import time
from typing import Any, Dict, Optional, Tuple

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from selenium_check import (
    create_webdriver,
    get_body_text,
    contains_error_keyword,
)


def _resolve_locator(selector: str) -> Tuple[str, str]:

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


def _get_case_field(case: Dict[str, Any], key: str, default: Any = None) -> Any:

    return case[key] if key in case else default


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Run a configurable Selenium flow defined by a JSON file. "
            "Supports actions: goto, type, click, wait_presence, wait_visible, wait_clickable, sleep, "
            "assert_page_contains, assert_page_not_contains, assert_element_contains, assert_element_not_contains, "
            "check_error_keyword, screenshot, save_source."
        )
    )

    parser.add_argument("--flow", required=True, help="Path to JSON flow file")
    parser.add_argument(
        "--headless", action="store_true", help="Override: run Chrome in headless mode"
    )
    parser.add_argument(
        "--timeout", type=int, default=None, help="Override: default step timeout seconds"
    )
    parser.add_argument(
        "--chromedriver-path",
        required=False,
        default=os.environ.get("CHROMEDRIVER"),
        help="Path to local chromedriver (optional). If omitted, Selenium Manager is used.",
    )

    return parser.parse_args()


def load_flow(flow_path: str) -> Dict[str, Any]:

    if not os.path.exists(flow_path):
        raise FileNotFoundError(f"Flow file not found: {flow_path}")
    with open(flow_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Flow must be a JSON object with keys: steps, variables, headless, timeout, etc.")
    if "steps" not in data or not isinstance(data["steps"], list):
        raise ValueError("Flow JSON must contain a 'steps' array")
    return data


def run_flow_steps(flow: Dict[str, Any], cli_overrides: argparse.Namespace) -> int:

    variables: Dict[str, Any] = flow.get("variables", {}) or {}
    default_timeout: int = (
        cli_overrides.timeout if cli_overrides.timeout is not None else int(flow.get("timeout", 20))
    )
    headless: bool = bool(cli_overrides.headless or flow.get("headless", False))
    chromedriver_path: Optional[str] = (
        cli_overrides.chromedriver_path if cli_overrides.chromedriver_path else flow.get("chromedriver_path")
    )

    driver = None
    try:
        driver = create_webdriver(headless=headless, chromedriver_path=chromedriver_path)

        for idx, step in enumerate(flow["steps"]):
            action = step.get("action")
            if not action:
                raise ValueError(f"Step {idx+1} missing 'action'")

            step_timeout = int(step.get("timeout", default_timeout))
            # Interpolate common params
            selector = _interpolate(step.get("selector"), variables) if step.get("selector") else None
            url = _interpolate(step.get("url"), variables) if step.get("url") else None
            text = _interpolate(step.get("text"), variables) if step.get("text") else None
            value = _interpolate(step.get("value"), variables) if step.get("value") else None
            path = _interpolate(step.get("path"), variables) if step.get("path") else None

            if action == "goto":
                if not url:
                    raise ValueError("goto requires 'url'")
                driver.get(url)

            elif action == "type":
                if not selector:
                    raise ValueError("type requires 'selector'")
                _type(driver, selector, text or "", step_timeout)

            elif action == "click":
                if not selector:
                    raise ValueError("click requires 'selector'")
                _click(driver, selector, step_timeout)

            elif action == "wait_presence":
                if not selector:
                    raise ValueError("wait_presence requires 'selector'")
                _wait_presence(driver, selector, step_timeout)

            elif action == "wait_visible":
                if not selector:
                    raise ValueError("wait_visible requires 'selector'")
                _wait_visible(driver, selector, step_timeout)

            elif action == "wait_clickable":
                if not selector:
                    raise ValueError("wait_clickable requires 'selector'")
                _wait_clickable(driver, selector, step_timeout)

            elif action == "sleep":
                seconds = float(step.get("seconds", 1))
                time.sleep(seconds)

            elif action == "assert_page_contains":
                needle = text or value
                if not needle:
                    raise ValueError("assert_page_contains requires 'text' or 'value'")
                page_text = get_body_text(driver)
                if needle not in page_text:
                    print(f"Assertion failed: page does not contain '{needle}'", file=sys.stderr)
                    return 1

            elif action == "assert_page_not_contains":
                needle = text or value
                if not needle:
                    raise ValueError("assert_page_not_contains requires 'text' or 'value'")
                page_text = get_body_text(driver)
                if needle in page_text:
                    print(f"Assertion failed: page unexpectedly contains '{needle}'", file=sys.stderr)
                    return 1

            elif action == "assert_element_contains":
                if not selector:
                    raise ValueError("assert_element_contains requires 'selector'")
                needle = text or value
                if not needle:
                    raise ValueError("assert_element_contains requires 'text' or 'value'")
                by, val = _resolve_locator(selector)
                element = WebDriverWait(driver, step_timeout).until(EC.visibility_of_element_located((by, val)))
                if needle not in (element.text or ""):
                    print(f"Assertion failed: element text does not contain '{needle}'", file=sys.stderr)
                    return 1

            elif action == "assert_element_not_contains":
                if not selector:
                    raise ValueError("assert_element_not_contains requires 'selector'")
                needle = text or value
                if not needle:
                    raise ValueError("assert_element_not_contains requires 'text' or 'value'")
                by, val = _resolve_locator(selector)
                element = WebDriverWait(driver, step_timeout).until(EC.visibility_of_element_located((by, val)))
                if needle in (element.text or ""):
                    print(f"Assertion failed: element text unexpectedly contains '{needle}'", file=sys.stderr)
                    return 1

            elif action == "check_error_keyword":
                page_text = get_body_text(driver)
                if contains_error_keyword(page_text):
                    print("Found ERROR keyword on the page.")
                    return 1

            elif action == "screenshot":
                if not path:
                    raise ValueError("screenshot requires 'path'")
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                driver.save_screenshot(path)

            elif action == "save_source":
                if not path:
                    raise ValueError("save_source requires 'path'")
                os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(driver.page_source or "")

            elif action == "set_var":
                # Set or override variable at runtime, e.g., {"action":"set_var","name":"token","value":"${some}"}
                name = step.get("name")
                if not name:
                    raise ValueError("set_var requires 'name'")
                variables[name] = text or value or ""

            else:
                raise ValueError(f"Unsupported action: {action}")

        # Completed all steps successfully
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


def main() -> None:

    args = parse_args()
    flow = load_flow(args.flow)
    exit_code = run_flow_steps(flow, args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()



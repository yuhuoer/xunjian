import argparse
import json
import os
import re
import sys
import time

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# OCR module import
from selenium_ocr import (
    is_ocr_available,
    ocr_captcha,
    solve_simple_captcha,
    CaptchaSolver
)

OCR_AVAILABLE = is_ocr_available()

from selenium_check import (
	_create_webdriver,
	_get_body_text,
	_contains_error_keyword,
	_resolve_locator,
	_type,
	_click,
	_interpolate,
	_wait_presence,
	_wait_visible,
	_wait_clickable
	
)


STATUS_BY_CODE: Dict[int, str] = {
    0: "PASS_NO_ERROR_FOUND", # 巡检通过
    1: "ERROR_KEYWORD_FOUND", # 巡检发现失败关键词
    2: "SELENIUM_TIMEOUT_OR_NO_SUCH_ELEMENT", # SELENIUM超时或没有找到对应元素
    3: "WEBDRIVER_ERROR", # WEBDRIVER驱动错误
    4: "UNEXPECTED_ERROR", # 未预知的错误
}


def parse_args() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Run multiple configurable Selenium flows defined in a single JSON file. "
            "The JSON can be either an array of flow objects, or an object with optional defaults and a 'flows' array."
        )
    )

    parser.add_argument("--suite", required=True, help="Path to suite JSON file")
    parser.add_argument("--output", default="selenium_results.json", help="Path to write JSON report")
    parser.add_argument("--headless", action="store_true", help="Default headless when a flow omits it")
    parser.add_argument("--default-timeout", type=int, default=20, help="Default per-step timeout seconds")
    parser.add_argument("--chromedriver-path",default=os.environ.get("CHROMEDRIVER"),
        help="Default local chromedriver path for all flows (each flow can override)",
    )
    parser.add_argument("--stop-on-fail", action="store_true", help="Stop after the first non-zero exit code")

    return parser.parse_args()


def load_suite(suite_path: str) -> Dict[str, Any]:

    if not os.path.exists(suite_path):
        raise FileNotFoundError(f"Suite file not found: {suite_path}")
    with open(suite_path, "r", encoding="utf-8") as f:
        data: Union[Dict[str, Any], List[Dict[str, Any]]] = json.load(f)

    if isinstance(data, list):
        return {"flows": data}
    if isinstance(data, dict):
        flows = data.get("flows")
        if isinstance(flows, list):
            return data
        raise ValueError("Suite JSON object must contain a 'flows' array")
    raise ValueError("Suite JSON must be an array of flows or an object with a 'flows' array")
    

def run_flow_steps(flow: Dict[str, Any], cli_overrides: argparse.Namespace) -> int:

	variables: Dict[str, Any] = flow.get("variables", {}) or {}
	default_timeout: int = (
		cli_overrides.timeout if getattr(cli_overrides, "timeout", None) is not None else int(flow.get("timeout", 20))
	)
	headless: bool = bool(getattr(cli_overrides, "headless", False) or flow.get("headless", False))
	chromedriver_path: Optional[str] = (
		getattr(cli_overrides, "chromedriver_path", None) if getattr(cli_overrides, "chromedriver_path", None) else flow.get("chromedriver_path")
	)

	driver = None
	try:
		driver = _create_webdriver(headless=headless, chromedriver_path=chromedriver_path)

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
				page_text = _get_body_text(driver)
				if needle not in page_text:
					print(f"Assertion failed: page does not contain '{needle}'", file=sys.stderr)
					return 1

			elif action == "assert_page_not_contains": # 需要参数 text or value
				needle = text or value
				if not needle:
					raise ValueError("assert_page_not_contains requires 'text' or 'value'")
				page_text = _get_body_text(driver)
				if needle in page_text:
					print(f"Assertion failed: page unexpectedly contains '{needle}'", file=sys.stderr)
					return 1

			elif action == "assert_element_contains": # 需要参数 selector 以及 text or value
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

			elif action == "assert_element_not_contains": # 需要参数 selector 以及 text or value
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
				page_text = _get_body_text(driver)
				if _contains_error_keyword(page_text):
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
				name = step.get("name")
				if not name:
					raise ValueError("set_var requires 'name'")
				variables[name] = text or value or ""

			elif action == "ocr_captcha":
				# 使用 pytesseract 识别验证码并存储到变量
				if not selector:
					raise ValueError("ocr_captcha requires 'selector' (captcha image)")
				name = step.get("name")
				if not name:
					raise ValueError("ocr_captcha requires 'name' to store result variable")
				preprocessing = step.get("preprocessing", "default")
				captcha_text = ocr_captcha(driver, selector, preprocessing)
				variables[name] = captcha_text
				print(f"验证码识别结果存储到变量 {name}: {captcha_text}")

			elif action == "solve_captcha":
				# 自动解决验证码（识别+输入+验证）
				captcha_selector = step.get("captcha_selector")
				input_selector = step.get("input_selector")
				submit_selector = step.get("submit_selector")
				max_attempts = int(step.get("max_attempts", 3))
				preprocessing = step.get("preprocessing", "default")
				
				if not captcha_selector:
					raise ValueError("solve_captcha requires 'captcha_selector'")
				if not input_selector:
					raise ValueError("solve_captcha requires 'input_selector'")
				
				# 传递selenium_check模块的函数引用
				selenium_check_funcs = (_get_body_text, _type, _click)
				success = solve_simple_captcha(
					driver, captcha_selector, input_selector, submit_selector, 
					max_attempts, preprocessing, selenium_check_funcs
				)
				if not success:
					print("验证码解决失败，请手动输入", file=sys.stderr)
					
					

			elif action == "wait_user":
				# 等待用户手动操作（如复杂验证码）
				msg = text or value or "请在浏览器内完成验证码后按回车继续..."
				try:
					input(msg)
				except EOFError:
					# 在CI环境中回退为固定等待
					time.sleep(float(step.get("seconds", 30)))

			elif action == "prompt":
				# 提示用户输入并存储到变量
				name = step.get("name")
				if not name:
					raise ValueError("prompt requires 'name' to store user input variable")
				prompt_msg = text or value or f"请输入 {name} 的值: "
				try:
					variables[name] = input(prompt_msg)
				except EOFError:
					variables[name] = ""



			elif action == "switch_to_default_content":
				# 切换回主文档
				driver.switch_to.default_content()

			elif action == "save_cookies":
				# 保存登录后的cookies
				if not path:
					raise ValueError("save_cookies requires 'path'")
				os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
				with open(path, "w", encoding="utf-8") as f:
					json.dump(driver.get_cookies(), f, ensure_ascii=False, indent=2)

			elif action == "load_cookies":
				# 加载之前保存的cookies
				if not path:
					raise ValueError("load_cookies requires 'path'")
				if not os.path.exists(path):
					raise FileNotFoundError(f"Cookies文件未找到: {path}")
				with open(path, "r", encoding="utf-8") as f:
					cookies = json.load(f)
				for ck in cookies:
					try:
						# 确保cookie字段有效
						ck.pop('sameSite', None)  # 某些驱动对大小写敏感
						driver.add_cookie(ck)
					except Exception:
						pass

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


def run_suite(suite: Dict[str, Any], cli: argparse.Namespace) -> List[Dict[str, Any]]:

    defaults: Dict[str, Any] = {
        "headless": bool(cli.headless or suite.get("headless", False)),
        "timeout": int(suite.get("timeout", cli.default_timeout)),
        "chromedriver_path": suite.get("chromedriver_path", cli.chromedriver_path),
    }

    results: List[Dict[str, Any]] = []
    for index, flow in enumerate(suite["flows"]):
        name: str = flow.get("name") or f"flow_{index+1}"

        # Merge default knobs via CLI overrides interface expected by run_flow_steps
        overrides = argparse.Namespace(
            headless=bool(flow.get("headless", defaults["headless"])),
            timeout=int(flow.get("timeout", defaults["timeout"])),
            chromedriver_path=flow.get("chromedriver_path", defaults["chromedriver_path"]),
        )

        exit_code = run_flow_steps(flow, overrides)

        results.append(
            {
                "name": name,
                "exit_code": exit_code,
                "status": STATUS_BY_CODE.get(exit_code, "UNKNOWN"),
                "timeout": overrides.timeout,
                "headless": overrides.headless,
            }
        )

        if cli.stop_on_fail and exit_code != 0:
            break

    return results


def write_report(path: str, results: List[Dict[str, Any]]) -> None:
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(results),
        "summary": {
            "pass": sum(1 for r in results if r["exit_code"] == 0),
            "error_found": sum(1 for r in results if r["exit_code"] == 1),
            "failures": sum(1 for r in results if r["exit_code"] not in (0, 1)),
        },
        "results": results,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> None:

    args = parse_args()
    suite = load_suite(args.suite)
    results = run_suite(suite, args)
    write_report(args.output, results)
    if any(r["exit_code"] != 0 for r in results):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
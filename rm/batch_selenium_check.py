import argparse
import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

from selenium_check import run_flow


STATUS_BY_CODE: Dict[int, str] = {
    0: "PASS_NO_ERROR_FOUND",
    1: "ERROR_KEYWORD_FOUND",
    2: "SELENIUM_TIMEOUT_OR_NO_SUCH_ELEMENT",
    3: "WEBDRIVER_ERROR",
    4: "UNEXPECTED_ERROR",
}


def load_config(config_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Config must be a JSON array of test case objects")
    return data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run Selenium checks against multiple webpages using a JSON config, "
            "reusing run_flow from selenium_check.py"
        )
    )

    parser.add_argument(
        "--config",
        required=True,
        help=(
            "Path to JSON file containing an array of cases. "
            "Each case must include url, username, password, username_selector, password_selector, submit_selector. "
            "Optional: feature_selector, after_login_wait_selector, post_click_wait_selector, timeout, headless, chromedriver_path, name"
        ),
    )

    parser.add_argument(
        "--output",
        default="selenium_results.json",
        help="Where to write the JSON summary report (default: selenium_results.json)",
    )

    parser.add_argument(
        "--default-timeout",
        type=int,
        default=20,
        help="Default per-step timeout seconds when a case doesn't specify it",
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Default headless mode when a case doesn't specify it",
    )

    parser.add_argument(
        "--chromedriver-path",
        default=os.environ.get("CHROMEDRIVER"),
        help=(
            "Default local chromedriver path when a case doesn't specify it (useful offline). "
            "If omitted, Selenium Manager will be used."
        ),
    )

    parser.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Stop executing further cases when a non-zero exit code is returned",
    )

    return parser.parse_args()


def run_cases(
    cases: List[Dict[str, Any]],
    default_timeout: int,
    default_headless: bool,
    default_chromedriver_path: Optional[str],
    stop_on_fail: bool,
) -> List[Dict[str, Any]]:

    results: List[Dict[str, Any]] = []
    for index, case in enumerate(cases):
        name: str = case.get("name") or f"case_{index+1}"

        url: str = case["url"]
        username: str = case["username"]
        password: str = case["password"]
        username_selector: str = case["username_selector"]
        password_selector: str = case["password_selector"]
        submit_selector: str = case["submit_selector"]

        feature_selector: Optional[str] = case.get("feature_selector")
        after_login_wait_selector: Optional[str] = case.get("after_login_wait_selector")
        post_click_wait_selector: Optional[str] = case.get("post_click_wait_selector")
        timeout: int = int(case.get("timeout", default_timeout))
        headless: bool = bool(case.get("headless", default_headless))
        chromedriver_path: Optional[str] = case.get("chromedriver_path", default_chromedriver_path)

        exit_code = run_flow(
            url=url,
            username=username,
            password=password,
            username_selector=username_selector,
            password_selector=password_selector,
            submit_selector=submit_selector,
            feature_selector=feature_selector or "",
            after_login_wait_selector=after_login_wait_selector,
            post_click_wait_selector=post_click_wait_selector,
            timeout=timeout,
            headless=headless,
            chromedriver_path=chromedriver_path,
        )

        case_result: Dict[str, Any] = {
            "name": name,
            "url": url,
            "exit_code": exit_code,
            "status": STATUS_BY_CODE.get(exit_code, "UNKNOWN"),
            "timeout": timeout,
            "headless": headless,
        }
        results.append(case_result)

        if stop_on_fail and exit_code != 0:
            break

    return results


def write_report(output_path: str, results: List[Dict[str, Any]]) -> None:
    report: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total": len(results),
        "summary": {
            "pass": sum(1 for r in results if r["exit_code"] == 0),
            "error_found": sum(1 for r in results if r["exit_code"] == 1),
            "failures": sum(1 for r in results if r["exit_code"] not in (0, 1)),
        },
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    cases = load_config(args.config)
    results = run_cases(
        cases=cases,
        default_timeout=args.default_timeout,
        default_headless=args.headless,
        default_chromedriver_path=args.chromedriver_path,
        stop_on_fail=args.stop_on_fail,
    )
    write_report(args.output, results)
    # Exit non-zero if any case found ERROR or failed
    if any(r["exit_code"] != 0 for r in results):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()



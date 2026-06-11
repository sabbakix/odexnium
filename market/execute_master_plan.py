#!/usr/bin/env python3
"""
Executor for the master plan defined in `prompts`.

This script orchestrates the full Selenium scraping pipeline using
`CoinMarketCapSeleniumScraper`:

- Ensures dependencies from `requirements.txt`
- Initializes Selenium (headless optional)
- Fetches top non-stablecoin coins (up to 100)
- Visits each coin page, configures chart (MAX/ALL + log scale), extracts SVG
- Generates an HTML table and saves JSON + raw SVG backups

Run:
  python execute_master_plan.py --headless --max-coins 25 --rate-limit-ms 1500 --timeout 30 --output-dir output
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional


REQUIREMENTS_FILE = "requirements.txt"


# Ensure prints don't crash on Windows consoles lacking UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _print_header(title: str) -> None:
    line = "=" * max(40, len(title) + 10)
    print(f"\n{line}\n{title}\n{line}")


def ensure_dependencies(requirements_path: str = REQUIREMENTS_FILE) -> None:
    """Install dependencies if imports fail, using requirements.txt.

    This is idempotent: if all imports succeed, it doesn't run pip.
    """
    _print_header("Phase 1: Setup & Dependencies")
    missing: List[str] = []

    def _try_import(module: str) -> None:
        try:
            __import__(module)
        except Exception:
            missing.append(module)

    # Core runtime imports we rely on
    _try_import("selenium")
    _try_import("webdriver_manager")
    _try_import("requests")
    _try_import("bs4")

    if not missing:
        print("✅ All dependencies already installed")
        return

    print(f"⚠️ Missing packages detected: {', '.join(missing)}")
    if not os.path.exists(requirements_path):
        raise FileNotFoundError(f"requirements file not found at {requirements_path}")

    # Install via pip
    print("📦 Installing dependencies from requirements.txt ...")
    cmd = [sys.executable, "-m", "pip", "install", "-r", requirements_path]
    try:
        subprocess.check_call(cmd)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Failed to install dependencies: {exc}") from exc


@contextlib.contextmanager
def temporarily_change_dir(target_dir: str):
    """Temporarily change current working directory to `target_dir`."""
    previous = os.getcwd()
    os.makedirs(target_dir, exist_ok=True)
    os.chdir(target_dir)
    try:
        yield
    finally:
        os.chdir(previous)


def execute_plan(headless: bool, timeout: int, max_coins: Optional[int], rate_limit_ms: int, output_dir: Optional[str]) -> None:
    """Execute phases 2-7 of the master plan using the scraper class."""
    # Import here so dependency installation can happen first
    from selenium_coinmarketcap_scraper import CoinMarketCapSeleniumScraper

    _print_header("Phase 2: Core Scraping Logic")
    scraper = CoinMarketCapSeleniumScraper(headless=headless, timeout=timeout)

    def _run_inside(dir_path: Optional[str]):
        # Fetch
        coins = scraper.get_top_100_coins()
        if not coins:
            print("❌ No coins found; aborting execution.")
            return

        # Filter/limit
        if isinstance(max_coins, int) and max_coins > 0:
            coins = coins[:max_coins]
        print(f"✅ Prepared {len(coins)} coins for processing")

        # Phase 3 + 4: individual processing + svg extraction
        _print_header("Phase 3 & 4: Coin Processing + SVG Extraction")
        processed: List[Dict] = []
        for index, coin in enumerate(coins, start=1):
            print(f"[{index}/{len(coins)}] {coin.get('name', 'Unknown')} ({coin.get('slug', '')})")
            svg = scraper.get_coin_chart_svg(coin)
            coin["svg_chart"] = svg
            processed.append(coin)
            # Rate limiting
            if rate_limit_ms > 0:
                time.sleep(rate_limit_ms / 1000.0)

        # Phase 5: HTML table
        _print_header("Phase 5: HTML Table Generation")
        html = scraper.create_html_table(processed)

        # Phase 6: Error Handling & Optimization — already applied via waits/try-catches
        # Minimal data validation
        svg_success = sum(1 for c in processed if c.get("svg_chart"))
        if svg_success == 0:
            print("⚠️ No SVGs extracted; output will still be saved for debugging.")

        # Phase 7: Output & Storage
        _print_header("Phase 7: Output & Storage")
        scraper.save_data(processed, html)

    try:
        if output_dir:
            with temporarily_change_dir(output_dir):
                _run_inside(output_dir)
        else:
            _run_inside(None)
        print("\n✅ Master plan executed successfully.")
    finally:
        # Ensure webdriver closes even if errors occur
        with contextlib.suppress(Exception):
            if getattr(scraper, "driver", None):
                scraper.driver.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description="Execute the master plan from `prompts` using Selenium scraper.")
    parser.add_argument("--headless", action="store_true", help="Run Chrome in headless mode")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout for webdriver waits (seconds)")
    parser.add_argument("--max-coins", type=int, default=None, help="Limit number of coins to process (<=100)")
    parser.add_argument("--rate-limit-ms", type=int, default=1500, help="Delay between coins in milliseconds")
    parser.add_argument("--output-dir", type=str, default=None, help="Directory to store outputs (created if missing)")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation checks")

    args = parser.parse_args()

    if not args.skip_deps:
        ensure_dependencies(REQUIREMENTS_FILE)

    start = time.time()
    try:
        execute_plan(
            headless=args.headless,
            timeout=args.timeout,
            max_coins=args.max_coins,
            rate_limit_ms=args.rate_limit_ms,
            output_dir=args.output_dir,
        )
    finally:
        elapsed = time.time() - start
        print(f"\n⏱️ Total elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    main()



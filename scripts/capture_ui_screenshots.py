from pathlib import Path
import subprocess
import time

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "images" / "ui"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    proc = subprocess.Popen(["python", "-m", "flashback_ops"], cwd=str(ROOT))
    try:
        time.sleep(3)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 920})
            page.goto("http://127.0.0.1:8000", wait_until="networkidle")
            page.click("#seedBtn")
            page.wait_for_timeout(1000)
            page.screenshot(path=str(OUT_DIR / "01-dashboard.png"), full_page=True)

            page.click("#applyScenarioBtn")
            page.click("button:has-text('Run Memory-Assisted Plan')")
            page.wait_for_timeout(1200)
            page.screenshot(path=str(OUT_DIR / "02-plan-view.png"), full_page=True)

            page.fill("input[name='email']", "oncall@company.com")
            page.fill("input[name='team_name']", "Platform Reliability")
            page.fill("textarea[name='use_case']", "Incident response at scale")
            page.screenshot(path=str(OUT_DIR / "03-subscription.png"), full_page=True)

            mobile = browser.new_page(viewport={"width": 430, "height": 932})
            mobile.goto("http://127.0.0.1:8000", wait_until="networkidle")
            mobile.click("#seedBtn")
            mobile.wait_for_timeout(900)
            mobile.screenshot(path=str(OUT_DIR / "04-mobile.png"), full_page=True)

            mobile.close()
            browser.close()
    finally:
        proc.terminate()
        proc.wait(timeout=10)


if __name__ == "__main__":
    main()

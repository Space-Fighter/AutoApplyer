import asyncio
import os
from pathlib import Path


from dotenv import load_dotenv
from playwright.async_api import async_playwright, Page



JOBS_URL = "https://www.workatastartup.com/jobs"
STATE_FILE = Path(__file__).with_name("yc_state.json")
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"



load_dotenv(dotenv_path=ENV_FILE)


BOT_EMAIL = os.getenv("YC_BOT_EMAIL")
BOT_PASSWORD = os.getenv("YC_BOT_PASSWORD")

async def is_logged_in(page: Page) -> bool:
    current_url = page.url.lower()
    login_button = page.locator("a.inline-flex:text('Log In')")
    if ("account.ycombinator.com" in current_url or "login" in current_url or await login_button.is_visible()):
        return False
    return True

async def login_and_save_state(page: Page) -> None:
    await page.get_by_text("Log In", exact=True).click()
    await page.locator('input[name="username"]').fill(BOT_EMAIL)
    await page.locator('input[name="password"]').fill(BOT_PASSWORD)
    await page.locator('input[name="password"]').press("Enter")
    await page.context.storage_state(path=str(STATE_FILE))
    
async def open_yc() -> None:
    if not STATE_FILE.exists():
        raise FileNotFoundError(f"No saved session found at {STATE_FILE}. Run the login flow first.")
    
    logged_in = True
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        try:
            context = await browser.new_context(storage_state=str(STATE_FILE))
            page = await context.new_page()
            print("Opening YC jobs page with saved session...")
            await page.goto(JOBS_URL)
            await page.wait_for_timeout(3000)
            logged_in = await is_logged_in(page)
        except:
            print("Failed to load saved state.")
            context = await browser.new_context()
            page = await context.new_page()
            print("Opening YC jobs page without saved session...")
            await page.goto(JOBS_URL)
            await page.wait_for_timeout(3000)
            logged_in = False

        if not logged_in:
            print("NOT LOGGED IN -  Logging in and updating state file...")
            await login_and_save_state(page)

        try:
            await asyncio.sleep(float("inf"))
        except (KeyboardInterrupt, Exception):
            print("Closing browser...")
            await context.close()
            await browser.close()

async def main() -> None:
    opened = await open_yc()

if __name__ == "__main__":
    asyncio.run(main())
import asyncio
import os
from pathlib import Path


from dotenv import load_dotenv
from playwright.async_api import async_playwright



JOBS_URL = "https://www.workatastartup.com/jobs"
STATE_FILE = Path(__file__).with_name("yc_state.json")
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


load_dotenv(dotenv_path=ENV_FILE)


BOT_EMAIL = os.getenv("YC_BOT_EMAIL")
BOT_PASSWORD = os.getenv("YC_BOT_PASSWORD")



async def login_and_save_state() -> None:
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()


        print("Opening YC jobs page for manual login...")
        if BOT_EMAIL:
            print(f"Bot email found in environment: {BOT_EMAIL}")
        else:
            print("No YC_BOT_EMAIL found in environment yet.")
        if not BOT_PASSWORD:
            print("No YC_BOT_PASSWORD found in environment yet.")
        await page.goto(JOBS_URL)
        print("Log in in the browser window, then come back here.")
        input("Press Enter after the YC jobs page shows you as signed in: ")


        await context.storage_state(path=str(STATE_FILE))
        print(f"Saved login state to {STATE_FILE}")


        await context.close()
        await browser.close()



async def open_with_saved_session() -> None:
    if not STATE_FILE.exists():
        raise FileNotFoundError(
            f"No saved session found at {STATE_FILE}. Run the login flow first."
        )


    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=False)
        context = await browser.new_context(storage_state=str(STATE_FILE))
        page = await context.new_page()


        print("Opening YC jobs page with saved session...")
        await page.goto(JOBS_URL)
        await page.wait_for_timeout(3000)


        print(f"Page title: {await page.title()}")
        print("Browser is open. Use this to confirm the saved session still works.")


        try:
            await asyncio.sleep(float("inf"))
        except (KeyboardInterrupt, Exception):
            print("Closing browser...")
        finally:
            await context.close()
            await browser.close()



async def main() -> None:
    action = input("Type 'login' to save YC session, or press Enter to reuse it: ")
    if action.strip().lower() == "login":
        await login_and_save_state()
    else:
        await open_with_saved_session()



if __name__ == "__main__":
    asyncio.run(main())
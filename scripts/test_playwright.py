from playwright.async_api import async_playwright
from playwright.async_api import Page, Browser, BrowserContext
import asyncio

"""
1. A browser is a single instance of a web browser. Playwright will automatically launch a browser instance 
specified by code or by inputs. Typically, this is either the Chromium, Firefox, or WebKit instance installed via 
playwright install, but it may also be other browsers installed on your local machine.
2. A browser context is an isolated incognito-alike session within a browser instance. They are fast and cheap to 
create. One browser may have multiple browser contexts. The recommended practice is for all tests to share one 
browser instance but for each test to have its own browser context.h
3. A page is a single tab or window within a browser context. A browser context may have multiple pages. Typically, 
an individual test should interact with only one page.
"""
async def test_basic_duckduckgo_search(page: Page) -> None:
    print("Navigating to DuckDuckGo...")
    await page.goto('https://www.duckduckgo.com')
    await page.wait_for_timeout(2000)  # Wait for page to fully load
    
    print("Typing 'panda' in search box...")
    await page.locator(".ai-searchbox_combobox__o04a2").type("panda", delay=0)  # Remove character delay for speed
    await page.wait_for_timeout(200)  # Minimal wait
    
    print("Pressing Enter...")
    await page.keyboard.press("Enter")
    
    await page.wait_for_timeout(2000)  # Wait for results to load

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("Browser launched!")
        await test_basic_duckduckgo_search(page)
        
        print("Browser is open. Close the window manually to exit, or press Ctrl+C...")
        try:
            await asyncio.sleep(float('inf'))
        except (KeyboardInterrupt, Exception):
            print("Closing browser...")
            await context.close()
            await browser.close()
        
asyncio.run(main())
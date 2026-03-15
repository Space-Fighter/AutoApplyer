from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://example.com")

    print(page.title())
    time.sleep(10)
    browser.close()
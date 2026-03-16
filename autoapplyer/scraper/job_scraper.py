from playwright.sync_api import sync_playwright


def scrape_jobs():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        page.goto("https://example.com")

        print("Page loaded:", page.title())

        browser.close()
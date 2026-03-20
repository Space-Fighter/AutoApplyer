**YC Scraper Plan**
- Step 1 — Contract + naming: in yc_scraper.py, define one public async function (`scrape_yc_jobs`) and standard output fields (`title`, `company`, `location`, `job_url`, `description`, `skill_tags`, `date_scraped`); this also fixes the current mismatch with test_yc_scraper.py.
- Step 2 — Browser/session setup: create a clean Playwright lifecycle (launch, context, page, close) with configurable headless mode and timeouts.
- Step 3 — Listing-page extraction: scrape YC job cards from `https://www.workatastartup.com/jobs`, collect unique job links plus lightweight metadata from the list page.
- Step 4 — Detail-page extraction: visit each job link (bounded concurrency with semaphore), extract rich fields (full description, tags, workplace/location, apply URL if present).
- Step 5 — Data normalization: clean whitespace/HTML, normalize missing values to `None`, dedupe by `job_url`, stamp UTC scrape time.
- Step 6 — Database persistence: map scraped data into Company + Job records using models.py and engine/session from db.py, with “insert-or-update by job_url”.
- Step 7 — Script wiring: keep a simple runner flow so test_yc_scraper.py can call scraper and print a sample job JSON.
- Step 8 — Reliability layer: add retry/backoff for page navigation and selector fallback paths so small YC DOM changes don’t break the run.
- Step 9 — Validation checklist: run scraper, confirm non-empty result, confirm DB rows are created, rerun to verify dedupe/upsert behavior.

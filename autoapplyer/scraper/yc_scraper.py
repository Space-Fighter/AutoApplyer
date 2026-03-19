import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
"""
- The site is a React SPA — all the job data is embedded as JSON inside a data-page attribute on a <div>. 
- This means you don't need Playwright to scrape individual job pages at all. 
  The data is right there in the HTML, structured and clean.
- Look at what's already in that JSON for each job:
id
title
description
job_type
eng_type
remote,
locations
salary_min
salary_max
equity_min
equity_max,
skills (with names)
company (name, website, batch, description)
- show_path → "https://www.workatastartup.com/jobs/13302"
This is far better than CSS selectors. You just parse the JSON.

- The Strategy
Instead of Playwright crawling each job page one by one, you:
Hit https://www.workatastartup.com/jobs with Playwright (one page load)
Read the data-page attribute from the div
Parse the JSON — you get all jobs + company data in one shot
Save to DB
"""

JOBS_URL = "https://www.workatastartup.com/jobs"


async def fetch_raw_page_data() -> dict:
    """
    YC's site is a React SPA. All job data is embedded as JSON
    in the data-page attribute of the root div. We just parse that.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("Loading YC jobs page...")
        await page.goto(JOBS_URL, timeout=60000)
        await page.wait_for_timeout(3000)  # let React render

        # The entire page state is in this one div's data-page attribute
        data_page_json = await page.get_attribute(
            "[data-page]", "data-page"
        )
        await browser.close()

        if not data_page_json:
            raise ValueError("Could not find data-page attribute on page")

        return json.loads(data_page_json)


def parse_jobs(raw_data: dict) -> list[dict]:
    """
    Extract jobs from the parsed JSON.
    Returns a clean list of job dicts ready to save.
    """
    jobs_out = []

    # Jobs are nested under props -> rawCompany -> jobs
    # OR props -> companies (on the /jobs listing page)
    props = raw_data.get("props", {})

    # On the /jobs page, companies is a list of companies each with jobs
    companies = props.get("companies", [])

    for company_data in companies:
        company_info = {
            "name": company_data.get("name"),
            "website": company_data.get("website"),
            "batch": company_data.get("batch"),
        }

        for job in company_data.get("jobs", []):
            # Parse location
            locations = job.get("locations") or []
            location_str = locations[0] if locations else None
            city, country = None, None
            if location_str:
                parts = location_str.split(",")
                city = parts[0].strip() if parts else None
                country = parts[-1].strip() if len(parts) > 1 else None

            # Parse skills into comma-separated string
            skills = job.get("skills", [])
            skill_tags = ", ".join(s["name"] for s in skills) if skills else None

            # Map remote field
            remote_raw = job.get("remote")  # "yes", "no", "only"
            workplace_map = {"yes": "hybrid", "no": "onsite", "only": "remote"}
            workplace = workplace_map.get(remote_raw, None)

            jobs_out.append({
                "title": job.get("title"),
                "job_url": job.get("show_path"),  # full URL
                "description": job.get("description"),
                "job_type": job.get("job_type"),        # "fulltime", "parttime", "intern"
                "role": job.get("pretty_eng_type"),     # "Backend", "Full stack", etc
                "city": city,
                "country": country,
                "workplace": workplace,
                "skill_tags": skill_tags,
                "source": "yc",
                "date_scraped": datetime.utcnow(),
                "company_name": company_info["name"],
                "company_website": company_info["website"],
                "company_batch": company_info["batch"],
            })

    print(f"Parsed {len(jobs_out)} jobs from {len(companies)} companies")
    return jobs_out


async def scrape_yc_jobs() -> list[dict]:
    raw_data = await fetch_raw_page_data()
    return parse_jobs(raw_data)
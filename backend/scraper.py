from linkedin_scraper import BrowserManager, login_with_credentials, is_logged_in, CompanyScraper, JobSearchScraper
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

from urllib.parse import urlencode
from typing import Optional


STATE_FILE = Path(__file__).with_name("session.json")
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
JOBS_URL = "https://www.linkedin.com/jobs/search"
load_dotenv(dotenv_path=ENV_FILE)

BOT_EMAIL = os.getenv("BOT_EMAIL")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")

class LinkedInScraper:
    def __init__(self, email: str = BOT_EMAIL, password: str = BOT_PASSWORD):
        self.email = email
        self.password = password
        self.browser = None
        self.browser_manager = None
        self.job_search_scraper = None

    async def login(self, page: Page) -> None:
        await login_with_credentials(
            page,
            email=self.email,
            password=self.password,

        )
        await page.context.storage_state(path=str(STATE_FILE))

    async def _build_search_url(
            self,
            keywords: Optional[str] = None,
            location: Optional[str] = None,
            distance: Optional[int] = None,
            geo_id: Optional[int] = None,
            time_filter: Optional[str] = None,
            f_wt: Optional[str] = None,
            f_EL: Optional[str] = None,
            f_JT: Optional[str] = None,
            sort_by: Optional[str] = "R",
            current_job_id: Optional[int] = None
        ) -> str:
        """
        Build LinkedIn job search URL with parameters.

        Args:
            keywords:       Job title or keywords (e.g. "senior operations manager")
            location:       Human-readable location label (e.g. "United States", "Florida")
            distance:       Search radius in miles
            geo_id:         LinkedIn geoId for the target location (default: 103644278 = United States)
            time_filter:    Recency filter. Common values:
                                "r3600"   – Last hour
                                "r86400"  – Last 24 hours  (default when provided)
                                "r604800" – Last week
                                "r2592000"– Last month
                            Pass None to omit the filter entirely.
            f_wt:          Job type filter. Common values:
                                ONSITE = "1"
                                REMOTE = "2"
                                HYBRID = "3"
            sort_by:        "R" = Relevance (default), "DD" = Date posted
            current_job_id: Optional job ID to pre-select in the viewer.

            f_JT: JOB TYPE -> Value=Meaning => F=Full-time|P=Part-time|C=Contract|T=Temporary|I=Internship|V=Volunteer|O=Other
            f_EL: EXPERIENCE LEVEL ->Value=Meaning => 1=Internship|2=Entry level (SWE1)|3=Associate|4=Mid-Senior|5=Director|6=Executive
        Returns:
            Fully encoded LinkedIn job search URL string.

        Examples:
            # Senior Operations Manager, US, last 24 hrs
            url = obj._build_search_url(
                keywords="senior operations manager",
                time_filter="r86400"
            )

            # Director of Sales Operations, Florida, last week, sorted by date
            url = obj._build_search_url(
                keywords="director sales operations",
                location="Florida",
                geo_id=101318387,   # Florida geoId
                distance=50,
                time_filter="r604800",
                sort_by="DD"
            )
        """
        base_url = "https://www.linkedin.com/jobs/search/"

        params = {}
        def _normalize(value: Optional[Union[str, list[str]]]) -> Optional[str]:
        if value is None:
            return None
        return ",".join(value) if isinstance(value, list) else value

        # Pre-selected job in the viewer (cosmetic; does not affect results)
        if current_job_id is not None:
            params["currentJobId"] = current_job_id

        # Search radius
        if distance is not None:
            params["distance"] = distance

        # Recency filter
        if time_filter is not None:
            params["f_TPR"] = time_filter

        if f_wt is not None:
            params["f_wt"] = _normalize(f_wt)

        if f_EL is not None:
            params["f_EL"] = _normalize(f_EL)

        if f_JT is not None:
            params["f_JT"] = _normalize(f_JT)

        # Geographic ID
        if geo_id is not None:
            params["geoId"] = geo_id

        # Keywords / job title
        if keywords:
            params["keywords"] = keywords

        # Human-readable location label
        if location:
            params["location"] = location

        # Always tag the origin so LinkedIn's analytics stay consistent
        params["origin"] = "JOB_SEARCH_PAGE_JOB_FILTER"

        # Sort order
        if sort_by is not None:
            params["sortBy"] = sort_by

        if params:
            return f"{base_url}?{urlencode(params)}"

        return base_url

    async def search_jobs(self) -> None:
        print(f"Searching for jobs...")
        jobs = await self.job_search_scraper.search(
            keywords="Python Developer",
            location="San Francisco",
            limit=10
        )
        print(f"Found {len(jobs)} jobs:")
        for job in jobs:
            print("JOB: ", job)

    async def start(self) -> None:
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=False)
            context = None
            try:
                try:
                    context = await self.browser.new_context(storage_state=str(STATE_FILE))
                except Exception:
                    context = await self.browser.new_context()
                page = await context.new_page()
                print("Opening LinkedIn jobs page with saved session...")
                await page.goto(JOBS_URL)
                await page.wait_for_timeout(3000)
                logged_in = await is_logged_in(page)

                if not logged_in:
                    print("NOT LOGGED IN - Logging in and updating state file...")
                    await self.login(page)
                    print("Login successful.")
                    await page.goto(JOBS_URL)

                # self.browser_manager = BrowserManager(_browser=self.browser, _context=context, _page=page, _is_authenticated=True)
                self.job_search_scraper = JobSearchScraper(page)
                await self.search_jobs()
                
                print("SLEEPING INDEFINITELY - Press Ctrl+C to exit.")
                await asyncio.sleep(float("inf"))

            except (KeyboardInterrupt, asyncio.CancelledError, PlaywrightError):
                print("Closing browser...")
                await self.close(context)
    
    async def close(self, context) -> None:
        try:
            if context:
                await context.close()
            await self.browser.close()
        except Exception:
            pass

async def main() -> None:
    await LinkedInScraper().start()    

asyncio.run(main())
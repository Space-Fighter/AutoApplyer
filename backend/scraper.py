from linkedin_scraper import BrowserManager, login_with_credentials, is_logged_in, CompanyScraper, JobSearchScraper
from playwright.async_api import async_playwright, Page, Error as PlaywrightError
from openai import OpenAI
from pydantic import BaseModel, field_validator, model_validator
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

from urllib.parse import urlencode
import json

from typing import Optional, Union
from enum import Enum



STATE_FILE = Path(__file__).with_name("session.json")
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
JOBS_URL = "https://www.linkedin.com/jobs/search"
load_dotenv(dotenv_path=ENV_FILE)

BOT_EMAIL = os.getenv("BOT_EMAIL")
BOT_PASSWORD = os.getenv("BOT_PASSWORD")


# ── Enums ─────────────────────────────────────────────────────────────────────

class WorkType(str, Enum):
    onsite = "1"
    remote = "2"
    hybrid = "3"

class ExperienceLevel(str, Enum):
    internship  = "1"
    entry       = "2"
    associate   = "3"
    mid_senior  = "4"
    director    = "5"
    executive   = "6"

class JobType(str, Enum):
    full_time   = "F"
    part_time   = "P"
    contract    = "C"
    temporary   = "T"
    volunteer   = "V"
    internship  = "I"
    other       = "O"

class SortBy(str, Enum):
    relevant = "R"
    recent   = "DD"

class TimeFilter(str, Enum):
    last_24h    = "r86400"
    last_week   = "r604800"
    last_month  = "r2592000"


# ── Search params model ───────────────────────────────────────────────────────

class JobSearchParams(BaseModel):
    keywords:       Optional[str]                       = None
    location:       Optional[list[str]]                       = None
    distance:       Optional[int]                       = None
    geo_id:         Optional[int]                       = None
    time_filter:    Optional[TimeFilter]                = None
    f_wt:           Optional[list[WorkType]]            = None
    f_EL:           Optional[list[ExperienceLevel]]     = None
    f_JT:           Optional[list[JobType]]             = None
    sort_by:        Optional[SortBy]                    = SortBy.relevant
    current_job_id: Optional[int]                       = None

    @field_validator("distance")
    @classmethod
    def distance_must_be_positive(cls, v):
        if v is not None and v < 0:
            raise ValueError("distance must be a positive integer")
        return v

    @model_validator(mode="after")
    def location_required_with_distance(self):
        if self.distance is not None and not self.location:
            raise ValueError("location is required when distance is specified")
        return self

    def to_url(self) -> str:
        def _normalize(values):
            if values is None:
                return None
            return ",".join(v.value for v in values)

        
        urls = []
        for location in locations:
            params = {}
            if self.current_job_id is not None:  params["currentJobId"]  = self.current_job_id
            if self.distance is not None:        params["distance"]      = self.distance
            if self.time_filter is not None:     params["f_TPR"]         = self.time_filter.value
            if self.f_wt is not None:            params["f_WT"]          = _normalize(self.f_wt)
            if self.f_EL is not None:            params["f_EL"]          = _normalize(self.f_EL)
            if self.f_JT is not None:            params["f_JT"]          = _normalize(self.f_JT)
            if self.geo_id is not None:          params["geoId"]         = self.geo_id
            if self.keywords:                    params["keywords"]      = self.keywords
            if self.location:                    params["location"]      = self.location
            params["origin"] = "JOB_SEARCH_PAGE_JOB_FILTER"
            if self.sort_by is not None:         params["sortBy"]        = self.sort_by.value

        urls.append(f"{JOBS_URL}?{urlencode(params, safe=',')}")

class ScraperBot:
    
class LinkedInScraper:
    def __init__(self, email: Optional[str] = BOT_EMAIL, password: Optional[str] = BOT_PASSWORD):
        self.email = email or ""
        self.password = password or ""
        self.browser = None
        self.browser_manager = None
        self.job_search_scraper = None
        self.client = OpenAI()
        def load_system_prompt() -> str:
            prompt_path = Path("prompts/job_search_system.md")
            return prompt_path.read_text(encoding="utf-8").strip()
        self.SYSTEM_PROMPT = load_system_prompt()

    async def login(self, page: Page) -> None:
        await login_with_credentials(
            page,
            email=self.email,
            password=self.password,

        )
        await page.context.storage_state(path=str(STATE_FILE))

    async def get_search_url(self, USER_PROMPT: str):
        messages = ["role: system", f"content: {self.SYSTEM_PROMPT}", 
                    "role: user", f"content: {USER_PROMPT}"]
        response = self.client.responses.parse(
            model="gpt-4.1-mini",
            input=messages,
            response_format=JobSearchParams,)
        params = response.output_parsed
        url = params.to_url()
        return url

    async def search_jobs(self) -> None:
        print(f"Searching for jobs...")
        if self.job_search_scraper is None:
            raise RuntimeError("Job search scraper is not initialized.")
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
            if self.browser:
                await self.browser.close()
        except Exception:
            pass

async def main() -> None:
    await LinkedInScraper().start()    

asyncio.run(main())
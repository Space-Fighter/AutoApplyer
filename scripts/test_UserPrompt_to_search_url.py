import os
import json
from pathlib import Path
from urllib.parse import urlencode
from typing import Optional
from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator, model_validator
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

STATE_FILE = Path(__file__).with_name("session.json")
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
JOBS_URL = "https://www.linkedin.com/jobs/search"
load_dotenv(dotenv_path=ENV_FILE)
JOBS_URL = "https://www.linkedin.com/jobs/search"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

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
    role_keywords:  Optional[list[str]]                 = None
    locations:      Optional[list[str]]                 = None
    distance:       Optional[int]                       = None
    geo_id:         Optional[int]                       = None
    time_filter:    Optional[TimeFilter]                = None
    f_wt:           Optional[list[WorkType]]            = None
    f_EL:           Optional[list[ExperienceLevel]]     = None
    f_JT:           Optional[list[JobType]]             = None
    easy_apply:     Optional[bool]                      = None
    sort_by:        Optional[SortBy]                    = SortBy.relevant
    current_job_id: Optional[int]                       = None

    @field_validator("distance")
    @classmethod
    def distance_must_be_positive(cls, value):
        if value is not None and value < 0:
            raise ValueError("distance must be a positive integer")
        return value
    

    @model_validator(mode="after")
    def location_required_with_distance(self):
        if self.distance is not None and not self.locations:
            raise ValueError("locations are required when distance is specified")
        return self

def build_urls(params: JobSearchParams) -> list[str]:
    def _normalize(values):
        if values is None:
            return None
        return ",".join(v.value for v in values)

    def _role_keywords() -> list[str]:
        if params.role_keywords:
            roles = [r.strip() for r in params.role_keywords if r and r.strip()]
            return roles or [""]
        if params.keywords and "," in params.keywords:
            roles = [k.strip() for k in params.keywords.split(",") if k.strip()]
            return roles or [params.keywords]
        return [params.keywords] if params.keywords else [""]
    
    def make_url(location, role_keyword):
        params_dict = {}
        if params.current_job_id is not None:  params_dict["currentJobId"]  = params.current_job_id
        if params.distance is not None:        params_dict["distance"]      = params.distance
        if params.time_filter is not None:     params_dict["f_TPR"]         = params.time_filter.value
        if params.f_wt is not None:            params_dict["f_WT"]          = _normalize(params.f_wt)
        if params.f_EL is not None:            params_dict["f_EL"]          = _normalize(params.f_EL)
        if params.f_JT is not None:            params_dict["f_JT"]          = _normalize(params.f_JT)
        if params.easy_apply is not None:      params_dict["f_AL"]          = str(params.easy_apply).lower()
        if params.geo_id is not None:          params_dict["geoId"]         = params.geo_id
        if role_keyword:                       params_dict["keywords"]      = role_keyword
        if location:                           params_dict["location"]      = location
        params_dict["origin"] = "JOB_SEARCH_PAGE_JOB_FILTER"
        if params.sort_by is not None:         params_dict["sortBy"]        = params.sort_by.value
        return f"{JOBS_URL}?{urlencode(params_dict, safe=',')}"

    locations = params.locations if params.locations else [None]
    roles = _role_keywords()
    urls: list[str] = []
    seen: set[str] = set()
    for location in locations:
        for role in roles:
            url = make_url(location, role)
            if url in seen:
                continue
            seen.add(url)
            urls.append(url)
    return urls


# ── Agent ─────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a LinkedIn job search assistant.
When a user describes the job they're looking for, extract search parameters for JobSearchParams.
For mixed role intent, populate role_keywords with distinct role phrases (for example: backend engineer, ai ml engineer, computer vision engineer).
Use short clean keyword phrases without punctuation clutter.
Infer sensible defaults:
- 'recent' -> time_filter=last_week
- 'remote' -> f_wt=[remote]
- 'onsite' -> f_wt=[onsite]
- 'hybrid' -> f_wt=[hybrid]
- 'new grad' or 'internship' -> f_EL include internship or entry and f_JT include internship if appropriate
- 'easy apply' -> easy_apply=true
If only one role is present, role_keywords can be omitted and keywords can be used."""



def get_search_url(USER_PROMPT: str):
    messages: list[ChatCompletionMessageParam] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ]
    response = client.chat.completions.parse(
        model="gpt-4.1-mini",
        messages=messages,
        response_format=JobSearchParams,
    )
    params = response.choices[0].message.parsed
    if params is None:
        raise ValueError("No parsed search params returned by model")
    urls = build_urls(params)
    return urls


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    prompts = ["Looking for remote backend, ai-ml, computer vision jobs in USA-REMOTE, EUROPE-REMOTE, OCEANIA-REMOTE, SINGAPORE-REMOTE, DUBAI-REMOTE, ASIA-REMOTE, INDIA-REMOTE/Onsite internships"]

    for prompt in prompts:
        print(f"\nPrompt: {prompt}")
        urls = get_search_url(prompt)
        for url in urls:
            print(f"Generated URL: {url}")
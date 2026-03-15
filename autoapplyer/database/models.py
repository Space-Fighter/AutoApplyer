from sqlmodel import Field, SQLModel
from typing import Optional


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    company: str
    title: str # raw title from job posting
    role: Optional[str] # backend, ai engineer, ml engineer etc
    job_type: Optional[str] # intern, swe1, fulltime etc
    
    # LOCATION FIELDS
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    # onsite/ remote / hybrid
    workplace: list[str]
    # main job url link(highest priority)
    job_url: str
    skill_tags: list[str]
    description: Optional[str] = None
    summary: Optional[str] = None


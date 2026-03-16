from sqlmodel import Field, SQLModel, Relationship
from typing import Optional, List
from datetime import datetime
from enum import Enum

class Company(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    website: Optional[str] = None
    career_page: Optional[str] = None

    # Relationship of Company with jobs
    jobs: List["Job"] = Relationship(back_populates="company")

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationship of job with company
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    company: Optional["Company"] = Relationship(back_populates="jobs")
    
    title: str # raw title from job posting
    role: Optional[str] # backend, ai engineer, ml engineer etc
    job_type: Optional[str] # intern, swe1, fulltime etc
    
    # LOCATION FIELDS
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

    # onsite/ remote / hybrid
    workplace: Optional[str] = None
    # main job url link(highest priority)
    job_url: str
    skill_tags: Optional[str] = None
    description: Optional[str] = None
    summary: Optional[str] = None
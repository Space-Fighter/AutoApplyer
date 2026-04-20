# AutoApplyer 🚀  
**Prompt-to-Job Search URL Generator with Future Auto-Apply Pipeline**

AutoApplyer is an automation tool designed to simplify job discovery workflows.  
Instead of manually applying multiple filters across job portals, this tool converts a natural language prompt into structured job search URLs, enabling efficient multi-location and multi-role job discovery.

---

# Current Features ✅

## 1. Prompt → Job Search URL Generator

Users can describe their job preferences in natural language, and the system generates relevant **LinkedIn job search URLs**.

<img width="1599" height="899" alt="image" src="https://github.com/user-attachments/assets/3754ee36-df2a-485f-b6a5-b07a61133306" />

This solves a major limitation:

> LinkedIn does not allow searching multiple locations and roles simultaneously without repeatedly changing filters.

---

## Problem This Solves 🎯

Traditional job searching is repetitive and inefficient:

- Users must apply filters repeatedly
- Multiple locations require separate searches
- Multiple roles require separate searches
- Remote + city combinations increase complexity
- Switching filters wastes time

This tool automates that process.

With one prompt:

- Multiple locations handled
- Multiple roles handled
- Remote preferences handled
- URLs generated automatically

---

# Work In Progress 🚧

The next stage of development focuses on **job data extraction and storage**.

## 2. Job Scraping Pipeline (Under Development)

Generated job search URLs will be:

- Opened using browser automation
- Job listings extracted
- Stored in a structured database

Planned components:

- Playwright-based scraper
- Structured job metadata extraction
- Database storage system

Expected stored fields:

- Job Title  
- Company Name  
- Location  
- Job Link  
- Job Description (optional)

---

# Planned Features 🔮

These features are part of the long-term roadmap.

---

## 3. AI-Based Auto Apply Agent

Goal:

Allow users to automatically apply to relevant jobs using stored data.

Planned workflow:

1. Match user profile to job description
2. Select appropriate resume
3. Generate personalized message
4. Submit application

---

## 4. Resume & Message Tracking System

A productivity-focused feature.

Users will be able to:

- Store multiple resumes
- Track messages sent to recruiters
- Avoid rewriting repetitive outreach messages
- Reuse customized templates

---

# Tech Stack 🧠

- Playwright for scraping
- Pydandtic for data ingestion
- SQLModel for database management

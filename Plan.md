## Goal

Build an **Auto-Applyer system** that:

* Scrapes jobs from portals
* Stores them in a structured database
* Automatically applies
* Generates cover letters using stored responses + resume
* Finds employees on LinkedIn/email and sends outreach
* Allows manual customization when needed

The plan below is designed for a **Python programmer with no web-dev experience**, and progresses in **small chunks** so you avoid reading a huge AI-generated codebase.

---

# Phase 0 — Tools Setup (1–2 days)

### Core stack (simple + beginner friendly)

| Component       | Tool                   | Why                        |
| --------------- | ---------------------- | -------------------------- |
| Language        | Python                 | You already know it        |
| Package manager | **uv**                 | fast dependency management |
| Scraping        | **Playwright**         | handles modern JS sites    |
| API server      | **FastAPI**            | simple backend             |
| Database        | **PostgreSQL**         | best structured DB         |
| ORM             | **SQLModel**           | Pythonic DB interaction    |
| LLM tasks       | OpenAI / Ollama        | cover letters etc          |
| Scheduler       | **APScheduler / cron** | daily scraping             |
| Automation      | Playwright             | job application forms      |
| Vector memory   | **ChromaDB**           | store responses/resume     |

Why **PostgreSQL**?

Because your data is **structured**:

```
Job
Company
Application
Contact person
Messages sent
```

A relational database is perfect.

---

# Phase 1 — Project Skeleton (Day 1) ✅

Folder structure:

```
autoapplyer/

backend/
    main.py
    config.py

database/
    models.py
    db.py

scraper/
    job_scraper.py

agents/
    apply_agent.py
    resume_agent.py
    message_agent.py

automation/
    form_filler.py
    linkedin_bot.py

storage/
    resume/
    responses/

scripts/
    run_scraper.py
```

Initialize project:

```bash
uv init autoapplyer
cd autoapplyer

uv add fastapi sqlalchemy sqlmodel
uv add playwright
uv add psycopg2-binary
uv add chromadb
```

Install browsers:

```
playwright install
```

---

# Phase 2 — Database Design (Important)

### Tables

#### Jobs

```
id
title
company
location
job_url
company_url
description
summary
tags
date_scraped
```

---

#### Companies

```
id
name
website
linkedin
industry
size
```

---

#### Applications

```
id
job_id
status
applied_on
portal
resume_used
cover_letter
```

status:

```
saved
applied
interview
rejected
```

---

#### Contacts

```
id
name
company
linkedin
email
role
priority
```

---

#### Messages

```
id
contact_id
message_type
message
sent_at
```

---

#### Personal Responses

For reusable answers:

```
id
question_type
content
tags
```

Examples:

```
"why_company"
"why_role"
"about_me"
"salary_expectation"
```

These feed the **cover letter generator**.

---

# Phase 3 — Job Scraper (First real feature)

Start with **one site only**.

Good beginner options:

```
Wellfound (AngelList)
YC Jobs
Greenhouse boards
Lever boards
```

These are easiest to scrape.

Example flow:

```
scraper/
    wellfound_scraper.py
```

Steps:

1. open job list
2. extract job links
3. visit each job
4. extract:

```
title
company
description
location
apply_link
```

5. store in database

Run daily.

---

# Phase 4 — Job Summary Generator

Each scraped job should be summarized.

Use LLM:

```
Job description → summary
```

Example summary:

```
Backend Python role
Startup company
Focus: ML infrastructure
Tech: Python, FastAPI, AWS
```

Also extract tags:

```
["python","backend","ai","startup"]
```

This helps filtering.

---

# Phase 5 — Resume + Memory System

Store:

```
resume
past answers
personal achievements
projects
```

Use **vector database**.

Example entries:

```
"My interest in AI started with building a self-driving car in CARLA..."

"I enjoy solving algorithmic problems and have experience with Kaggle competitions."
```

When generating a **cover letter**, retrieve relevant info.

---

# Phase 6 — Apply Automation

Automation uses **Playwright**.

Agent workflow:

```
open job page
click apply
upload resume
fill name/email
generate cover letter
submit
```

For each portal you will need **custom handlers**:

```
greenhouse_apply.py
lever_apply.py
workday_apply.py
```

Because forms differ.

---

# Phase 7 — Company Website Applications

After applying on portal:

```
check if company has careers page
```

If yes:

```
scrape careers
look for same job
apply there too
```

---

# Phase 8 — LinkedIn Outreach

Goal:

```
find employees relevant to job
send connection message
```

Priority order:

```
1 hiring manager
2 recruiter
3 team lead
4 engineers in team
```

Message template:

```
Hi [Name],

I recently applied to the [Role] position at [Company].
I would love to learn more about the team and would greatly appreciate any advice or referral.

Thanks!
Tejas
```

---

# Phase 9 — Email Scraping

Find emails via:

```
company website
hunter.io style patterns
github commits
```

Example patterns:

```
firstname@company.com
first.last@company.com
```

Then send email outreach.

Use:

```
SMTP / Gmail API
```

---

# Phase 10 — Personalization System

You should have a **manual override interface**.

When system encounters:

```
"Why do you want to work here?"
```

Options:

```
1 Auto generate
2 Choose saved answer
3 Let user edit
```

Store edited answers for future reuse.

---

# Phase 11 — Simple Dashboard (Optional)

Later you can add a UI.

Example stack:

```
React + FastAPI
```

Dashboard shows:

```
jobs scraped
jobs applied
responses
contacts messaged
```

---

# Phase 12 — Scheduler

Daily workflow:

```
1 scrape jobs
2 summarize
3 filter relevant
4 auto apply
5 send linkedin outreach
6 send email outreach
```

---

# Simple System Architecture

```
           Scraper
              |
              v
          Job Database
              |
              v
       Apply Agent
        /       \
       v         v
 LinkedIn      Emails
 Outreach      Outreach
```

---

# Important Beginner Advice

Do **NOT** build everything at once.

Build **this order only**:

```
1 scrape jobs
2 store jobs
3 summarize jobs
4 manual apply helper
5 auto apply
6 linkedin outreach
7 email outreach
```

Each step should work **independently**.

---

# First 5 Tasks You Should Do

1️⃣ Install tools

```
python
uv
playwright
postgres
```

---

2️⃣ Build database models

```
jobs
companies
applications
```

---

3️⃣ Scrape **Wellfound jobs**

Store them.

---

4️⃣ Add **LLM job summarizer**

---

5️⃣ Make a **CLI**

```
python run_scraper.py
python run_apply.py
```

---

# Important Legal Note

Automation for:

```
LinkedIn
Workday
Greenhouse
```

can violate ToS if abused.

Keep rate low.

---

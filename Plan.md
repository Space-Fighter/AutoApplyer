---
name: job-application-agentic-system
overview: Design and implement a modular, production-grade agentic workflow system that automates and assists with job applications while preserving human-in-the-loop control.
todos:
  - id: design-core-schema
    content: Finalize and implement PostgreSQL schema for jobs, applications, knowledge base, QA responses, templates, generated contents, and pending actions.
    status: completed
  - id: implement-backend-skeleton
    content: Set up FastAPI app, configuration, database connection, and Alembic migrations.
    status: completed
  - id: build-llm-and-vector-abstractions
    content: Implement provider-agnostic LLM client and vector store integration for profile and QA retrieval.
    status: completed
  - id: implement-job-pipelines
    content: Develop job discovery, parsing, and analysis agents with background task orchestration.
    status: completed
  - id: implement-tailoring-and-application-flows
    content: Build resume tailoring, application assistant, and pending-action approval flows with Playwright worker.
    status: completed
  - id: implement-outreach-and-tracking
    content: Add outreach message generation, careers page handling, and application tracking agents with APIs.
    status: completed
  - id: add-logging-monitoring
    content: Integrate structured logging, metrics, and error handling across agents and workers.
    status: completed
isProject: false
---

## High-level architecture

- **Core pattern**: Event-driven, agentic workflow system with a FastAPI backend, PostgreSQL relational database, a vector store, a task queue, and a browser automation worker (Playwright) orchestrated by an agent framework (LangGraph or equivalent).
- **Separation of concerns**:
  - **API layer**: HTTP+WebSocket APIs, authentication, user settings, human-approval endpoints.
  - **Orchestration layer**: Agent workflows (graphs) for discovery, analysis, tailoring, and application assistance.
  - **Execution layer**: Background workers for scraping, browser automation, and LLM calls.
  - **Persistence layer**: PostgreSQL for structured data (jobs, applications, messages, templates, responses) and a vector DB for semantic retrieval over resumes, projects, job descriptions, and past answers.
  - **Front-end**: Web UI (or CLI initially) for reviewing jobs, editing content, and approving submissions.
- **Human-in-the-loop control**: All actions that send or submit data outwards (job applications, LinkedIn messages, emails) are represented as **pending actions** that require explicit approval via the API/UI before execution.

```mermaid
flowchart TD
  user[User] --> ui[Web UI / CLI]
  ui --> api[FastAPI Backend]
  api -->|HTTP/WebSocket| orchestrator[Agent Orchestration (LangGraph)]
  orchestrator -->|tasks| queue[Task Queue]
  queue --> workers[Background Workers]
  workers --> playwright[Browser Automation (Playwright)]
  orchestrator --> llm[LLM Provider]
  orchestrator --> vecdb[Vector DB]
  orchestrator --> pg[PostgreSQL]
  workers --> pg
  workers --> logs[Logging & Metrics]
  api --> pg
```



## Database schema (PostgreSQL)

- **jobs**
  - `id` (UUID, PK)
  - `source` (enum: 'linkedin', 'indeed', 'company_careers', 'manual', ...)
  - `external_job_id` (string, nullable)
  - `title` (text)
  - `company` (text)
  - `location` (text)
  - `employment_type` (text, nullable)
  - `job_url` (text)
  - `company_website` (text, nullable)
  - `raw_description` (text)
  - `clean_description` (text)
  - `summary` (text)
  - `tags` (string[]; skills, role, seniority, domain)
  - `salary_min` (numeric, nullable)
  - `salary_max` (numeric, nullable)
  - `currency` (text, nullable)
  - `seniority_level` (text, nullable)
  - `role_family` (text, nullable)
  - `status` (enum: 'new', 'shortlisted', 'applied', 'rejected', 'interviewing', 'offer', 'archived')
  - `created_at`, `updated_at`
- **applications**
  - `id` (UUID, PK)
  - `job_id` (FK jobs.id)
  - `channel` (enum: 'linkedin', 'indeed', 'company_careers', 'email', 'referral', ...)
  - `status` (enum: 'draft', 'pending_approval', 'submitted', 'failed', 'withdrawn')
  - `applied_at` (timestamp, nullable)
  - `resume_version_id` (FK resumes.id, nullable)
  - `cover_letter_id` (FK generated_contents.id, nullable)
  - `notes` (text)
    - `portal_username` (text, nullable)
  - `portal_application_id` (text, nullable)
  - `last_error` (text, nullable)
  - `created_at`, `updated_at`
- **resumes**
  - `id` (UUID, PK)
  - `name` (text)  // e.g. "General SWE", "ML-focused"
  - `file_path` (text)  // path to PDF/Doc in storage
  - `raw_text` (text)
  - `embedding_id` (FK embeddings.id, nullable)
  - `is_primary` (boolean)
  - `created_at`, `updated_at`
- **profile_knowledge_items** (resume & profile KB)
  - `id` (UUID, PK)
  - `type` (enum: 'resume_section', 'project', 'experience', 'bio', 'achievement')
  - `title` (text)
  - `content` (text)
  - `tags` (string[]; e.g. ['backend', 'TypeScript', 'leadership'])
  - `embedding_id` (FK embeddings.id, nullable)
  - `created_at`, `updated_at`
- **qa_responses** (response memory system)
  - `id` (UUID, PK)
  - `question_canonical` (text)
  - `question_variants` (string[])
  - `answer_markdown` (text)
  - `tags` (string[]; e.g. ['motivation', 'why_company', 'leadership'])
  - `embedding_id` (FK embeddings.id, nullable)
  - `created_at`, `updated_at`
- **message_templates** (message personalization system)
  - `id` (UUID, PK)
  - `template_type` (enum: 'recruiter_outreach', 'referral_request', 'hiring_manager_intro', 'follow_up', ...)
  - `name` (text)
  - `body_markdown` (text)  // with placeholders like {{company}}, {{role_title}}, {{person_name}}
  - `description` (text, nullable)
  - `is_active` (boolean)
  - `created_at`, `updated_at`
- **generated_contents** (cover letters, tailored bullets, messages)
  - `id` (UUID, PK)
  - `content_type` (enum: 'cover_letter', 'resume_bullets', 'application_answer', 'outreach_message')
  - `job_id` (FK jobs.id, nullable)
  - `application_id` (FK applications.id, nullable)
  - `template_id` (FK message_templates.id, nullable)
  - `source_agent` (text)
  - `content_markdown` (text)
  - `metadata` (JSONB)
  - `created_at`, `updated_at`
- **pending_actions** (for human approval)
  - `id` (UUID, PK)
  - `action_type` (enum: 'submit_application', 'send_linkedin_message', 'send_email')
  - `application_id` (FK applications.id, nullable)
  - `job_id` (FK jobs.id, nullable)
  - `payload` (JSONB)  // structured description of what will be done
  - `status` (enum: 'pending', 'approved', 'rejected', 'executed', 'failed')
  - `created_at`, `updated_at`, `executed_at` (nullable)
- **embeddings** (shared table for vector DB sync, if needed)
  - `id` (UUID, PK)
  - `source_table` (text)
  - `source_id` (UUID)
  - `embedding` (vector or external_id pointing into vector store)
  - `created_at`
- **event_log** (for auditing & monitoring)
  - `id` (UUID, PK)
  - `event_type` (text)
  - `payload` (JSONB)
  - `created_at`

## Agent responsibilities

- **JobDiscoveryAgent**
  - Periodically search job boards and company career pages via APIs/scraping.
  - Apply role/keyword filters.
  - Emit raw job listing artifacts into a processing queue.
- **JobParsingAgent**
  - Normalize raw HTML/JSON into structured job records.
  - Extract title, company, description, location, salary data, and links.
  - Store to `jobs` and enqueue for analysis.
- **JobAnalysisAgent**
  - Summarize job descriptions.
  - Extract and tag skills, role family, seniority, company type.
  - Generate embeddings for the job description and store/search in vector DB.
  - Decide whether a job fits preconfigured preferences (e.g. must-have techs).
- **ResumeKnowledgeAgent**
  - Ingest resume(s), projects, experiences, and Q&A content into `resumes`, `profile_knowledge_items`, and `qa_responses`.
  - Maintain embeddings and sync with vector DB.
- **ResponseMemoryAgent**
  - Given a new application question, retrieve top-k similar `qa_responses`.
  - Suggest reusing or adapting past answers.
  - Optionally update memory with user-edited final answers.
- **ResumeTailoringAgent**
  - For a given job, analyze requirements vs. profile KB.
  - Select relevant experiences and generate tailored bullet points.
  - Produce a tailored resume variant (structured bullets + suggestions) and a draft cover letter stored in `generated_contents`.
- **ApplicationAssistantAgent**
  - For a selected job, create an `applications` record.
  - Plan required fields for the chosen portal (based on prior templates/heuristics).
  - Generate draft answers using the ResponseMemoryAgent + job analysis + templates.
  - Create a `pending_actions` entry to perform browser automation for final submission.
- **BrowserAutomationWorker (Playwright worker)**
  - Consume approved `pending_actions` of type `submit_application`.
  - Open browser, navigate to the job portal, fill forms, upload resume, paste answers.
  - Capture screenshots, detect errors, update `applications.status` and `last_error`.
- **CompanyCareersAgent**
  - Given a job/company, discover the official career site.
  - Search for equivalent/related roles there.
  - If found, create additional `applications` and `pending_actions` for those paths.
- **OutreachAgent**
  - Given a job, look up likely contacts (title-based heuristics + user-provided lists/LinkedIn searches via manual input or browser assist).
  - Propose outreach messages using `message_templates` + profile KB.
  - Store generated drafts in `generated_contents` and create `pending_actions` of type `send_linkedin_message` or `send_email`, leaving execution to human.
- **ApplicationTrackerAgent**
  - Periodically revisit portals/email (where possible) or let user manually update statuses.
  - Provide summaries of application pipeline and reminders for follow-up.
- **Supervisor/OrchestratorAgent**
  - Define multi-step workflows (graphs): discovery -> parsing -> analysis -> shortlist -> tailoring -> application.
  - Monitor failures and retries, write to `event_log`.

## Recommended tech stack

- **Language**: Python
  - Rich ecosystem for web scraping, Playwright, LLM integration, FastAPI, LangGraph.
- **Backend framework**: FastAPI
  - Async-friendly, great for APIs and background task triggers.
  - Automatic OpenAPI docs, easy integration with Pydantic models.
- **Agent framework**: LangGraph (on top of LangChain) or similar graph-based orchestration
  - Natural fit for defining multi-step agent workflows with state and human-in-the-loop nodes.
  - Supports tool-calling patterns and error handling.
- **Database**: PostgreSQL
  - Strong relational capabilities, JSONB for flexible metadata, good for pipelines, mature ecosystem.
- **Vector store**: PostgreSQL pgvector extension or an external service like Qdrant/Weaviate
  - For an MVP: pgvector inside PostgreSQL to keep ops simple while supporting semantic retrieval.
- **Browser automation**: Playwright (Python bindings)
  - Reliable, headless/full-browser automation with good testability.
- **Task queue**: Celery or RQ with Redis, or FastAPI+Arq
  - Decouples long-running tasks (scraping, browser automation, heavy LLM calls) from the API.
  - For simplicity, Redis+RQ or Celery with Redis broker.
- **LLM provider**: Pluggable abstraction
  - Start with a hosted provider (e.g. OpenAI/Anthropic via an adapter) but design an interface to swap for local models later.
- **Logging & monitoring**:
  - Structured logging via `structlog` or standard logging with JSON formatter.
  - Metrics via Prometheus-compatible exporter.
  - Optional: Sentry for error tracking.

## API architecture (FastAPI)

- **Auth & settings** (even for single user, keep it modular)
  - `GET /api/me/profile` – view profile and preferences.
  - `PUT /api/me/profile` – update preferences (target roles, locations, salary range, etc.).
- **Jobs**
  - `GET /api/jobs` – list/filter jobs (status, tags, source).
  - `GET /api/jobs/{job_id}` – job details with analysis and related applications.
  - `POST /api/jobs/import` – manual import of a job URL or pasted description.
- **Applications**
  - `POST /api/jobs/{job_id}/applications` – create a new application draft and trigger tailoring.
  - `GET /api/applications` – list applications.
  - `GET /api/applications/{app_id}` – detail, including generated resume bullets, cover letter, answers.
  - `PATCH /api/applications/{app_id}` – update notes/status.
- **Content generation & memory**
  - `GET /api/jobs/{job_id}/tailor` – get tailored resume bullets and cover letter draft.
  - `POST /api/applications/{app_id}/answers/generate` – generate draft answers for portal questions.
  - `POST /api/qa_responses` – add/update reusable Q&A entries.
  - `GET /api/qa_responses/search` – retrieve suggested answers for a question.
- **Outreach & templates**
  - `GET /api/message_templates` / `POST /api/message_templates` – CRUD templates.
  - `POST /api/jobs/{job_id}/outreach/generate` – generate suggested outreach messages.
- **Pending actions (human approval)**
  - `GET /api/pending_actions` – list actions requiring approval.
  - `POST /api/pending_actions/{action_id}/approve` – approve and enqueue execution.
  - `POST /api/pending_actions/{action_id}/reject` – reject/delete.
- **Admin & diagnostics**
  - `GET /api/health` – health check.
  - `GET /api/events` – recent system events (for debugging).

## Data pipelines & workflow orchestration

- **Job discovery pipeline**
  1. Scheduler (cron/worker) enqueues a `discover_jobs` task.
  2. `JobDiscoveryAgent` fetches listings from sources and emits raw artifacts.
  3. For each artifact, enqueue `parse_job`.
  4. `JobParsingAgent` normalizes and saves to `jobs`, then enqueues `analyze_job`.
  5. `JobAnalysisAgent` enriches the job (summary, tags, embeddings) and updates `jobs`.
- **Job selection & tailoring pipeline**
  1. User selects a job via UI or API.
  2. API creates an `applications` record (status `draft`).
  3. Orchestrator triggers `ResumeTailoringAgent` for this job.
  4. Tailored bullets & cover letter are saved in `generated_contents`.
  5. UI shows drafts; user can edit/resave.
- **Portal application pipeline (approval-gated)**
  1. User clicks "Prepare application".
  2. `ApplicationAssistantAgent` determines necessary fields/questions (from configured templates + heuristics).
  3. `ResponseMemoryAgent` and LLM generate draft answers and attach to `generated_contents`.
  4. System creates a `pending_actions` record of type `submit_application` with a full plan (target URL, job id, portal type, answers, resume path).
  5. UI displays this action; user reviews content and clicks Approve.
  6. On approval, a worker consumes the action and runs Playwright to execute it.
  7. Upon success/failure, the worker updates `applications.status` and logs an event.
- **Company careers pipeline**
  1. Given a job and company domain, `CompanyCareersAgent` looks for `/careers`, `/jobs`, or configured endpoints.
  2. Scrapes relevant openings and matches them semantically to the original role.
  3. If a match is found, creates additional `jobs`/`applications` and follows the same tailoring & pending-action path.
- **Outreach pipeline**
  1. User requests outreach suggestions for a job.
  2. `OutreachAgent` retrieves job + profile KB + templates.
  3. Generates N candidate messages (connection, follow-up, referral) saved in `generated_contents`.
  4. Optionally creates `pending_actions` (e.g. `send_linkedin_message`) that the user can use as copy-paste helpers rather than auto-send.

## Error handling strategy

- **Layered retries**
  - Transient errors in scraping, LLM calls, and browser automation retried with exponential backoff via the task queue.
  - Max retry count per task, with failure recorded in `event_log` and `applications.last_error`.
- **Validation & safety**
  - Strict Pydantic models for API requests and internal task payloads.
  - Explicit schema for `pending_actions.payload` to prevent malformed actions.
  - Security guardrails: never execute an outward action unless `pending_actions.status = 'approved'`.
- **Graceful degradation**
  - If LLM is unavailable, allow manual text entry/editing and save to DB.
  - If scraping fails for a source, mark that source as temporarily unavailable but keep other pipelines running.

## Logging & monitoring

- **Structured logs**
  - Every agent and worker logs events with correlation IDs (job_id, app_id, action_id) to ease tracing.
- **Metrics**
  - Counters: jobs discovered, jobs parsed, applications created, applications submitted, failures per source.
  - Histograms: LLM latency, scraping task duration, browser automation duration.
- **Alerting**
  - On repeated failures for the same source or portal, raise alerts (e.g. email/Sentry) so scrapers can be updated.

## Folder/project structure (monorepo, backend-focused for now)

- `backend/`
  - `app/`
    - `main.py` (FastAPI entrypoint)
    - `config.py` (settings, env config)
    - `api/`
      - `routes_jobs.py`
      - `routes_applications.py`
      - `routes_templates.py`
      - `routes_pending_actions.py`
      - `routes_profile.py`
    - `models/` (SQLAlchemy models/Pydantic schemas)
      - `job.py`
      - `application.py`
      - `resume.py`
      - `profile_knowledge.py`
      - `qa_response.py`
      - `template.py`
      - `generated_content.py`
      - `pending_action.py`
      - `embedding.py`
      - `event_log.py`
    - `db/`
      - `base.py` (session, engine)
      - `migrations/` (Alembic)
    - `agents/`
      - `orchestrator.py` (LangGraph definitions)
      - `job_discovery.py`
      - `job_parsing.py`
      - `job_analysis.py`
      - `resume_knowledge.py`
      - `response_memory.py`
      - `resume_tailoring.py`
      - `application_assistant.py`
      - `company_careers.py`
      - `outreach.py`
      - `application_tracker.py`
    - `workers/`
      - `queue.py` (task queue setup)
      - `tasks_jobs.py`
      - `tasks_applications.py`
      - `tasks_outreach.py`
      - `playwright_worker.py`
    - `services/`
      - `llm_client.py` (provider abstraction)
      - `embedding_service.py`
      - `scraping_service.py`
      - `career_page_discovery.py`
      - `vector_store.py`
      - `resume_parser.py`
      - `email_service.py`
    - `schemas/` (Pydantic)
      - `job_schemas.py`
      - `application_schemas.py`
      - `template_schemas.py`
      - `pending_action_schemas.py`
      - `qa_schemas.py`
    - `logging_config.py`
    - `security/` (auth, secrets management; even for single user keep modular)
  - `tests/`
    - `test_api_jobs.py`
    - `test_agents_tailoring.py`
    - `test_workers_playwright.py`
- `frontend/` (optional for later; could be React/Next.js or simple SPA)
  - For now, backend-first; UI can be CLI or minimal web interface.

## Step-by-step implementation plan

1. **Project bootstrap**
  - Initialize Python project with `pyproject.toml`, set up FastAPI, SQLAlchemy, Alembic, and basic configuration.
  - Configure PostgreSQL (with pgvector if chosen), Redis (for queue), and environment-based settings.
2. **Core data models & migrations**
  - Implement SQLAlchemy models for `jobs`, `applications`, `resumes`, `profile_knowledge_items`, `qa_responses`, `message_templates`, `generated_contents`, `pending_actions`, and `event_log`.
  - Set up Alembic migrations and create initial schema.
3. **LLM & vector store abstraction**
  - Implement `llm_client` with a provider-agnostic interface.
  - Implement `embedding_service` and `vector_store` wrapper (pgvector/Qdrant) and integrate with KB tables.
4. **Profile knowledge & response memory ingestion**
  - Build APIs and services to upload/import resume(s) and structured profile data.
  - Build CRUD endpoints for `qa_responses` and `message_templates`.
  - Implement embedding and retrieval for profile KB and QA.
5. **Job discovery & parsing pipeline**
  - Implement minimal `JobDiscoveryAgent` and `JobParsingAgent` for 1–2 sources (e.g. manual URL import + one job board).
  - Implement background tasks for discovery and parsing, wired into the queue.
  - Implement `JobAnalysisAgent` for summarization, tagging, and embeddings.
6. **Job browsing & filtering API**
  - Implement `/api/jobs` and `/api/jobs/{id}` endpoints (with filters and pagination).
  - Add basic UI or CLI to view and shortlist jobs.
7. **Resume tailoring & cover letter generation**
  - Implement `ResumeTailoringAgent` using profile KB + job description.
  - Implement endpoints to trigger tailoring for a job and return drafts (stored in `generated_contents`).
8. **Application assistant & pending actions**
  - Implement `ApplicationAssistantAgent` to create `applications` and generate draft answers using `ResponseMemoryAgent`.
  - Implement `pending_actions` creation, listing, approval, rejection.
  - Enforce human approval guardrails at all execution boundaries.
9. **Browser automation (Playwright worker)**
  - Set up Playwright worker process using the task queue.
  - Implement a minimal automation flow for one portal (e.g. a demo site or a simpler board) consuming `pending_actions`.
  - Add logging, screenshots, and robust error handling.
10. **Company careers and outreach workflows**
  - Implement `CompanyCareersAgent` to find and parse a few common career site patterns.
    - Implement `OutreachAgent` to generate outreach messages from templates and KB, saving drafts in `generated_contents`.
11. **Application tracking & summaries**
  - Implement `ApplicationTrackerAgent` for basic status updates and pipeline summaries.
    - Add APIs and minimal UI to see funnel stats and recommended follow-ups.
12. **Hardening, logging, and monitoring**
  - Add structured logging across agents and workers.
    - Add metrics and simple dashboards.
    - Improve error handling, retries, and idempotency for key tasks.
13. **Optional: frontend enhancements**
  - Build a simple web dashboard for reviewing jobs, editing drafts, and approving actions.
    - Polish UX around manual edits and approvals before any external submission.


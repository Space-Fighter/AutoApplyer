# LinkedIn Job Ingestion Plan (Compliance-First)

## Goal

Build a reliable LinkedIn job ingestion workflow for `AutoApplyer` that prioritizes account safety, legal compliance, and maintainability, while still using AI agents for enrichment and matching.

This plan avoids bot-evasion and fragile scraping tactics. The main strategy is:

1. Ingest jobs from compliant/low-friction sources first.
2. Treat LinkedIn as an optional source with strict limits.
3. Use AI agents for processing, not anti-bot bypass.

## Scope

1. In scope: job discovery pipeline, normalization, dedupe, AI ranking, persistence, and observability.
2. In scope: connector architecture that can include LinkedIn metadata where legally and technically allowed.
3. Out of scope: bypassing login protections, CAPTCHA solving, stealth fingerprinting, and any ToS-violating automation.

## Phase Plan

### Phase 1 - Contract and Data Model

1. Define a common `JobIngestRecord` contract used by all sources:
   - `source`
   - `external_id`
   - `job_url`
   - `title`
   - `company`
   - `location`
   - `employment_type`
   - `description`
   - `apply_url`
   - `posted_at`
   - `scraped_at`
   - `raw_payload`
2. Update DB models (if needed) so each job row stores source + source identifier for upsert safety.
3. Add unique constraint recommendation: `(source, external_id)` and fallback uniqueness on `job_url`.

### Phase 2 - Connector Layer

1. Create connector interface in `autoapplyer/scraper/`:
   - `fetch_listings(query_config) -> list[JobIngestRecord]`
2. Implement priority connectors first:
   - `greenhouse_connector.py`
   - `lever_connector.py`
   - `ashby_connector.py`
3. Add `linkedin_connector.py` as optional and guarded:
   - Explicit feature flag.
   - Strict rate limits.
   - Graceful failure path that does not break full pipeline.

### Phase 3 - Ingestion Orchestrator

1. Create orchestrator service that:
   - Runs enabled connectors.
   - Normalizes records to shared schema.
   - Deduplicates by source id and URL.
   - Upserts into database.
2. Add run metadata:
   - total fetched
   - total inserted
   - total updated
   - total failed
   - failure reasons by connector

### Phase 4 - AI Agent Workflow

1. Add `job_enrichment_agent`:
   - Summarizes descriptions.
   - Extracts skills and seniority.
   - Produces normalized tags.
2. Add `fit_scoring_agent`:
   - Scores role fit against resume/profile.
   - Outputs explainable reasons for score.
3. Add `dedupe_resolution_agent`:
   - Resolves near-duplicate jobs from multiple sources.
4. Keep all agent outputs cached to avoid re-processing unchanged jobs.

### Phase 5 - Compliance and Safety Controls

1. Implement per-source `robots/ToS` policy notes in code comments/docs.
2. Add configurable rate limiting (requests/minute) and jittered delays.
3. Add retry budget with exponential backoff, then fail closed.
4. Add kill switch:
   - Disable any source at runtime via env var.
5. Log minimal required data and avoid collecting user-private data not needed for job matching.

### Phase 6 - Testing and Verification

1. Unit tests:
   - Schema validation
   - Deduping/upsert logic
   - Connector parsing behavior
2. Integration tests:
   - End-to-end ingestion run with mocked connector payloads
3. Regression checks:
   - Re-running ingestion must not duplicate existing jobs
4. Performance checks:
   - Connector failures should not stop other sources

## File Plan

1. `autoapplyer/scraper/linkedin_scraper_plan.md` (this document)
2. `autoapplyer/scraper/linkedin_scraper.py` (optional connector implementation)
3. `autoapplyer/scraper/connectors_base.py` (shared interface + helpers)
4. `autoapplyer/services/ingestion_orchestrator.py` (source execution and upsert flow)
5. `autoapplyer/services/job_enrichment_agent.py` (AI summarization/tagging)
6. `autoapplyer/services/fit_scoring_agent.py` (AI ranking)
7. `scripts/test_linkedin_ingestion.py` (integration-style runner)

## Suggested Environment Flags

1. `INGEST_ENABLE_LINKEDIN=false`
2. `INGEST_ENABLE_GREENHOUSE=true`
3. `INGEST_ENABLE_LEVER=true`
4. `INGEST_ENABLE_ASHBY=true`
5. `INGEST_RATE_LIMIT_PER_MIN=20`
6. `INGEST_MAX_RETRIES=3`

## Milestones

1. Milestone A: shared schema + orchestrator + one compliant source working.
2. Milestone B: three compliant sources live with dedupe/upsert stability.
3. Milestone C: AI enrichment + fit scoring running on new jobs.
4. Milestone D: optional LinkedIn connector behind safety flag with full observability.

## Risks and Mitigations

1. Risk: connector breakage from HTML/layout changes.
   - Mitigation: source adapters + parser tests + fallback selectors.
2. Risk: legal/account risk from aggressive LinkedIn automation.
   - Mitigation: keep LinkedIn optional, constrained, and compliance-reviewed.
3. Risk: noisy duplicate postings.
   - Mitigation: canonical key strategy + AI-assisted duplicate resolution.
4. Risk: AI cost growth.
   - Mitigation: cache by description hash and only process new/changed jobs.

## Definition of Done

1. Pipeline runs end-to-end and stores jobs without duplication.
2. AI enrichment and fit scores are available for newly ingested jobs.
3. Source-level metrics and failures are visible after every run.
4. LinkedIn path is feature-flagged and safe to disable instantly.
5. Test suite covers parser behavior, dedupe, upsert, and orchestrator resilience.


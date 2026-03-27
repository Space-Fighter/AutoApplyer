## Plan: React Notion-Style YC Database

Build a React + JavaScript frontend backed by FastAPI + SQLModel where scraped YC jobs are displayed in a Notion-like table, with user-addable columns and user-managed tags. Use JSON-first custom field storage in `Job` for fastest delivery and lowest schema complexity, while keeping a clean migration path to normalized custom-value tables later.

**Steps**
1. Phase 1 — Lock data contract and scope (*blocks all later steps*): keep scraper contract as `scrape_yc_jobs()` = persist + return list, and define viewer scope as single-user local MVP unless changed later.
2. Phase 1 — Extend DB schema for JSON custom fields (*depends on 1*): in `autoapplyer/database/models.py`, add `custom_data` (JSON string) to `Job`; add `ColumnDefinition` table (column key/label/type/options/order/visibility); add tag tables (`Tag`, `JobTagLink`) for many-to-many tagging.
3. Phase 1 — DB initialization/migration safety (*depends on 2*): ensure `create_db()` in `autoapplyer/database/db.py` creates new tables and define deterministic bootstrap behavior for existing DBs (safe recreate/dev reset path documented).
4. Phase 2 — Persistence services (*depends on 2-3*): implement services in `autoapplyer/services/` for (a) upsert job by `job_url`, (b) read/update `custom_data`, (c) create/list/update/delete column definitions, (d) create/list/delete tags, (e) attach/detach tags on jobs.
5. Phase 2 — Scraper integration (*depends on 4*): keep scraper pipeline in `autoapplyer/scraper/yc_scraper.py` writing base job fields as before, leaving `custom_data` empty/default on ingest.
6. Phase 3 — FastAPI API layer (*depends on 4-5*): in backend package, add REST endpoints for jobs table retrieval, column-definition CRUD, and tag operations; include payload shape that merges fixed job fields + parsed JSON custom fields + tags.
7. Phase 3 — Query/view model shaping (*depends on 6*): implement API response adapters for Notion-like grid rendering (stable `columns[]`, `rows[]`, `tags[]` schema) and update endpoints for inline cell edits.
8. Phase 4 — React app scaffold (*depends on 6; parallel with 7 after endpoint contracts are known*): add `frontend/` React + JS app (Vite) with API client, environment config, and dev scripts that run alongside FastAPI.
9. Phase 4 — Notion-style table MVP (*depends on 8*): implement jobs table with dynamic columns from `ColumnDefinition`, editable cells (updates `custom_data`), visible fixed columns (`title`, `company`, `job_url`, `date_scraped`), and tag chips per row.
10. Phase 4 — Column & tag UX (*depends on 9*): add UI to create columns (type, label, options), reorder/hide columns, and add/remove tags on jobs; keep interactions minimal and table-centric (no extra pages/modals beyond required forms).
11. Phase 5 — End-to-end verification (*depends on 3-10*): verify scrape → DB persist → API read/write → React render/edit loop, including rerun upsert behavior and retained custom fields/tags.
12. Phase 5 — Hardening (*depends on 11*): add input validation for JSON/custom field types, graceful handling of unknown column keys, and API error responses suitable for inline UI feedback.

**Relevant files**
- `autoapplyer/scraper/yc_scraper.py` — preserve login/session flow and ensure scrape pipeline remains compatible with DB additions.
- `autoapplyer/database/models.py` — add `Job.custom_data`, `ColumnDefinition`, `Tag`, `JobTagLink`.
- `autoapplyer/database/db.py` — ensure table creation/init behavior supports new models.
- `autoapplyer/services/` — implement job/column/tag persistence and transformation logic.
- `autoapplyer/backend/main.py` — wire FastAPI app and routers.
- `autoapplyer/backend/` (new route modules) — jobs/columns/tags endpoints.
- `scripts/test_yc_scraper.py` — keep contract check for returned list + persistence side effects.
- `frontend/` (new) — React + JS Notion-like database viewer.
- `README.md` — update run instructions for backend + frontend + scraper workflow.

**Verification**
1. Scrape run: execute scraper script and confirm base rows are written/upserted by `job_url`.
2. API health: call jobs/columns/tags endpoints and verify JSON contracts match frontend needs.
3. UI load: run React app, confirm table renders rows and dynamic columns from DB.
4. Inline edit: edit custom field cell, refresh page, confirm value persists via `custom_data`.
5. Column creation: create a new column, confirm it appears in table and can be edited per row.
6. Tag flow: add/remove tags on a job, verify persistence and rerender.
7. Upsert safety: rerun scraper and confirm existing rows update without duplicate `job_url` entries; custom_data/tags remain intact.

**Decisions**
- Frontend stack: React + JavaScript.
- Custom-field storage: JSON-first (`custom_data`) for simplicity and speed.
- UX target: Notion-like table with addable columns + tags.
- Included scope: scraper persistence + API + React table workflow.
- Excluded scope for MVP: multi-user auth/permissions, advanced filter builder, drag-and-drop board/calendar views.

**Further Considerations**
1. Single-user vs multi-user remains open; recommendation is single-user local first, then add auth and ownership columns later.
2. Tag color strategy can start with backend-assigned defaults and user override in a lightweight color picker.
3. Migration path to normalized custom values is straightforward by backfilling from `Job.custom_data` into dedicated tables once advanced SQL filtering is needed.

**YC Scraper Plan**
- Step 1 — Contract + naming: in yc_scraper.py, define one public async function (`scrape_yc_jobs`) and standard output fields (`title`, `company`, `location`, `job_url`, `description`, `skill_tags`, `date_scraped`); this also fixes the current mismatch with test_yc_scraper.py.
- Step 2 — Browser/session setup: create a clean Playwright lifecycle (launch, context, page, close) with configurable headless mode and timeouts.
- Step 3 — Listing-page extraction: scrape YC job cards from `https://www.workatastartup.com/jobs`, collect unique job links plus lightweight metadata from the list page.
- Step 4 — Detail-page extraction: visit each job link (bounded concurrency with semaphore), extract rich fields (full description, tags, workplace/location, apply URL if present).
- Step 5 — Data normalization: clean whitespace/HTML, normalize missing values to `None`, dedupe by `job_url`, stamp UTC scrape time.
- Step 6 — Database persistence: map scraped data into Company + Job records using models.py and engine/session from db.py, with “insert-or-update by job_url”.
- Step 7 — Script wiring: keep a simple runner flow so test_yc_scraper.py can call scraper and print a sample job JSON.
- Step 8 — Reliability layer: add retry/backoff for page navigation and selector fallback paths so small YC DOM changes don’t break the run.
- Step 9 — Validation checklist: run scraper, confirm non-empty result, confirm DB rows are created, rerun to verify dedupe/upsert behavior.

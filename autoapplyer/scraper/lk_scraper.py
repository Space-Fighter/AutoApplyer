import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlmodel import Session, select

from autoapplyer.database.db import create_db, engine
from autoapplyer.database.models import Company, Job


@dataclass
class FilterConfig:
    required_keywords: list[str]
    excluded_keywords: list[str]
    allowed_workplace: list[str]
    allowed_locations: list[str]
    min_ai_score: float


def build_default_config() -> FilterConfig:
    return FilterConfig(
        required_keywords=["python", "backend"],
        excluded_keywords=["senior manager", "principal"],
        allowed_workplace=["remote", "hybrid"],
        allowed_locations=["india", "bangalore", "bengaluru", "pune", "delhi", "mumbai"],
        min_ai_score=0.55,
    )


def read_jobs_from_json(input_file: Path) -> list[dict[str, Any]]:
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}\n"
            "Create it with a JSON array of jobs. Example item:\n"
            '{"title":"Backend Engineer","company":"Acme","job_url":"https://...","description":"..."}'
        )

    payload = json.loads(input_file.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("Input JSON must be a list of job objects.")
    return payload


def normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def infer_role(title: str, description: str) -> str | None:
    text = f"{title} {description}".lower()
    if "machine learning" in text or "ml engineer" in text:
        return "ml engineer"
    if "ai engineer" in text:
        return "ai engineer"
    if "backend" in text:
        return "backend engineer"
    if "full stack" in text or "fullstack" in text:
        return "full stack engineer"
    return None


def infer_job_type(title: str, description: str) -> str | None:
    text = f"{title} {description}".lower()
    if "intern" in text or "internship" in text:
        return "intern"
    if "contract" in text:
        return "contract"
    if "part-time" in text or "part time" in text:
        return "part-time"
    return "full-time"


def ai_style_fit_score(title: str, description: str, config: FilterConfig) -> float:
    text = f"{title} {description}".lower()

    positive_keywords = [
        "python",
        "fastapi",
        "django",
        "flask",
        "sql",
        "postgres",
        "api",
        "backend",
        "automation",
        "llm",
        "ai",
    ]
    penalty_keywords = ["director", "vp", "staff+", "architect", "15+ years"]

    score = 0.0
    for kw in positive_keywords:
        if kw in text:
            score += 0.08

    for kw in config.required_keywords:
        if kw in text:
            score += 0.12

    for kw in penalty_keywords:
        if kw in text:
            score -= 0.15

    return max(0.0, min(1.0, score))


def passes_filters(job: dict[str, Any], config: FilterConfig) -> tuple[bool, float, str]:
    title = normalize_text(job.get("title"))
    description = normalize_text(job.get("description"))
    workplace = normalize_text(job.get("workplace"))
    location = normalize_text(job.get("location"))

    blob = f"{title} {description}"

    if config.required_keywords and not any(kw in blob for kw in config.required_keywords):
        return False, 0.0, "missing required keywords"

    if any(kw in blob for kw in config.excluded_keywords):
        return False, 0.0, "contains excluded keywords"

    if workplace and config.allowed_workplace and workplace not in config.allowed_workplace:
        return False, 0.0, "workplace filtered out"

    if location and config.allowed_locations and not any(loc in location for loc in config.allowed_locations):
        return False, 0.0, "location filtered out"

    score = ai_style_fit_score(title=title, description=description, config=config)
    if score < config.min_ai_score:
        return False, score, "ai score below threshold"

    return True, score, "accepted"


def split_location(location: str | None) -> tuple[str | None, str | None, str | None]:
    if not location:
        return None, None, None

    parts = [p.strip() for p in location.split(",")]
    if len(parts) == 1:
        return parts[0], None, None
    if len(parts) == 2:
        return parts[0], None, parts[1]
    return parts[0], parts[1], parts[2]


def upsert_company(session: Session, company_name: str) -> Company:
    existing_company = session.exec(select(Company).where(Company.name == company_name)).first()
    if existing_company:
        return existing_company

    company = Company(name=company_name)
    session.add(company)
    session.commit()
    session.refresh(company)
    return company


def upsert_job(session: Session, raw_job: dict[str, Any], ai_score: float) -> tuple[Job, bool]:
    title = (raw_job.get("title") or "").strip()
    company_name = (raw_job.get("company") or "").strip() or "Unknown Company"
    job_url = (raw_job.get("job_url") or "").strip()
    description = (raw_job.get("description") or "").strip()
    skill_tags = raw_job.get("skill_tags") or ""

    if not title or not job_url:
        raise ValueError("Each job must have non-empty 'title' and 'job_url'.")

    company = upsert_company(session, company_name)
    existing_job = session.exec(select(Job).where(Job.job_url == job_url)).first()

    city, region, country = split_location(raw_job.get("location"))
    workplace = normalize_text(raw_job.get("workplace")) or None

    summary = f"AI fit score: {ai_score:.2f}"

    if existing_job:
        existing_job.title = title
        existing_job.description = description or existing_job.description
        existing_job.skill_tags = skill_tags or existing_job.skill_tags
        existing_job.summary = summary
        existing_job.company_id = company.id
        existing_job.role = infer_role(title, description)
        existing_job.job_type = infer_job_type(title, description)
        existing_job.city = city
        existing_job.region = region
        existing_job.country = country
        existing_job.workplace = workplace
        existing_job.date_scraped = datetime.utcnow()

        session.add(existing_job)
        session.commit()
        session.refresh(existing_job)
        return existing_job, False

    new_job = Job(
        title=title,
        role=infer_role(title, description),
        job_type=infer_job_type(title, description),
        city=city,
        region=region,
        country=country,
        workplace=workplace,
        company_id=company.id,
        job_url=job_url,
        skill_tags=skill_tags,
        description=description,
        summary=summary,
        date_scraped=datetime.utcnow(),
    )
    session.add(new_job)
    session.commit()
    session.refresh(new_job)
    return new_job, True


def run_ingestion(input_file: Path, dry_run: bool = False) -> None:
    config = build_default_config()
    jobs = read_jobs_from_json(input_file)

    print(f"Loaded {len(jobs)} jobs from {input_file}")
    create_db()

    accepted = 0
    inserted = 0
    updated = 0

    with Session(engine) as session:
        for idx, job in enumerate(jobs, start=1):
            ok, score, reason = passes_filters(job, config)
            title = job.get("title", "Unknown title")
            company = job.get("company", "Unknown company")

            if not ok:
                print(f"[SKIP {idx}] {title} @ {company} -> {reason}")
                continue

            accepted += 1
            print(f"[PASS {idx}] {title} @ {company} -> score={score:.2f}")

            if dry_run:
                continue

            _, is_insert = upsert_job(session, job, score)
            if is_insert:
                inserted += 1
            else:
                updated += 1

    print("")
    print("Ingestion summary")
    print(f"- accepted: {accepted}")
    print(f"- inserted: {inserted}")
    print(f"- updated: {updated}")
    print(f"- dry_run: {dry_run}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MVP LinkedIn-style job ingestion: read jobs JSON, apply filters, write to DB."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path(__file__).with_name("linkedin_jobs_input.json"),
        help="Path to input JSON file (list of job objects).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run filters/scoring without writing to database.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_ingestion(input_file=args.input, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

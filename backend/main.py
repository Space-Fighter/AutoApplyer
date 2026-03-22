# main.py

from scraper import scrape_linkedin_jobs
from database import init_db, insert_job


def main():

    init_db()

    jobs = scrape_linkedin_jobs("python developer")

    for job in jobs:

        insert_job(job)

    print(f"Saved {len(jobs)} jobs")


if __name__ == "__main__":
    main()
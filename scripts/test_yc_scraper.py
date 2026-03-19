import asyncio
import sys
sys.path.insert(0, '../')

from autoapplyer.scraper.yc_scraper import scrape_yc_jobs
import json


async def main():
    print("Starting YC jobs scraper...")
    jobs = await scrape_yc_jobs()
    
    print(f"\n✅ Scraped {len(jobs)} jobs!")
    
    if jobs:
        print("\n--- First Job Example ---")
        print(json.dumps(jobs[0], indent=2, default=str))
    
    return jobs


if __name__ == "__main__":
    jobs = asyncio.run(main())

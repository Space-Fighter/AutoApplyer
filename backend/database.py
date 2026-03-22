# database.py

import sqlite3


def init_db():

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (

        job_url TEXT PRIMARY KEY,
        title TEXT,
        company TEXT,
        location TEXT,
        skills TEXT

    )
    """)

    conn.commit()
    conn.close()


def insert_job(job):

    conn = sqlite3.connect("jobs.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO jobs
    (job_url, title, company, location, skills)

    VALUES (?, ?, ?, ?, ?)
    """, (

        job["job_url"],
        job["title"],
        job["company"],
        job["location"],
        job.get("skills")

    ))

    conn.commit()
    conn.close()
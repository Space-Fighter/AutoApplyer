from sqlmodel import SQLModel, create_engine
"""
PostgreSQL → the database

SQLModel → Python library for working with the database

psycopg2 → driver that connects Python to PostgreSQL
"""
DATABASE_URL = "sqlite:///jobs.db"

engine = create_engine(DATABASE_URL, echo=True)

def create_db():
    SQLModel.metadata.create_all(engine)
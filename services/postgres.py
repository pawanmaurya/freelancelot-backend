from datetime import datetime
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model.job import Job
import os

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def save_jobs(jobs: list[dict]):
    session = SessionLocal()
    try:
        for job in jobs:
            logging.info(f"[DB] Saving job: {job.get('title', 'No title')}")

            if not job.get("url") or not job.get("title"):
                logging.warning("[DB] Skipping job with missing URL or title")
                continue

            # Upwork jobs have stable IDs → use to deduplicate
            exists = session.query(Job).filter_by(id=job["url"].split("~")[-1]).first()
            if exists:
                continue  # skip if already saved

            new_job = Job(
                id=job["url"].split("~")[-1],
                title=job["title"],
                url=job["url"],
                type=job["type"],
                category=job["category"],
                description=job["description"],
                skills=",".join(job["skills"]),
                budget=float(job["budget"] or 0),
                location=job["location"],
                client_spend=job["client_spend"],
                client_rating=job["client_rating"],
                published_at=datetime.fromisoformat(job["published_at"])
            )
            session.add(new_job)

        session.commit()
    except Exception as e:
        logging.error(f"[DB] Error saving jobs: {e}")
        session.rollback()
    finally:
        session.close()

def setup_database():
    # Create tables if they don't exist
    Job.metadata.create_all(engine)
    logging.info("[DB] Database setup complete")

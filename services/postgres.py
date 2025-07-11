from datetime import datetime, timedelta
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from model.job import Job
from model.filter import Filter, FilterKeyword, FilterCategory, Profile
import os
from dotenv import load_dotenv
from sqlalchemy import and_
from model.job_alert import JobAlert

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def save_jobs(jobs: list[dict]):
    session = SessionLocal()
    try:
        for job in jobs:
            # logging.info(f"[DB] Saving job: {job.get('title', 'No title')}")

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

        logging.info(f"[DB] Saving {len(jobs)} jobs")
        session.commit()
    except Exception as e:
        logging.error(f"[DB] Error saving jobs: {e}")
        session.rollback()
    finally:
        session.close()

def setup_database():
    # Create tables if they don't exist
    Job.metadata.create_all(engine)
    JobAlert.metadata.create_all(engine)
    logging.info("[DB] Database setup complete")

def get_latest_jobs(minutes=10):
    session = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(minutes=minutes)
        jobs = session.query(Job).filter(Job.published_at >= since).all()
        return [
            {
                "title": job.title,
                "id": job.id,
                "url": job.url,
                "type": job.type,
                "category": job.category,
                "description": job.description,
                "skills": job.skills.split(",") if job.skills else [],
                "budget": float(job.budget) if job.budget is not None else 0,
                "location": job.location,
                "client_spend": job.client_spend,
                "client_rating": job.client_rating,
                "published_at": job.published_at,
            }
            for job in jobs
        ]
    finally:
        session.close()

def log_job_alert(user_id, job_id):
    session = SessionLocal()
    try:
        session.execute(
            text("INSERT INTO job_alerts (user_id, job_id, sent_at) VALUES (:user_id, :job_id, :sent_at)"),
            {"user_id": user_id, "job_id": job_id, "sent_at": datetime.utcnow()}
        )
        session.commit()
    finally:
        session.close()

def has_alert_been_sent(user_id, job_id):
    session = SessionLocal()
    try:
        result = session.execute(
            text("SELECT 1 FROM job_alerts WHERE user_id = :user_id AND job_id = :job_id"),
            {"user_id": user_id, "job_id": job_id}
        ).fetchone()
        return result is not None
    finally:
        session.close()

def alert_count_last_hour(user_id):
    session = SessionLocal()
    try:
        result = session.execute(
            text("""
            SELECT COUNT(*) FROM job_alerts
            WHERE user_id = :user_id AND sent_at > NOW() - INTERVAL '1 hour'
            """),
            {"user_id": user_id}
        ).scalar()
        return result
    finally:
        session.close()

def get_all_alerts_for_users_and_jobs(user_ids, job_ids):
    session = SessionLocal()
    try:
        if not user_ids or not job_ids:
            return set()
        result = session.execute(
            text("""
                SELECT user_id, job_id FROM job_alerts
                WHERE user_id = ANY(ARRAY[:user_ids]::uuid[]) AND job_id = ANY(:job_ids)
            """),
            {"user_ids": user_ids, "job_ids": job_ids}
        )
        return set((row[0], row[1]) for row in result)
    finally:
        session.close()

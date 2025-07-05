from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List
from datetime import datetime, timedelta
from fastapi import Depends
from services.postgres import SessionLocal
from model.job import Job
from utils.authcheck import verify_api_key

router = APIRouter()

@router.get("/fetch_filtered_jobs")
def fetch_filtered_jobs(
    keywords: List[str] = Query(default=[]),
    categories: List[str] = Query(default=[]),
    _ = Depends(verify_api_key)
):
    session: Session = SessionLocal()
    try:
        query = session.query(Job)

        # Build OR conditions
        or_conditions = []

        if keywords:
            for kw in keywords:
                kw = kw.strip()
                if kw:
                    or_conditions.append(Job.title.ilike(f"%{kw}%"))
                    or_conditions.append(Job.description.ilike(f"%{kw}%"))

        if categories:
            or_conditions.append(Job.category.in_(categories))

        if or_conditions:
            query = query.filter(or_(*or_conditions))

        # Limit to last 1 day
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        query = query.filter(Job.published_at >= one_day_ago)

        matches = query.order_by(Job.published_at.desc()).limit(20).all()
        total_matches = query.count()

        results = [
            {
                "title": job.title,
                "url": job.url,
                "budget": job.budget,
                "published_at": job.published_at,
                "category": job.category,
                "type": job.type,
                "description": job.description[:300],  # Limit description length
                "skills": job.skills.split(",") if job.skills else [],
                "location": job.location,
                "budget": job.budget

            }
            for job in matches
        ]

        return {
            "matches": results,
            "total_matches": total_matches
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()

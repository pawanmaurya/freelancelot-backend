from fastapi import APIRouter, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
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
        # Categories are mandatory
        if not categories:
            raise HTTPException(status_code=400, detail="Categories parameter is required")
        
        query = session.query(Job)
        
        # First filter by categories (mandatory)
        query = query.filter(Job.category.in_(categories))
        
        # If keywords are provided, add keyword filtering with AND condition
        if keywords:
            keyword_conditions = []
            for kw in keywords:
                kw = kw.strip()
                if kw:
                    keyword_conditions.append(
                        or_(
                            Job.title.ilike(f"%{kw}%"),
                            Job.description.ilike(f"%{kw}%")
                        )
                    )
            
            # Apply keyword conditions with AND logic
            if keyword_conditions:
                query = query.filter(and_(*keyword_conditions))

        # Limit to last 1 day
        one_day_ago = datetime.utcnow() - timedelta(days=1)
        query = query.filter(Job.published_at >= one_day_ago)

        matches = query.order_by(Job.published_at.desc()).all()
        total_matches = query.count()

        results = [
            {
                "title": job.title,
                "url": job.url,
                "budget": job.budget,
                "published_at": job.published_at,
                "category": job.category,
                "type": job.type,
                "description": job.description,  # Limit description length
                "skills": job.skills.split(",") if job.skills is not None else [],
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

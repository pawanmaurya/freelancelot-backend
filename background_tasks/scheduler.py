from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from services.postgres import save_jobs
from services.apify_scrapper import fetch_upwork_jobs_from_apify
import logging
from datetime import datetime

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Wrap the async function so it can be scheduled
    async def run_crawler():
        jobs = await fetch_upwork_jobs_from_apify()
        if jobs:
            save_jobs(jobs)
            logging.info(f"[Scheduler] Fetched and saved {len(jobs)} jobs")
        else:
            logging.error("[Scheduler] No jobs fetched")

    # Add job to run immediately and then every minute
    scheduler.add_job(
        run_crawler, 
        trigger=IntervalTrigger(minutes=1),
        next_run_time=datetime.now()
    )
    scheduler.start()
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from services.postgres import save_jobs
import logging

def start_scheduler():


    scheduler = AsyncIOScheduler()
    
    # Wrap the async function so it can be scheduled
    async def run_crawler():
        jobs = await fetch_upwork_jobs()
        if jobs:
            await save_jobs(jobs)
        else:
            logging.error("[Scheduler] No jobs fetched")

        logging.error(f"[Scheduler] Fetched {len(jobs)} jobs")

    scheduler.add_job(run_crawler, trigger=IntervalTrigger(minutes=1))
    scheduler.start()
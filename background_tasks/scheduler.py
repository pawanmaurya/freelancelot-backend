from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from services.postgres import save_jobs, get_latest_jobs, has_alert_been_sent, log_job_alert, alert_count_last_hour
from services.apify_scrapper import fetch_upwork_jobs_from_apify
from services.notification import match_jobs_to_filter, send_telegram_alert
from services.supabase import get_users_with_filters_and_telegram
import logging
from datetime import datetime

def notify_users_of_new_jobs():
    jobs = get_latest_jobs()
    users = get_users_with_filters_and_telegram()
    for user in users:
        jobs_to_alert = []
        for filter in user['filters']:
            matches = match_jobs_to_filter(jobs, filter)
            for job in matches:
                if not has_alert_been_sent(user['user_id'], job['url']):
                    jobs_to_alert.append(job)
        # Optional: Rate limit (e.g., max 10 alerts/hour)
        if jobs_to_alert and alert_count_last_hour(user['user_id']) < 10:
            jobs_to_send = jobs_to_alert[:10]
            send_telegram_alert(user['telegram_id'], jobs_to_send)
            for job in jobs_to_send:
                log_job_alert(user['user_id'], job['url'])

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    # Wrap the async function so it can be scheduled
    async def run_crawler():
        jobs = await fetch_upwork_jobs_from_apify()
        if jobs:
            save_jobs(jobs)
            logging.info(f"[Scheduler] Fetched and saved {len(jobs)} jobs")
            notify_users_of_new_jobs()
        else:
            logging.error("[Scheduler] No jobs fetched")

    # Add job to run immediately and then every minute
    scheduler.add_job(
        run_crawler, 
        trigger=IntervalTrigger(minutes=1),
        next_run_time=datetime.now()
    )
    scheduler.start()
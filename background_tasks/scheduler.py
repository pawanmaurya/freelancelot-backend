from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from services.postgres import save_jobs, get_latest_jobs, has_alert_been_sent, log_job_alert, alert_count_last_hour, get_all_alerts_for_users_and_jobs
from services.apify_scrapper import fetch_upwork_jobs_from_apify
from services.notification import match_jobs_to_filter, send_telegram_alert
from services.supabase import get_users_with_filters_and_telegram
import logging
from datetime import datetime
from uuid import UUID

def notify_users_of_new_jobs():
    jobs = get_latest_jobs()
    users = get_users_with_filters_and_telegram()
    user_ids = [user['user_id'] for user in users]
    job_ids = [job['id'] for job in jobs]
    sent_alerts = get_all_alerts_for_users_and_jobs(user_ids, job_ids)  # returns set of (user_id, job_id)
    logging.info(f"[Scheduler] Sent {sent_alerts} alerts")
    sent_this_run = set()  # Track (user_id, job_id) sent in this run
    for job in jobs:
        for user in users:
            for filter in user['filters']:
                key = (UUID(str(user['user_id'])), job['id'])
                # logging.info(f"[Scheduler] key: {key}")
                if match_jobs_to_filter([job], filter):
                    if key not in sent_alerts and key not in sent_this_run:
                        send_telegram_alert(user['telegram_id'], [job])
                        log_job_alert(user['user_id'], job['id'])
                        sent_this_run.add(key)


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
        trigger=IntervalTrigger(seconds=30),
        next_run_time=datetime.now()
    )
    scheduler.start()
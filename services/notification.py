import os
import requests
import logging
import json
from utils.logger import setup_logging
from datetime import datetime

logger = logging.getLogger(__name__)


def match_jobs_to_filter(jobs, filter):
    matched = []
    keywords = set([kw.lower() for kw in filter['keywords']])
    categories = set([cat.lower() for cat in filter['categories']])
    min_price = filter.get('min_price')
    max_price = filter.get('max_price')

    for job in jobs:
        job_text = (job['title'] + ' ' + job['description']).lower()
        if keywords and not any(kw in job_text for kw in keywords):
            continue
        if categories and job.get('category', '').lower() not in categories:
            continue
        if min_price is not None and job.get('budget', 0) < min_price:
            continue
        if max_price is not None and job.get('budget', 0) > max_price:
            continue
        matched.append(job)
    # logger.info(f"Matched {len(matched)} jobs for filter '{filter.get('name', '')}'")
    return matched

def send_telegram_alert(telegram_chat_id, jobs):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        raise Exception("TELEGRAM_BOT_TOKEN not set in environment variables")
    if not jobs:
        logger.info(f"No jobs to send to telegram_id {telegram_chat_id}")
        return
    # Sort jobs by published_at ascending (oldest first)
    jobs = sorted(jobs, key=lambda job: job.get('published_at') or datetime.min)
    for job in jobs:
        id = job.get('id', 'N/A')
        title = job.get('title', 'No Title')
        url = job.get('url', '#')
        price = f"${job['budget']:.2f}" if job.get('budget') else "N/A"
        job_type = job.get('type', 'N/A')
        category = job.get('category', 'N/A')
        location = job.get('location', 'N/A')
        client_spend = f"${job['client_spend']:.0f}" if job.get('client_spend') else "N/A"
        client_rating = f"{job['client_rating']:.1f}★" if job.get('client_rating') else "N/A"
        published_at = job.get('published_at')
        published_str = published_at.strftime('%b %d, %Y') if published_at else "N/A"
        skills = job.get('skills', '')
        if isinstance(skills, list):
            skills_str = ' • '.join([s.strip() for s in skills if s.strip()])
        elif isinstance(skills, str):
            skills_str = ' • '.join([s.strip() for s in skills.split(',') if s.strip()])
        else:
            skills_str = "N/A"
        desc = job.get('description', '')
        desc_short = desc[:200] + ("..." if len(desc) > 200 else "")

        # Calculate posted time
        now = datetime.utcnow()
        if published_at:
            delta = now - published_at
            minutes = int(delta.total_seconds() // 60)
            if minutes < 1:
                posted_str = "just now"
            elif minutes == 1:
                posted_str = "1 minute ago"
            elif minutes < 60:
                posted_str = f"{minutes} minutes ago"
            else:
                hours = minutes // 60
                posted_str = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            posted_str = "unknown"

        message = (
            f"<b>{title}</b>\n\n"
            f"{category} • {job_type} • <b>Budget: {price}</b>\n"
            f"<b>Skills</b>\n{skills_str}\n\n"
            f"<b>About Client</b>\n🌍 {location} • 💸 Total spent: {client_spend} • ⭐ Rating: {client_rating} • 📅 Since: {published_str}\n"
            f"🕒 Posted {posted_str}\n\n"
            f"<b>Description</b>\n<pre>{desc_short}</pre>\n\n"
        )

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Apply Now", "url": url}
                ]
            ]
        }

        url_api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": json.dumps(reply_markup)
        }
        try:
            response = requests.post(url_api, data=payload)
            if response.status_code == 200:
                logger.info(f"Sent jobId '{id}' to telegram_id {telegram_chat_id}")
            else:
                # logger.error(f"Failed to send alert to telegram_id {telegram_chat_id}: {response.text}")
                # TODO add error back
                pass
        except Exception as e:
            # TODO error back
            # logger.error(f"Exception sending alert to telegram_id {telegram_chat_id}: {e}") 
            pass
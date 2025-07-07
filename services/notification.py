import os
import requests
import logging
from utils.logger import setup_logging

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
    logger.info(f"Matched {len(matched)} jobs for filter '{filter.get('name', '')}'")
    return matched

def send_telegram_alert(telegram_chat_id, jobs):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        raise Exception("TELEGRAM_BOT_TOKEN not set in environment variables")
    if not jobs:
        logger.info(f"No jobs to send to telegram_id {telegram_chat_id}")
        return
    message = "<b>New Upwork Jobs:</b>\n\n"
    for job in jobs:
        title = job['title']
        url = job['url']
        price = f"${job['budget']:.2f}" if job.get('budget') else "N/A"
        desc = job['description'][:150] + ("..." if len(job['description']) > 150 else "")
        message += f"• <a href='{url}'>{title}</a> | <b>{price}</b>\n{desc}\n\n"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": telegram_chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info(f"Sent {len(jobs)} job(s) to telegram_id {telegram_chat_id}")
        else:
            logger.error(f"Failed to send alert to telegram_id {telegram_chat_id}: {response.text}")
    except Exception as e:
        logger.error(f"Exception sending alert to telegram_id {telegram_chat_id}: {e}") 
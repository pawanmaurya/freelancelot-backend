import os
import httpx
import logging
from typing import List, Dict
from dotenv import load_dotenv
from datetime import datetime
import traceback

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
APIFY_URL = "https://api.apify.com/v2/actor-tasks/vigorous_juggernaut~upwork-extractor-task/run-sync-get-dataset-items"

async def fetch_upwork_jobs_from_apify() -> List[Dict]:
    headers = { "Accept": "application/json" }
    params = { "token": APIFY_API_TOKEN }

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            logging.info("[Crawler] Fetching Upwork jobs from Apify...")
            res = await client.post(APIFY_URL, headers=headers, params=params)
            res.raise_for_status()
            data = res.json()

            if not data:
                logging.warning("[Crawler] No jobs found.")
                return []

            logging.info(f"[Crawler] Jobs data: {data}")

            jobs = []
            for item in data:
                job = {
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "type": item.get("type", ""),
                    "description": item.get("description", "")[:300],
                    "category": item.get("category", {}).get("name") or "uncategorized",
                    "skills": [s.get("name", "") for s in item.get("skills") or []],
                    "budget": (
                        item.get("fixed") and item["fixed"].get("budget") and item["fixed"]["budget"].get("amount")
                    ) if item.get("type") == "FIXED" else (
                        item.get("hourly") and item["hourly"].get("max")
                    ),
                    "location": (
                        item.get("buyer") and item["buyer"].get("location") and item["buyer"]["location"].get("country")
                    ),
                    "client_spend": (
                        ((item.get("buyer") or {}).get("stats") or {}).get("totalCharges") or {}
                    ).get("amount"),
                    "client_rating": (
                        item.get("buyer") and item["buyer"].get("stats") and item["buyer"]["stats"].get("score")
                    ),
                    "published_at": format_publish_time(item.get("ts_publish", ""))
                }
                jobs.append(job)


            logging.info(f"[Crawler] Fetched {len(jobs)} jobs")
            return jobs

    except Exception as e:
        logging.error(traceback.format_exc())
        logging.error(f"[Crawler] Error: {e}")
        return []


def format_publish_time(iso_str: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return ""
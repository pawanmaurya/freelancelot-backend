from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from utils.logger import setup_logging
from background_tasks.scheduler import start_scheduler
from services.apify_scrapper import fetch_upwork_jobs_from_apify
import logging
from routers import jobs
from services.postgres import save_jobs, setup_database
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routers.telegram import router as telegram_router

load_dotenv()

app = FastAPI()

# Get allowed origins from env, split by comma
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Testing
@app.get("/ping")
async def ping():
    jobs = await fetch_upwork_jobs_from_apify()
    if jobs:
        save_jobs(jobs)
        logging.info(f"[Scheduler] saved {len(jobs)} jobs")
    else:
        logging.error("[Scheduler] No jobs fetched")

    return {"message": jobs}


@app.on_event("startup")
def startup_event():
    setup_logging()
    setup_database()
    start_scheduler()


app.include_router(jobs.router, prefix="/api")
app.include_router(telegram_router)

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from agents.autonomous import run_autonomous_scraper

logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = BackgroundScheduler()

def start_scheduler():
    """
    Starts the background scheduler.
    """
    if not scheduler.running:
        # Schedule the autonomous agent to run every 6 hours
        scheduler.add_job(
            func=run_autonomous_scraper,
            trigger=IntervalTrigger(hours=6),
            id='autonomous_job_scraper',
            name='Run the autonomous LangGraph job scraper',
            replace_existing=True
        )
        scheduler.start()
        logger.info("Started autonomous background scheduler (running every 6 hours).")

def shutdown_scheduler():
    """
    Shuts down the background scheduler safely.
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Stopped autonomous background scheduler.")

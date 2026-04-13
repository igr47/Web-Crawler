import os
import sys
from dotenv import load_dotenv

load_dotenv()

def setup_database():
    """Initialize database"""
    from database.models import init_db
    from config import config
    
    print("Setting up database...")
    session = init_db(config.DATABASE_URL)
    print("Database setup complete")
    return session

def run_initial_crawl():
    """Run initial full crawl of all sources"""
    from initial_crawl import run_initial_crawl as initial_crawl
    print("Running initial full crawl of all sources...")
    result = initial_crawl()
    print("Initial crawl completed!")
    return result

def start_api():
    """Start FastAPI server"""
    import uvicorn
    print("Starting API server...")
    uvicorn.run(
        "api.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

def start_celery_worker():
    """Start Celery worker"""
    import subprocess
    print("Starting Celery worker...")
    subprocess.run([
        "celery", "-A", "workers.crawler_worker", "worker",
        "--loglevel=info", "--concurrency=4"
    ])

def start_celery_beat():
    """Start Celery beat scheduler"""
    import subprocess
    print("Starting Celery beat scheduler...")
    subprocess.run([
        "celery", "-A", "workers.crawler_worker", "beat",
        "--loglevel=info"
    ])

def run_crawler_once():
    """Run crawler once (for testing)"""
    from workers.crawler_worker import crawl_all_sources
    result = crawl_all_sources.delay()
    print(f"Crawler started with task ID: {result.id}")
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="News Sentiment Crawler")
    parser.add_argument("--mode", choices=["api", "worker", "beat", "crawl", "initial-crawl", "setup"], 
                       default="api", help="Run mode")
    
    args = parser.parse_args()
    
    if args.mode == "setup":
        setup_database()
    elif args.mode == "initial-crawl":
        setup_database()
        run_initial_crawl()
    elif args.mode == "api":
        setup_database()
        start_api()
    elif args.mode == "worker":
        start_celery_worker()
    elif args.mode == "beat":
        start_celery_beat()
    elif args.mode == "crawl":
        run_crawler_once()

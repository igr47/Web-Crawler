from celery import Celery
from celery.app import task
from celery.schedules import crontab, schedule
from datetime import datetime
import logging
import json
import sys
import os

from requests import get, options

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'crawler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,

    # schedule task configurations
    beat_schedule={
        # Fast crawl for major news site (every five minutes)
        'crawl-major-sources': {
            'task': 'crawler.crawl_major_sources',
            'schedule': 300.0, # 5 minutes
            'options': {'queue': 'fast_crawl'}
        },
        # Full crawl for all sources (every one hour)
        'crawl_all_sources': {
            'task': 'crawler.crawl_all_sources',
            'schedule': 3600.0, # 1 hour
            'options': {'queue': 'full_crawl'}
        },
        #Update sentiment aggregations ()
                # Update sentiment aggregations (every 15 minutes)
        'update-sentiment-aggregations': {
            'task': 'crawler.update_sentiment_aggregations',
            'schedule': 900.0,  # 15 minutes
        },
        # Clean old data (daily at 2 AM)
        'clean-old-data': {
            'task': 'crawler.clean_old_data',
            'schedule': crontab(hour=2, minute=0),
        },
        # Health check (every minute)
        'health-check': {
            'task': 'crawler.health_check',
            'schedule': 60.0,
        },
    },

    # Task routing
    task_routes={
        'crawler.crawl_major_sources': {'queue': 'fast_crawl'},
        'crawler.crawl_all_sources': {'queue': 'full_crawl'},
        'crawler.update_sentiment_aggregations': {'queue': 'default'},
        'crawler.clean_old_data': {'queue': 'maintenance'},
        'crawler.health_check': {'queue': 'monitoring'},
    },
)

@celery_app.task(name='crawler.crawl_major_sources')
def crawl_major_sources():
    """Task to crawl all news sources"""
    from database.connections import get_db_session
    from crawlers.news_crawler import NewsCrawler
    from crawlers.sentiment_analyzer import SentimentAnalyzer
    from processors.category_classifier import CategoryClassifier
    from database.models import NewsArticle, CrawlHistory
    from config import config
    
    db = get_db_session()
    sentiment_analyzer = SentimentAnalyzer()
    classifier = CategoryClassifier()
    crawler = NewsCrawler(db, sentiment_analyzer, config)

    # Only crawl top major sources for speed
    major_sources = {
        "BBC NEWS": config.RSS_FEEDS.get("BBC NEWS"),
        "CNN": config.RSS_FEEDS.get("CNN"),
        "Reuters": config.RSS_FEEDS.get("Reuters"),
        "TechCrunch": config.RSS_FEEDS.get("TechCrunch"),
        "The Guardian": config.RSS_FEEDS.get("The Guardian"),
        "Sky News": config.RSS_FEEDS.get("Sky News"),
        "CBC News": config.RSS_FEEDS.get("CBC News"),
        "The Verge": config.RSS_FEEDS.get("The Verge"),
        "Yahoo Finance": config.RSS_FEEDS.get("Yahoo Finance"),
        "MarketWatch": config.RSS_FEEDS.get("MarketWatch"),
        "USA TODAY": config.RSS_FEEDS.get("USA TODAY")
    }

    # Temporarily override RSS feeds
    original_feeds = config.RSS_FEEDS.copy()
    config.RSS_FEEDS = major_sources
    
    # Track crawl
    crawl_record = CrawlHistory(
        source="major_sources_fast",
        start_time=datetime.utcnow(),
        status="running"
    )
    db.add(crawl_record)
    db.commit()
    
    try:
        # Crawl RSS feeds
        articles = crawler.crawl_rss_feeds()
        
        # Process each article
        new_count = 0
        for article_data in articles:
            # Check if article already exists
            existing = db.query(NewsArticle).filter(
                NewsArticle.url == article_data['url']
            ).first()

            if existing: 
                continue


            # Classify category
            category, keywords = classifier.classify_article(
                article_data['title'],
                article_data['content']
            )
            
            # Create article record
            article = NewsArticle(
                url=article_data['url'],
                title=article_data['title'],
                content=article_data['content'],
                summary=article_data['summary'],
                source=article_data['source'],
                published_date=article_data['published_date'],
                category=category,
                sentiment_score=article_data['sentiment_score'],
                sentiment_label=article_data['sentiment_label'],
                confidence_score=article_data['confidence_score'],
                keywords=json.dumps(article_data['keywords']),
                image_url=article_data.get('image_url'),
                processed=True
            )
            
            db.add(article)
            new_count += 1
        
        db.commit()
        
        # Update crawl record
        crawl_record.end_time = datetime.utcnow()
        crawl_record.articles_found = len(articles)
        crawl_record.articles_new = new_count
        crawl_record.status = "completed"
        db.commit()

        # Restore original feeds
        config.RSS_FEEDS = original_feeds
        
        logger.info(f"Fast crawl completed: {new_count} new articles")
        
        return {
            "status": "success",
            "articles_found": len(articles),
            "new_articles": new_count
            #"crawl_type": "fast"
        }
        
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        crawl_record.status = "failed"
        crawl_record.error_message = str(e)
        db.commit()
        config.RSS_FEEDS = original_feeds
        raise

@celery_app.task(name='crawler.update_sentiment_aggregations')
def update_sentiment_aggregations():
    """Update category sentiment aggregations"""
    from database.connection import get_db_session
    from processors.aggregator import SentimentAggregator
    from database.models import CategoryAggregation
    
    db = get_db_session()
    aggregator = SentimentAggregator(db)
    
    # Update aggregations
    results = aggregator.aggregate_by_category('day')
    
    for category, data in results.items():
        agg = CategoryAggregation(
            category=category,
            avg_sentiment=data['avg_sentiment'],
            total_articles=data['total_articles'],
            positive_count=data['positive_count'],
            negative_count=data['negative_count'],
            neutral_count=data['neutral_count']
        )
        db.add(agg)
    
    db.commit()
    
    return {"status": "success", "categories_updated": len(results)}

@celery_app.task(name='crawler.clean_old_data')
def clean_old_data():
    """Clean articles older than 30 days"""
    from database.connections import get_db_session
    from database.models import NewsArticle
    
    db = get_db_session()
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    
    deleted = db.query(NewsArticle).filter(
        NewsArticle.published_date < cutoff_date
    ).delete()
    
    db.commit()
    
    logger.info(f"Cleaned {deleted} old articles")
    
    return {"status": "success", "deleted_articles": deleted}

@celery_app.task(name='crawler.health_check')
def health_check():
    """Monitor crawler health and alert if issues"""
    from database.connections import get_db_session
    from database.models import CrawlHistory
    from datetime import timedelta
    
    db = get_db_session()
    
    # Check last successful crawl
    last_crawl = db.query(CrawlHistory).filter(
        CrawlHistory.status == "completed"
    ).order_by(CrawlHistory.end_time.desc()).first()
    
    if last_crawl:
        time_since_last = datetime.utcnow() - last_crawl.end_time
        if time_since_last > timedelta(hours=2):
            logger.warning(f"No successful crawl in {time_since_last}")
            
            # Trigger alert (you can add email/webhook here)
            return {
                "status": "warning",
                "message": f"No successful crawl in {time_since_last}",
                "last_crawl": last_crawl.end_time.isoformat()
            }
    
    return {
        "status": "healthy",
        "last_crawl": last_crawl.end_time.isoformat() if last_crawl else None
    }

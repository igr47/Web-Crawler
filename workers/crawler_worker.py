# workers/crawler_worker.py
from celery import Celery
from datetime import datetime
import logging

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
)

@celery_app.task(name='crawler.crawl_all_sources')
def crawl_all_sources():
    """Task to crawl all news sources"""
    from database.connection import get_db_session
    from crawlers.news_crawler import NewsCrawler
    from crawlers.sentiment_analyzer import SentimentAnalyzer
    from processors.category_classifier import CategoryClassifier
    from database.models import NewsArticle, CrawlHistory
    from config import config
    
    db = get_db_session()
    sentiment_analyzer = SentimentAnalyzer(use_deep_learning=False)
    classifier = CategoryClassifier()
    crawler = NewsCrawler(db, sentiment_analyzer, config)
    
    # Track crawl
    crawl_record = CrawlHistory(
        source="all_rss_feeds",
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
        
        logger.info(f"Crawl completed: {new_count} new articles")
        
        return {
            "status": "success",
            "articles_found": len(articles),
            "new_articles": new_count
        }
        
    except Exception as e:
        logger.error(f"Crawl failed: {e}")
        crawl_record.status = "failed"
        crawl_record.error_message = str(e)
        db.commit()
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

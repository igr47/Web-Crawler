#!/usr/bin/env python
"""Runing initial full crawl to populate database with all sources"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_initial_crawl():
    """Run initial full crawl synchronously"""
    from database.connections import get_db_session
    from crawlers.news_crawler import NewsCrawler
    from crawlers.sentiment_analyzer import SentimentAnalyzer
    from processors.category_classifier import CategoryClassifier
    from database.models import NewsArticle, CrawlHistory
    from config import config
    import json
    
    print("Starting INITIAL FULL CRAWL of all sources...")
    print("This may take several minutes...")
    
    db = get_db_session()
    sentiment_analyzer = SentimentAnalyzer()
    classifier = CategoryClassifier()
    crawler = NewsCrawler(db, sentiment_analyzer, config)
    
    # Track crawl
    crawl_record = CrawlHistory(
        source="initial_full_crawl",
        start_time=datetime.utcnow(),
        status="running"
    )
    db.add(crawl_record)
    db.commit()
    
    try:
        # Crawl ALL RSS feeds
        print(f"Fetching articles from {len(config.RSS_FEEDS)} sources...")
        articles = crawler.crawl_rss_feeds()
        
        print(f"Found {len(articles)} total articles. Processing...")
        
        # Process each article
        new_count = 0
        for idx, article_data in enumerate(articles, 1):
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
            
            if idx % 10 == 0:
                print(f"  Processed {idx}/{len(articles)} articles...")
                db.commit()
        
        db.commit()
        
        # Update crawl record
        crawl_record.end_time = datetime.utcnow()
        crawl_record.articles_found = len(articles)
        crawl_record.articles_new = new_count
        crawl_record.status = "completed"
        db.commit()
        
        print(f"\n✅ INITIAL CRAWL COMPLETED!")
        print(f"   Total articles found: {len(articles)}")
        print(f"   New articles added: {new_count}")
        print(f"   Time taken: {(datetime.utcnow() - crawl_record.start_time).total_seconds():.2f} seconds")
        
        return {
            "status": "success",
            "articles_found": len(articles),
            "new_articles": new_count
        }
        
    except Exception as e:
        print(f"❌ Initial crawl failed: {e}")
        crawl_record.status = "failed"
        crawl_record.error_message = str(e)
        db.commit()
        raise

if __name__ == "__main__":
    run_initial_crawl()

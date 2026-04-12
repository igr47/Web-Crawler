from fastapi import FastAPI, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import json

app = FastAPI(title="News Sentiment API")

# CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
#from database.connection import get_db
from database.models import NewsArticle, CategoryAggregation
from processors.aggregator import SentimentAggregator

class SentimentResponse(BaseModel):
    category: str
    avg_sentiment: float
    total_articles: int
    sentiment_distribution: dict
    timestamp: datetime

class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    source: str
    published_date: datetime
    category: str
    sentiment_score: float
    sentiment_label: str
    url: str

@app.get("/")
async def root():
    return {"message": "News Sentiment Crawler API", "version": "1.0"}

@app.get("/api/sentiment/overview")
async def get_sentiment_overview(timeframe: str = "day"):
    """Get overall sentiment overview"""
    db = next(get_db())
    aggregator = SentimentAggregator(db)
    
    results = aggregator.aggregate_by_category(timeframe)
    
    return {
        "status": "success",
        "data": results,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/sentiment/category/{category}")
async def get_category_sentiment(
    category: str,
    days: int = Query(7, ge=1, le=30)
):
    """Get sentiment for specific category"""
    db = next(get_db())
    aggregator = SentimentAggregator(db)
    
    timeline = aggregator.get_sentiment_timeline(category, days)
    
    return {
        "category": category,
        "timeline": timeline,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/articles/latest")
async def get_latest_articles(
    category: Optional[str] = None,
    limit: int = Query(50, le=200),
    sentiment: Optional[str] = None
):
    """Get latest articles with optional filtering"""
    db = next(get_db())
    
    query = db.query(NewsArticle).filter(NewsArticle.processed == True)
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    if sentiment:
        query = query.filter(NewsArticle.sentiment_label == sentiment)
    
    articles = query.order_by(NewsArticle.published_date.desc()).limit(limit).all()
    
    return {
        "articles": [article.to_dict() for article in articles],
        "count": len(articles)
    }

@app.get("/api/trending")
async def get_trending_topics(limit: int = 10):
    """Get trending topics"""
    db = next(get_db())
    aggregator = SentimentAggregator(db)
    
    trending = aggregator.get_trending_topics(limit)
    
    return {
        "trending": trending,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/markets/sentiment")
async def get_market_sentiment():
    """Get sentiment for market-related categories (like Polymarket)"""
    market_categories = ["Crypto", "Stock Market", "Economy", "Politics"]
    
    db = next(get_db())
    aggregator = SentimentAggregator(db)
    
    sentiment_data = aggregator.aggregate_by_category("day")
    
    market_sentiment = {
        cat: sentiment_data.get(cat, {})
        for cat in market_categories
    }
    
    # Calculate overall market sentiment
    all_scores = []
    for cat in market_categories:
        if cat in sentiment_data:
            all_scores.append(sentiment_data[cat]['avg_sentiment'])
    
    overall_sentiment = sum(all_scores) / len(all_scores) if all_scores else 0
    
    return {
        "market_categories": market_sentiment,
        "overall_market_sentiment": overall_sentiment,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

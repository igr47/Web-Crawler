from itertools import count
from operator import and_
from fastapi import FastAPI, Query, BackgroundTasks, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime, timedelta
import json

from sqlalchemy import True_

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
from database.connections import get_db_session
from database.models import NewsArticle, CategoryAggregation
from processors.aggregator import SentimentAggregator
from api.websocket import manager

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

class WebhookPayload(BaseModel):
    url: HttpUrl
    title: str
    content: Optional[str] = None
    source: str
    published_at: datetime
    category: Optional[str] = None

def get_db():
    """Dependency for FastAPI routes"""
    db = get_db_session()
    try:
        yield db
    finally:
        pass  # Keep session alive for now

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

@app.get("/api/analytics/summary")
async def get_analytics_summary():
    """Get comprehensive analytics summary"""
    db = next(get_db())
    
    from database.models import NewsArticle
    from sqlalchemy import func, and_
    
    # Total articles
    total_articles = db.query(func.count(NewsArticle.id)).scalar()
    
    # Articles by sentiment
    sentiment_counts = db.query(
        NewsArticle.sentiment_label, 
        func.count(NewsArticle.id)
    ).group_by(NewsArticle.sentiment_label).all()
    
    # Articles by category
    category_counts = db.query(
        NewsArticle.category, 
        func.count(NewsArticle.id)
    ).group_by(NewsArticle.category).all()
    
    # Date range
    oldest = db.query(func.min(NewsArticle.published_date)).scalar()
    latest = db.query(func.max(NewsArticle.published_date)).scalar()
    
    # Top sources
    top_sources = db.query(
        NewsArticle.source, 
        func.count(NewsArticle.id)
    ).group_by(NewsArticle.source).order_by(func.count(NewsArticle.id).desc()).limit(10).all()
    
    # Average sentiment by category
    avg_sentiment = db.query(
        NewsArticle.category,
        func.avg(NewsArticle.sentiment_score).label('avg_sentiment'),
        func.count(NewsArticle.id).label('count')
    ).group_by(NewsArticle.category).order_by(func.avg(NewsArticle.sentiment_score).desc()).all()
    
    return {
        "total_articles": total_articles,
        "sentiment_distribution": dict(sentiment_counts),
        "category_distribution": dict(category_counts),
        "date_range": {
            "oldest": oldest.isoformat() if oldest else None,
            "latest": latest.isoformat() if latest else None
        },
        "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
        "average_sentiment_by_category": [
            {"category": c[0], "avg_sentiment": float(c[1]), "article_count": c[2]} 
            for c in avg_sentiment
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/api/analytics/sentiment-trends")
async def get_sentiment_trends(
    category: Optional[str] = None,
    days: int = Query(7, ge=1, le=30)
):
    """Get sentiment trends over time"""
    db = next(get_db())
    from database.models import NewsArticle
    from sqlalchemy import func, cast, Date
    
    # Calculate date range
    start_date = datetime.utcnow() - timedelta(days=days)
    
    query = db.query(
        func.date(NewsArticle.published_date).label('date'),
        func.avg(NewsArticle.sentiment_score).label('avg_sentiment'),
        func.count(NewsArticle.id).label('article_count'),
        func.sum(func.case([(NewsArticle.sentiment_label == 'positive', 1)], else_=0)).label('positive_count'),
        func.sum(func.case([(NewsArticle.sentiment_label == 'negative', 1)], else_=0)).label('negative_count'),
        func.sum(func.case([(NewsArticle.sentiment_label == 'neutral', 1)], else_=0)).label('neutral_count')
    ).filter(
        NewsArticle.published_date >= start_date
    )
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    results = query.group_by(func.date(NewsArticle.published_date)).order_by('date').all()
    
    return {
        "category": category or "All",
        "days": days,
        "trends": [
            {
                "date": str(r.date),
                "avg_sentiment": float(r.avg_sentiment) if r.avg_sentiment else 0,
                "article_count": r.article_count,
                "sentiment_breakdown": {
                    "positive": r.positive_count,
                    "negative": r.negative_count,
                    "neutral": r.neutral_count
                }
            }
            for r in results
        ],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/analytics/top-articles")
async def get_top_articles(
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(10, le=50)
):
    """Get top articles by sentiment score or relevance"""
    db = next(get_db())
    from database.models import NewsArticle
    
    query = db.query(NewsArticle)
    
    if sentiment:
        query = query.filter(NewsArticle.sentiment_label == sentiment)
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    # Get articles with highest absolute sentiment scores
    from sqlalchemy import func
    articles = query.order_by(func.abs(NewsArticle.sentiment_score).desc()).limit(limit).all()
    
    return {
        "articles": [article.to_dict() for article in articles],
        "count": len(articles),
        "filters": {
            "sentiment": sentiment,
            "category": category
        }
    }

@app.get("/api/export/csv")
async def export_articles_csv(
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    limit: int = Query(1000, le=10000)
):
    """Export articles as CSV"""
    db = next(get_db())
    from database.models import NewsArticle
    import csv
    from fastapi.responses import StreamingResponse
    import io
    
    query = db.query(NewsArticle).filter(NewsArticle.processed == True)
    
    if category:
        query = query.filter(NewsArticle.category == category)
    
    if sentiment:
        query = query.filter(NewsArticle.sentiment_label == sentiment)
    
    articles = query.order_by(NewsArticle.published_date.desc()).limit(limit).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        'ID', 'Title', 'Source', 'Category', 'Published Date',
        'Sentiment Score', 'Sentiment Label', 'URL', 'Summary'
    ])
    
    # Write data
    for article in articles:
        writer.writerow([
            article.id,
            article.title,
            article.source,
            article.category,
            article.published_date.isoformat() if article.published_date else '',
            article.sentiment_score,
            article.sentiment_label,
            article.url,
            article.summary[:200] if article.summary else ''
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=news_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
    )

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # Receive subscription requests
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get('action') == 'subscribe':
                    category = message.get('category')
                    if category:
                        await manager.subscribe(websocket, category)
                        await websocket.send_json({
                            "status": "subscribed",
                            "category": category
                        })
            except:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/webhook/news")
async def receive_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    """Receive real-time news updates via webhook"""
    
    # Process in background
    background_tasks.add_task(process_webhook_article, payload)
    
    return {
        "status": "received",
        "message": "Article received and queued for processing",
        "timestamp": datetime.utcnow().isoformat()
    }

async def process_webhook_article(payload: WebhookPayload):
    """Process webhook article asynchronously"""
    from database.connections import get_db_session
    from database.models import NewsArticle
    from crawlers.sentiment_analyzer import SentimentAnalyzer
    from processors.category_classifier import CategoryClassifier
    from api.websocket import manager
    
    db = get_db_session()
    sentiment_analyzer = SentimentAnalyzer()
    classifier = CategoryClassifier()
    
    # Check if article exists
    existing = db.query(NewsArticle).filter(
        NewsArticle.url == str(payload.url)
    ).first()
    
    if existing:
        return
    
    # Analyze sentiment
    sentiment = sentiment_analyzer.analyze_article(
        payload.title,
        payload.content or payload.title
    )
    
    # Classify category
    category, keywords = classifier.classify_article(
        payload.title,
        payload.content or payload.title
    )
    
    # Create article
    article = NewsArticle(
        url=str(payload.url),
        title=payload.title,
        content=payload.content or '',
        summary=payload.content[:500] if payload.content else payload.title,
        source=payload.source,
        published_date=payload.published_at,
        category=category,
        sentiment_score=sentiment['sentiment_score'],
        sentiment_label=sentiment['sentiment_label'],
        confidence_score=sentiment['confidence_score'],
        keywords=json.dumps(keywords),
        processed=True
    )
    
    db.add(article)
    db.commit()
    
    # Broadcast via WebSocket
    await manager.broadcast_new_article(article.to_dict(), category)
    
    logger.info(f"Processed webhook article: {payload.title}")


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

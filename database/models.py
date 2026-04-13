from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

Base = declarative_base()

class NewsArticle(Base):
    __tablename__ = 'news_articles'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, index=True)
    title = Column(String(500))
    content = Column(Text)
    summary = Column(Text)
    
    # Metadata
    source = Column(String(100))
    author = Column(String(200), nullable=True)
    published_date = Column(DateTime, index=True)
    crawled_date = Column(DateTime, default=datetime.utcnow)
    
    # Classification
    category = Column(String(50), index=True)
    sub_category = Column(String(50))
    tags = Column(Text, nullable=True)  # JSON string of tags
    
    # Sentiment analysis
    sentiment_score = Column(Float)  # -1 to 1
    sentiment_label = Column(String(20))  # positive, negative, neutral
    confidence_score = Column(Float, default=0.0)
    
    # Engagement metrics
    shares = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    relevance_score = Column(Float, default=0.5)
    
    # Processing flags
    processed = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    
    # Additional data
    image_url = Column(String(500))
    keywords = Column(Text)  # JSON string
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'category': self.category,
            'sentiment_score': self.sentiment_score,
            'sentiment_label': self.sentiment_label,
            'url': self.url,
            'relevance_score': self.relevance_score
        }

class CategoryAggregation(Base):
    __tablename__ = 'category_aggregations'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(50), index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Aggregated metrics
    avg_sentiment = Column(Float)
    total_articles = Column(Integer)
    positive_count = Column(Integer)
    negative_count = Column(Integer)
    neutral_count = Column(Integer)
    
    # Trending
    sentiment_trend = Column(Float)  
    volume_trend = Column(Float)
    
    # Top articles
    top_articles = Column(Text)  # JSON of article IDs
    
    def to_dict(self):
        return {
            'category': self.category,
            'avg_sentiment': self.avg_sentiment,
            'total_articles': self.total_articles,
            'positive_percentage': (self.positive_count / self.total_articles * 100) if self.total_articles > 0 else 0,
            'negative_percentage': (self.negative_count / self.total_articles * 100) if self.total_articles > 0 else 0,
            'sentiment_trend': self.sentiment_trend,
            'date': self.date.isoformat()
        }

class CrawlHistory(Base):
    __tablename__ = 'crawl_history'
    
    id = Column(Integer, primary_key=True)
    source = Column(String(100))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    articles_found = Column(Integer)
    articles_new = Column(Integer)
    status = Column(String(20))
    error_message = Column(Text)

# Database setup
def init_db(database_url):
    if database_url.startswith('sqlite'):
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            pool_size=10,  
            max_overflow=20
        )
    else:
        engine = create_engine(database_url)

    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

    if USE_SQLITE:
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news_sentiment.db")
    else:
        DATABASE_URL = os.getenv("DATABASE_URL","postresql://user:pass@localhost/news_sentiment")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Crawler settings
    USER_AGENT = "NewsSentimentCrawler/1.0"
    REQUESTS_DELAY = 1 #seconds
    MAX_CONCURRENT_REQUESTS = 5
    REQUEST_TIMEOUT = 30

    # Categories for news aggregation
    CATEGORIES = [
        "Politics", "Economy", "Technology", "Sports",
        "Entertainment", "Health", "Science", "Business",
        "Crypto", "Stock Market", "Real Estate", "Energy"
    ]

    # News sources (RSS feeds)
    RSS_FEEDS = {
        "BBC NEWS": "http://feeds.bbci.co.uk/news/rss.xml",
        "CNN": "http://rss.cnn.com/rss.edition.rss",
        "Reuters": "http://feeds.reuters.com/reuters/topNews",
        "TechCrunch": "http://feeds.feedburner.com/TechCrunch",
        "Wall Street Journal": "http://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "The Gurdian": "https://www.theguardian.com/world/rss",
        "Bloomerg": "http://feeds.bloomberg.com/markets/news.rss"
    }

    # Sentiment threshhold
    SENTIMENT_THRESHOLDS = {
        "very_positive": 0.7,
        "positive": 0.3,
        "neutral": 0.0,
        "negative": -0.3,
        "very_negative": -0.7
    }

config = Config()

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    USE_SQLITE = os.getenv("USE_SQLITE", "true").lower() == "true"

    if USE_SQLITE:
        DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news_sentiment.db")
    else:
        DATABASE_URL = os.getenv("DATABASE_URL","postgresql://user:pass@localhost/news_sentiment")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # Crawler settings
    USER_AGENT = "NewsSentimentCrawler/1.0"
    REQUEST_DELAY = 1 #seconds
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
        #"Wall Street Journal": "http://feeds.a.dj.com/rss/RSSWorldNews.xml",
        "The Guardian": "https://www.theguardian.com/world/rss",
        #"Bloomberg": "http://feeds.bloomberg.com/markets/news.rss",
        "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
        "Associated Press": "http://hosted2.ap.org/atom/APTopnews",
        "NPR": "https://feeds.npr.org/1001/rss.xml",
        "The Independent": "https://www.independent.co.uk/news/uk/rss",
        "Sky News": "https://feeds.skynews.com/feeds/rss/home.xml",
        "CNBC": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "Business Insider": "https://feeds.feedburner.com/businessinsider",

        # UN & International Organizations
        "UN News": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        
        # Public Broadcasters
        "DW News": "https://rss.dw.com/rdf/rss-en-all",
        "France 24": "https://www.france24.com/en/tv-shows/rss",
        "NHK World": "https://www3.nhk.or.jp/nhkworld/upd/rss/en/",
        "Global Voices": "https://globalvoices.org/feed/",
        "ABC Australia": "https://www.abc.net.au/news/feed/51120/rss.xml",
        #"CBC News": "https://www.cbc.ca/rss/",
        "PBS News": "https://www.pbs.org/newshour/feeds/rss/headlines",
        
        # Technology & Science
        #"The Verge": "https://www.theverge.com/rss/index.xml",
        "Ars Technica": "https://arstechnica.com/feed/",
        "Engadget": "https://www.engadget.com/rss.xml",
        "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "arXiv AI": "http://export.arxiv.org/rss/cs.AI",
        "Wired": "https://www.wired.com/feed/rss",
        "MIT Technology Review": "https://www.technologyreview.com/feed/",
        "Science Daily": "https://www.sciencedaily.com/rss/all.xml",
        "Nature": "https://www.nature.com/nature.rss",
        
        # Regional & Specialized News
        "The Hill": "https://thehill.com/feed/",
        "HuffPost": "https://www.huffpost.com/section/front-page/feed",
        "USA TODAY": "https://rssfeeds.usatoday.com/usatoday-NewsTopStories",
        
        # Financial & Business News
        "Yahoo Finance": "https://finance.yahoo.com/news/rssindex",
        "MarketWatch": "https://www.marketwatch.com/rss/topstories",
        "Investopedia": "https://www.investopedia.com/rss.xml",
        "Seeking Alpha": "https://seekingalpha.com/feed.xml",
        "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "CoinTelegraph": "https://cointelegraph.com/rss",
        
        # Additional Quality Sources
        "Axios": "https://www.axios.com/feeds/feed.rss",
        "Vox": "https://www.vox.com/rss/index.xml",
        "Quartz": "https://qz.com/feed",
        "The Conversation": "https://theconversation.com/us/articles.atom",
        "VICE News": "https://www.vice.com/en/rss",
        "Mother Jones": "https://www.motherjones.com/feed/",
        "ProPublica": "https://www.propublica.org/feeds/propublica/main",

        "Standard (Main Headlines)": "https://www.standardmedia.co.ke/rss/headlines.php",
        "Standard (Kenya News)": "https://www.standardmedia.co.ke/rss/kenya.php",
        "Standard (World News)": "https://www.standardmedia.co.ke/rss/world.php",
        "Standard (Politics)": "https://www.standardmedia.co.ke/rss/politics.php",
        "Standard (Business)": "https://www.standardmedia.co.ke/rss/business.php",

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

import requests
from bs4 import BeautifulSoup
from newspaper import Article
import feedparser
from datetime import datetime, timedelta
import time
import hashlib
from typing import List, Dict
from urllib.parse import urlparse
import logging

from processors.sentiment_refiner import SentimentRefiner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsCrawler:
    def __init__(self, db_session, sentiment_analyzer, config):
        self.db = db_session
        self.sentiment_analyzer = sentiment_analyzer
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': config.USER_AGENT})
    
    def crawl_rss_feeds(self) -> List[Dict]:
        """Crawl RSS feeds for news articles"""
        articles = []
        
        for source, feed_url in self.config.RSS_FEEDS.items():
            try:
                logger.info(f"Crawling RSS feed: {source}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:20]:  # Limit per feed
                    article = self.process_rss_entry(entry, source)
                    if article and self.is_article_new(article['url']):
                        articles.append(article)
                
                time.sleep(self.config.REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error crawling {source}: {e}")
                continue
        
        logger.info(f"Found {len(articles)} new articles from RSS feeds")
        return articles
    
    def process_rss_entry(self, entry, source: str) -> Dict:
        """Process a single RSS entry"""
        try:
            # Extract basic info
            url = entry.get('link', '')
            if not url:
                return None
            
            title = entry.get('title', '')
            published = entry.get('published_parsed')
            published_date = datetime(*published[:6]) if published else datetime.utcnow()
            
            # Use newspaper3k to extract full article
            article_data = self.extract_article_content(url)
            
            if not article_data:
                return None
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_article(
                title, 
                article_data['content']
            )

            refiner = SentimentRefiner()
            sentiment = refiner.refine_sentiment(
                title,
                article_data['content'],
                sentiment
            )
            
            return {
                'url': url,
                'title': title,
                'content': article_data['content'],
                'summary': article_data['summary'],
                'source': source,
                'published_date': published_date,
                'image_url': article_data.get('image_url'),
                'sentiment_score': sentiment['sentiment_score'],
                'sentiment_label': sentiment['sentiment_label'],
                'confidence_score': sentiment['confidence_score'],
                'keywords': article_data.get('keywords', [])
            }
            
        except Exception as e:
            logger.error(f"Error processing entry: {e}")
            return None
    
    def extract_article_content(self, url: str) -> Dict:
        """Extract article content using newspaper3k"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            article.nlp()
            
            return {
                'content': article.text[:5000],  # Limit length
                'summary': article.summary[:500],
                'image_url': article.top_image,
                'keywords': article.keywords[:10]
            }
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def crawl_news_api(self, query: str, from_date: datetime = None) -> List[Dict]:
        """Crawl news from NewsAPI (requires API key)"""
        # This is optional - you'd need a NewsAPI key
        api_key = os.getenv('NEWS_API_KEY')
        if not api_key:
            return []
        
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': query,
            'apiKey': api_key,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100
        }
        
        if from_date:
            params['from'] = from_date.isoformat()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            data = response.json()
            
            articles = []
            for article_data in data.get('articles', []):
                sentiment = self.sentiment_analyzer.analyze_article(
                    article_data['title'],
                    article_data['description'] or ''
                )
                
                articles.append({
                    'url': article_data['url'],
                    'title': article_data['title'],
                    'content': article_data['description'] or article_data['content'] or '',
                    'summary': article_data['description'] or '',
                    'source': article_data['source']['name'],
                    'published_date': datetime.fromisoformat(article_data['publishedAt'].replace('Z', '+00:00')),
                    'image_url': article_data['urlToImage'],
                    'sentiment_score': sentiment['sentiment_score'],
                    'sentiment_label': sentiment['sentiment_label'],
                    'confidence_score': sentiment['confidence_score'],
                    'keywords': []
                })
            
            return articles
            
        except Exception as e:
            logger.error(f"Error calling NewsAPI: {e}")
            return []
    
    def is_article_new(self, url: str) -> bool:
        """Check if article already exists in database"""
        from database.models import NewsArticle
        existing = self.db.query(NewsArticle).filter(NewsArticle.url == url).first()
        return existing is None

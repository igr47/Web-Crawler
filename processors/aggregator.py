# processors/aggregator.py
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import defaultdict
import json

class SentimentAggregator:
    def __init__(self, db_session):
        self.db = db_session
    
    def aggregate_by_category(self, time_period: str = 'day') -> dict:
        """Aggregate sentiment by category for given time period"""
        from database.models import NewsArticle, CategoryAggregation
        
        # Determine time window
        if time_period == 'hour':
            since = datetime.utcnow() - timedelta(hours=1)
        elif time_period == 'day':
            since = datetime.utcnow() - timedelta(days=1)
        elif time_period == 'week':
            since = datetime.utcnow() - timedelta(days=7)
        else:
            since = datetime.utcnow() - timedelta(days=30)
        
        # Query articles
        articles = self.db.query(NewsArticle).filter(
            NewsArticle.published_date >= since,
            NewsArticle.processed == True
        ).all()
        
        # Group by category
        category_data = defaultdict(lambda: {
            'scores': [],
            'positive': 0,
            'negative': 0,
            'neutral': 0,
            'articles': []
        })
        
        for article in articles:
            category = article.category
            data = category_data[category]
            
            data['scores'].append(article.sentiment_score)
            data['articles'].append(article.id)
            
            if article.sentiment_label == 'positive':
                data['positive'] += 1
            elif article.sentiment_label == 'negative':
                data['negative'] += 1
            else:
                data['neutral'] += 1
        
        # Calculate aggregates
        results = {}
        for category, data in category_data.items():
            if data['scores']:
                avg_sentiment = sum(data['scores']) / len(data['scores'])
                
                results[category] = {
                    'avg_sentiment': avg_sentiment,
                    'total_articles': len(data['scores']),
                    'positive_count': data['positive'],
                    'negative_count': data['negative'],
                    'neutral_count': data['neutral'],
                    'sentiment_distribution': {
                        'positive': (data['positive'] / len(data['scores'])) * 100,
                        'negative': (data['negative'] / len(data['scores'])) * 100,
                        'neutral': (data['neutral'] / len(data['scores'])) * 100
                    }
                }
        
        return results
    
    def get_trending_topics(self, limit: int = 10) -> list:
        """Extract trending topics based on recent articles"""
        from database.models import NewsArticle
        
        # Get last 24 hours of articles
        since = datetime.utcnow() - timedelta(hours=24)
        articles = self.db.query(NewsArticle).filter(
            NewsArticle.published_date >= since
        ).all()
        
        # Extract keywords
        all_keywords = []
        for article in articles:
            if article.keywords:
                keywords = json.loads(article.keywords)
                all_keywords.extend(keywords)
        
        # Count frequency
        from collections import Counter
        keyword_counts = Counter(all_keywords)
        
        trending = [
            {'topic': keyword, 'mentions': count}
            for keyword, count in keyword_counts.most_common(limit)
        ]
        
        return trending
    
    def get_sentiment_timeline(self, category: str = None, days: int = 7) -> list:
        """Get sentiment timeline for a category"""
        from database.models import NewsArticle
        
        timeline = []
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())
            
            query = self.db.query(NewsArticle).filter(
                NewsArticle.published_date.between(start, end),
                NewsArticle.processed == True
            )
            
            if category:
                query = query.filter(NewsArticle.category == category)
            
            articles = query.all()
            
            if articles:
                avg_sentiment = sum(a.sentiment_score for a in articles) / len(articles)
                timeline.append({
                    'date': date.isoformat(),
                    'avg_sentiment': avg_sentiment,
                    'article_count': len(articles)
                })
        
        return timeline

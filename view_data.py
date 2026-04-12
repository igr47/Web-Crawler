#!/usr/bin/env python
"""View and analyze crawled news data"""

import sys
import json
from datetime import datetime, timedelta
from database.connections import get_db_session
from database.models import NewsArticle
from sqlalchemy import func, desc
from tabulate import tabulate

class DataViewer:
    def __init__(self):
        self.db = get_db_session()
    
    def show_summary(self):
        """Show overall statistics"""
        print("\n" + "="*60)
        print("📊 NEWS DATABASE SUMMARY")
        print("="*60)
        
        total = self.db.query(func.count(NewsArticle.id)).scalar()
        print(f"📰 Total Articles: {total}")
        
        # Date range
        oldest = self.db.query(func.min(NewsArticle.published_date)).scalar()
        latest = self.db.query(func.max(NewsArticle.published_date)).scalar()
        print(f"📅 Date Range: {oldest.date()} to {latest.date()}")
        
        # Sentiment distribution
        print("\n📈 SENTIMENT DISTRIBUTION:")
        sentiment_stats = self.db.query(
            NewsArticle.sentiment_label,
            func.count(NewsArticle.id),
            func.avg(NewsArticle.sentiment_score)
        ).group_by(NewsArticle.sentiment_label).all()
        
        for label, count, avg_score in sentiment_stats:
            emoji = "😊" if label == "positive" else "😞" if label == "negative" else "😐"
            print(f"  {emoji} {label.capitalize()}: {count} articles (avg score: {avg_score:.2f})")
        
        # Category breakdown
        print("\n🏷️  TOP CATEGORIES:")
        category_stats = self.db.query(
            NewsArticle.category,
            func.count(NewsArticle.id),
            func.avg(NewsArticle.sentiment_score)
        ).group_by(NewsArticle.category).order_by(func.count(NewsArticle.id).desc()).limit(10).all()
        
        for category, count, avg_score in category_stats:
            print(f"  📌 {category}: {count} articles (avg sentiment: {avg_score:.2f})")
        
        # Top sources
        print("\n📰 TOP SOURCES:")
        source_stats = self.db.query(
            NewsArticle.source,
            func.count(NewsArticle.id)
        ).group_by(NewsArticle.source).order_by(func.count(NewsArticle.id).desc()).limit(5).all()
        
        for source, count in source_stats:
            print(f"  • {source}: {count} articles")
    
    def show_recent_articles(self, limit=20):
        """Show most recent articles"""
        print("\n" + "="*60)
        print(f"📰 RECENT ARTICLES (Last {limit})")
        print("="*60)
        
        articles = self.db.query(NewsArticle).order_by(
            NewsArticle.published_date.desc()
        ).limit(limit).all()
        
        table_data = []
        for article in articles:
            sentiment_emoji = "😊" if article.sentiment_label == "positive" else "😞" if article.sentiment_label == "negative" else "😐"
            table_data.append([
                article.id,
                article.title[:50] + "..." if len(article.title) > 50 else article.title,
                article.category,
                f"{sentiment_emoji} {article.sentiment_label}",
                f"{article.sentiment_score:.2f}",
                article.published_date.strftime("%Y-%m-%d")
            ])
        
        print(tabulate(table_data, headers=["ID", "Title", "Category", "Sentiment", "Score", "Date"], tablefmt="grid"))
    
    def show_by_category(self, category=None):
        """Show articles grouped by category"""
        if category:
            articles = self.db.query(NewsArticle).filter(
                NewsArticle.category == category
            ).order_by(NewsArticle.published_date.desc()).all()
            
            print(f"\n📂 CATEGORY: {category} ({len(articles)} articles)")
            print("="*60)
            
            for article in articles[:20]:
                print(f"\n📰 {article.title}")
                print(f"   📅 {article.published_date.strftime('%Y-%m-%d')} | 🏷️ {article.sentiment_label} ({article.sentiment_score:.2f})")
                print(f"   🔗 {article.url}")
                if article.summary:
                    print(f"   📝 {article.summary[:150]}...")
        else:
            # Show all categories
            categories = self.db.query(
                NewsArticle.category,
                func.count(NewsArticle.id)
            ).group_by(NewsArticle.category).order_by(NewsArticle.category).all()
            
            print("\n📂 ALL CATEGORIES")
            print("="*60)
            for cat_name, count in categories:
                print(f"  • {cat_name}: {count} articles")
    
    def show_most_positive(self, limit=10):
        """Show most positive articles"""
        articles = self.db.query(NewsArticle).filter(
            NewsArticle.sentiment_label == 'positive'
        ).order_by(NewsArticle.sentiment_score.desc()).limit(limit).all()
        
        print(f"\n😊 MOST POSITIVE ARTICLES (Top {limit})")
        print("="*60)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Score: {article.sentiment_score:.2f} | Category: {article.category}")
            print(f"   {article.url}")
    
    def show_most_negative(self, limit=10):
        """Show most negative articles"""
        articles = self.db.query(NewsArticle).filter(
            NewsArticle.sentiment_label == 'negative'
        ).order_by(NewsArticle.sentiment_score.asc()).limit(limit).all()
        
        print(f"\n😞 MOST NEGATIVE ARTICLES (Top {limit})")
        print("="*60)
        
        for i, article in enumerate(articles, 1):
            print(f"\n{i}. {article.title}")
            print(f"   Score: {article.sentiment_score:.2f} | Category: {article.category}")
            print(f"   {article.url}")
    
    def search_articles(self, keyword):
        """Search articles by keyword in title or content"""
        articles = self.db.query(NewsArticle).filter(
            (NewsArticle.title.contains(keyword)) | 
            (NewsArticle.content.contains(keyword))
        ).limit(50).all()
        
        print(f"\n🔍 SEARCH RESULTS FOR: '{keyword}'")
        print(f"Found {len(articles)} articles")
        print("="*60)
        
        for article in articles:
            print(f"\n📰 {article.title}")
            print(f"   Sentiment: {article.sentiment_label} ({article.sentiment_score:.2f}) | Category: {article.category}")
            print(f"   Published: {article.published_date.strftime('%Y-%m-%d')}")
            print(f"   🔗 {article.url}")
    
    def show_daily_summary(self, days=7):
        """Show daily summary for last N days"""
        print(f"\n📊 DAILY SUMMARY (Last {days} days)")
        print("="*60)
        
        for i in range(days):
            date = datetime.utcnow().date() - timedelta(days=i)
            start = datetime.combine(date, datetime.min.time())
            end = datetime.combine(date, datetime.max.time())
            
            articles = self.db.query(NewsArticle).filter(
                NewsArticle.published_date.between(start, end)
            ).all()
            
            if articles:
                avg_sentiment = sum(a.sentiment_score for a in articles) / len(articles)
                positive = sum(1 for a in articles if a.sentiment_label == 'positive')
                negative = sum(1 for a in articles if a.sentiment_label == 'negative')
                neutral = sum(1 for a in articles if a.sentiment_label == 'neutral')
                
                print(f"\n📅 {date}:")
                print(f"   Articles: {len(articles)} | Avg Sentiment: {avg_sentiment:.2f}")
                print(f"   😊 Positive: {positive} | 😞 Negative: {negative} | 😐 Neutral: {neutral}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="View news crawler data")
    parser.add_argument("--command", choices=["summary", "recent", "categories", "positive", "negative", "search", "daily"], 
                       default="summary", help="Command to execute")
    parser.add_argument("--category", type=str, help="Category name")
    parser.add_argument("--keyword", type=str, help="Search keyword")
    parser.add_argument("--limit", type=int, default=20, help="Number of items to show")
    parser.add_argument("--days", type=int, default=7, help="Number of days for daily summary")
    
    args = parser.parse_args()
    
    viewer = DataViewer()
    
    if args.command == "summary":
        viewer.show_summary()
    elif args.command == "recent":
        viewer.show_recent_articles(args.limit)
    elif args.command == "categories":
        viewer.show_by_category(args.category)
    elif args.command == "positive":
        viewer.show_most_positive(args.limit)
    elif args.command == "negative":
        viewer.show_most_negative(args.limit)
    elif args.command == "search":
        if not args.keyword:
            print("Please provide --keyword for search")
            sys.exit(1)
        viewer.search_articles(args.keyword)
    elif args.command == "daily":
        viewer.show_daily_summary(args.days)

if __name__ == "__main__":
    main()

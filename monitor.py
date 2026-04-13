#!/usr/bin/env python
"""Simple working news monitor"""

import sqlite3
import os
from datetime import datetime, timedelta
import time
import sys

DB_PATH = "news_sentiment.db"

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def get_db_connection():
    """Get database connection"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found!")
        print("Please run: python main.py --setup")
        return None
    
    return sqlite3.connect(DB_PATH)

def get_latest_articles(limit=15):
    """Fetch latest articles directly from database"""
    conn = get_db_connection()
    if not conn:
        return []
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, source, category, sentiment_label, sentiment_score, 
               published_date, url, summary
        FROM news_articles 
        WHERE processed = 1
        ORDER BY published_date DESC 
        LIMIT ?
    """, (limit,))
    
    articles = []
    for row in cursor.fetchall():
        articles.append({
            'id': row[0],
            'title': row[1],
            'source': row[2],
            'category': row[3],
            'sentiment_label': row[4],
            'sentiment_score': row[5],
            'published_date': row[6],
            'url': row[7],
            'summary': row[8]
        })
    
    conn.close()
    return articles

def get_sentiment_stats():
    """Get sentiment statistics"""
    conn = get_db_connection()
    if not conn:
        return {}
    
    cursor = conn.cursor()
    
    # Total articles
    cursor.execute("SELECT COUNT(*) FROM news_articles WHERE processed = 1")
    total = cursor.fetchone()[0]
    
    # Sentiment distribution
    cursor.execute("""
        SELECT sentiment_label, COUNT(*) 
        FROM news_articles 
        WHERE processed = 1 
        GROUP BY sentiment_label
    """)
    sentiment_counts = dict(cursor.fetchall())
    
    # Category stats
    cursor.execute("""
        SELECT category, COUNT(*), AVG(sentiment_score)
        FROM news_articles 
        WHERE processed = 1 
        GROUP BY category 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    category_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'sentiment': sentiment_counts,
        'categories': category_stats
    }

def display_articles(articles):
    """Display articles in formatted way"""
    if not articles:
        print("\n❌ No articles found in database!")
        print("\nPlease run the crawler first:")
        print("  python run_crawler.py")
        return
    
    print("\n" + "="*100)
    print(f"📰 LATEST NEWS ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    print("="*100)
    
    for i, article in enumerate(articles[:10], 1):
        sentiment_emoji = "😊" if article['sentiment_label'] == 'positive' else "😞" if article['sentiment_label'] == 'negative' else "😐"
        
        # Format date
        pub_date = article['published_date']
        if isinstance(pub_date, str):
            pub_date = pub_date[:10]
        else:
            pub_date = pub_date.strftime('%Y-%m-%d') if pub_date else 'Unknown'
        
        print(f"\n{i}. {article['title'][:80]}")
        print(f"   📅 {pub_date} | 🏷️ {article['category']} | 📰 {article['source']}")
        print(f"   {sentiment_emoji} Sentiment: {article['sentiment_label']} ({article['sentiment_score']:.2f})")
        if article.get('summary'):
            summary = article['summary'][:120] if article['summary'] else ''
            if summary:
                print(f"   📝 {summary}...")
        print(f"   🔗 {article['url'][:80]}...")

def display_stats(stats):
    """Display statistics"""
    if not stats or stats.get('total', 0) == 0:
        print("\n📊 No data available yet")
        return
    
    print("\n" + "="*100)
    print("📊 DATABASE STATISTICS")
    print("="*100)
    
    print(f"\n📰 Total Articles: {stats['total']}")
    
    # Sentiment distribution
    print("\n📈 Sentiment Distribution:")
    sentiment = stats.get('sentiment', {})
    pos_count = sentiment.get('positive', 0)
    neg_count = sentiment.get('negative', 0)
    neu_count = sentiment.get('neutral', 0)
    
    if stats['total'] > 0:
        pos_pct = (pos_count / stats['total']) * 100
        neg_pct = (neg_count / stats['total']) * 100
        neu_pct = (neu_count / stats['total']) * 100
        print(f"   😊 Positive: {pos_count} ({pos_pct:.1f}%)")
        print(f"   😞 Negative: {neg_count} ({neg_pct:.1f}%)")
        print(f"   😐 Neutral: {neu_count} ({neu_pct:.1f}%)")
    
    # Top categories
    print("\n🏷️ Top Categories:")
    for cat in stats.get('categories', [])[:5]:
        cat_name, count, avg_sent = cat
        print(f"   • {cat_name}: {count} articles (avg sentiment: {avg_sent:.2f})")

def monitor_loop(refresh_interval=10):
    """Main monitoring loop"""
    print("🔍 News Monitor Started")
    print(f"📁 Database: {DB_PATH}")
    print(f"⏱️  Refreshing every {refresh_interval} seconds")
    print("Press Ctrl+C to stop\n")
    
    # Track seen article IDs
    seen_ids = set()
    
    try:
        while True:
            # Fetch data
            articles = get_latest_articles(20)
            stats = get_sentiment_stats()
            
            # Check for new articles
            new_articles = [a for a in articles if a['id'] not in seen_ids]
            for article in new_articles:
                seen_ids.add(article['id'])
            
            # Show alert for new articles
            if new_articles:
                print(f"\n🔔 {len(new_articles)} NEW ARTICLE(S) DETECTED!")
                for article in new_articles[:3]:
                    emoji = "😊" if article['sentiment_label'] == 'positive' else "😞" if article['sentiment_label'] == 'negative' else "😐"
                    print(f"   {emoji} {article['title'][:60]}...")
            
            # Clear and display
            clear_screen()
            display_stats(stats)
            display_articles(articles)
            
            print("\n" + "-"*100)
            print(f"🔄 Next update in {refresh_interval} seconds... (Press Ctrl+C to exit)")
            
            time.sleep(refresh_interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

def check_database():
    """Check if database exists and has data"""
    if not os.path.exists(DB_PATH):
        print(f"❌ Database {DB_PATH} not found!")
        print("\nPlease set up the database first:")
        print("  python main.py --setup")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='news_articles'
    """)
    
    if not cursor.fetchone():
        print("❌ Table 'news_articles' not found!")
        print("\nPlease run setup to create tables:")
        print("  python main.py --setup")
        conn.close()
        return False
    
    # Check if there's data
    cursor.execute("SELECT COUNT(*) FROM news_articles")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("⚠️ Database exists but no articles found!")
        print("\nPlease run the crawler to fetch articles:")
        print("  python run_crawler.py")
    else:
        print(f"✅ Database found with {count} articles")
    
    conn.close()
    return True

if __name__ == "__main__":
    # Check if we should just show stats once
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        stats = get_sentiment_stats()
        articles = get_latest_articles(10)
        display_stats(stats)
        display_articles(articles)
    else:
        # Check database first
        if check_database():
            monitor_loop()
        else:
            sys.exit(1)

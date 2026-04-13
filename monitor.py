#!/usr/bin/env python
"""Monitor real-time news feed"""

import asyncio
import websockets
import json
from datetime import datetime

async def monitor_news():
    """Connect to WebSocket and monitor news in real-time"""
    uri = "ws://localhost:8000/ws/client1"
    
    async with websockets.connect(uri) as websocket:
        # Subscribe to category
        await websocket.send(json.dumps({
            "action": "subscribe",
            "category": "Technology"
        }))
        
        print("Connected to news feed. Monitoring for new articles...")
        print("-" * 60)
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                
                if data['type'] == 'new_article':
                    article = data['article']
                    print(f"\n📰 NEW ARTICLE DETECTED!")
                    print(f"   Title: {article['title']}")
                    print(f"   Category: {article['category']}")
                    print(f"   Sentiment: {article['sentiment_label']} ({article['sentiment_score']:.2f})")
                    print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
                    print(f"   URL: {article['url']}")
                    print("-" * 60)
                    
            except websockets.exceptions.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(monitor_news())

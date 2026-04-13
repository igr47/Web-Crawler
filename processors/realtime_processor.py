"""Real-time article processing with streaming"""

import asyncio
from datetime import datetime
from typing import List, Dict
import redis
import json
import logging

logger = logging.getLogger(__name__)

class RealtimeArticleProcessor:
    """Process articles as they come in real-time"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis(
            host='localhost', 
            port=6379, 
            decode_responses=True
        )
        self.stream_key = 'news_stream'
        self.consumer_group = 'news_processors'
    
    def setup_stream(self):
        """Setup Redis stream for real-time processing"""
        try:
            # Create consumer group if it doesn't exist
            self.redis.xgroup_create(
                self.stream_key, 
                self.consumer_group, 
                id='0', 
                mkstream=True
            )
        except redis.exceptions.ResponseError:
            # Group already exists
            pass
    
    def publish_article(self, article: Dict):
        """Publish article to stream for processing"""
        article_id = self.redis.xadd(
            self.stream_key,
            {
                'article_id': str(article.get('id')),
                'title': article.get('title', ''),
                'content': article.get('content', ''),
                'url': article.get('url', ''),
                'source': article.get('source', ''),
                'published_at': article.get('published_date', datetime.utcnow().isoformat())
            }
        )
        logger.info(f"Published article {article.get('id')} to stream")
        return article_id
    
    def process_stream(self, callback):
        """Process stream continuously"""
        self.setup_stream()
        
        while True:
            try:
                # Read from stream
                messages = self.redis.xreadgroup(
                    self.consumer_group,
                    f'consumer_{datetime.utcnow().timestamp()}',
                    {self.stream_key: '>'},
                    count=10,
                    block=1000  # Block for 1 second
                )
                
                for stream, message_list in messages:
                    for message_id, data in message_list:
                        # Process the message
                        callback(data)
                        
                        # Acknowledge the message
                        self.redis.xack(self.stream_key, self.consumer_group, message_id)
                        
            except Exception as e:
                logger.error(f"Error processing stream: {e}")
                asyncio.sleep(1)

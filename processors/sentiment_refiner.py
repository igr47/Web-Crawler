import re
from typing import Dict, List

class SentimentRefiner:
    """
    Post-processes sentiment results to catch edge cases and improve accuracy.
    """
    
    def __init__(self):
        # Strong negative indicators (guarantee negative sentiment)
        self.strong_negative_patterns = [
            (r'\b(?:death|dead|died|dying)\b', -0.8),
            (r'\b(?:kill|killed|killing|murder|murdered)\b', -0.9),
            (r'\b(?:massacre|genocide|slaughter)\b', -1.0),
            (r'\b(?:casualty|casualties|fatal|fatalities)\b', -0.7),
            (r'\b(?:disaster|catastrophe|tragedy)\b', -0.8),
            (r'\b(?:attack|attacked|bombing|explosion)\b', -0.6),
            (r'\b(?:blockade|sanctions|crisis)\b', -0.5),
            (r'\b(?:plunged|plummeted|crashed|collapsed)\b', -0.7),
        ]
        
        # Strong positive indicators
        self.strong_positive_patterns = [
            (r'\b(?:surged|soared|rocketed|skyrocketed)\b', 0.8),
            (r'\b(?:record|all-time high|milestone)\b', 0.7),
            (r'\b(?:breakthrough|revolutionary|game-changing)\b', 0.8),
            (r'\b(?:victory|win|success|triumph)\b', 0.6),
        ]
        
        # Negation patterns that flip sentiment
        self.negation_patterns = [
            r'\b(?:not|no|never|without)\s+\w+\s+(?:good|positive|happy|successful)',
            r'\b(?:failed? to|unable to)\s+\w+',
        ]
    
    def refine_sentiment(self, title: str, content: str, current_result: Dict) -> Dict:
        """
        Refine sentiment analysis by checking for strong indicators.
        """
        text = f"{title} {content[:2000]}".lower()
        
        # Check for strong negative patterns
        max_negative_boost = 0
        for pattern, score in self.strong_negative_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                max_negative_boost = min(max_negative_boost, score)
        
        # Check for strong positive patterns
        max_positive_boost = 0
        for pattern, score in self.strong_positive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                max_positive_boost = max(max_positive_boost, score)
        
        # Apply boosts if they override current sentiment
        refined_score = current_result['sentiment_score']
        refined_label = current_result['sentiment_label']
        
        if max_negative_boost < -0.5:
            # Strong negative indicator found
            refined_score = min(refined_score, max_negative_boost)
            refined_label = 'negative'
            current_result['confidence_score'] = min(1.0, current_result['confidence_score'] + 0.2)
        elif max_positive_boost > 0.5:
            # Strong positive indicator found
            refined_score = max(refined_score, max_positive_boost)
            refined_label = 'positive'
            current_result['confidence_score'] = min(1.0, current_result['confidence_score'] + 0.2)
        
        # Check for death/violence specifically
        death_pattern = r'\b(?:death|dead|died|dying|kill|killed|murder)\b'
        if re.search(death_pattern, text, re.IGNORECASE):
            refined_score = min(refined_score, -0.6)
            refined_label = 'negative'
            current_result['confidence_score'] = min(1.0, current_result['confidence_score'] + 0.3)
        
        current_result['sentiment_score'] = round(refined_score, 3)
        current_result['sentiment_label'] = refined_label
        
        return current_result

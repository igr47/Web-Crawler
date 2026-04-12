import re
from typing import Tuple, List, Dict
from collections import Counter
import math

class SentimentAnalyzer:
    """
    Lightweight sentiment analyzer using lexicon-based approach.
    No AI models, no large downloads, just simple word scoring.
    """
    
    def __init__(self):
        # Positive and negative word lists
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 
            'brilliant', 'awesome', 'incredible', 'outstanding', 'perfect',
            'positive', 'strong', 'growth', 'profit', 'gain', 'up', 'rise',
            'increasing', 'success', 'successful', 'win', 'winning', 'victory',
            'happy', 'pleased', 'satisfied', 'impressed', 'proud', 'optimistic',
            'bullish', 'rally', 'surge', 'boom', 'opportunity', 'advantage',
            'benefit', 'improvement', 'better', 'best', 'leading', 'top',
            'breakthrough', 'innovation', 'award', 'celebrate', 'hope'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'disaster', 'catastrophic',
            'negative', 'weak', 'loss', 'decline', 'down', 'fall', 'decrease',
            'dropping', 'failure', 'fail', 'losing', 'defeat', 'crisis',
            'angry', 'upset', 'disappointed', 'concerned', 'pessimistic',
            'bearish', 'crash', 'plunge', 'slump', 'risk', 'threat',
            'damage', 'problem', 'issue', 'cancer', 'death', 'dead',
            'worst', 'poor', 'low', 'against', 'attack', 'war', 'conflict'
        }
        
        # Intensifiers (amplify sentiment)
        self.intensifiers = {
            'very', 'extremely', 'incredibly', 'absolutely', 'really',
            'highly', 'particularly', 'exceptionally', 'remarkably'
        }
        
        # Negations (flip sentiment)
        self.negations = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
            'hardly', 'scarcely', 'barely', "isn't", "aren't", "wasn't",
            "weren't", "hasn't", "haven't", "hadn't", "won't", "wouldn't",
            "don't", "doesn't", "didn't", "cannot", "can't", "couldn't",
            "shouldn't", "isnt", "arent", "wasnt", "werent", "hasnt"
        }
        
        # Domain-specific financial/news terms
        self.financial_positive = {
            'surged', 'soared', 'jumped', 'climbed', 'rose', 'gained',
            'upgraded', 'outperform', 'buy', 'overweight', 'bull',
            'dividend', 'profit', 'revenue', 'earnings', 'beat'
        }
        
        self.financial_negative = {
            'plunged', 'tumbled', 'slumped', 'dropped', 'fell', 'lost',
            'downgraded', 'underperform', 'sell', 'underweight', 'bear',
            'loss', 'debt', 'bankrupt', 'lawsuit', 'investigation'
        }
        
        # Combine all word lists
        self.positive_words.update(self.financial_positive)
        self.negative_words.update(self.financial_negative)
        
        # Compile regex for word boundary matching
        self.word_pattern = re.compile(r'\b[a-z]+\b')
    
    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Convert text to lowercase words, remove punctuation"""
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split into words
        words = self.word_pattern.findall(text)
        return words
    
    def _calculate_sentiment_score(self, words: List[str]) -> Tuple[float, int, int]:
        """
        Calculate sentiment score based on word occurrences.
        Returns (score, positive_count, negative_count)
        """
        positive_count = 0
        negative_count = 0
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check for negation (affects current and next word)
            negated = False
            if word in self.negations:
                negated = True
                i += 1
                if i >= len(words):
                    break
                word = words[i]
            
            # Check for intensifier
            intensifier = 1.0
            if word in self.intensifiers:
                intensifier = 1.5
                i += 1
                if i >= len(words):
                    break
                word = words[i]
            
            # Score the word
            if word in self.positive_words:
                if negated:
                    negative_count += 1 * intensifier
                else:
                    positive_count += 1 * intensifier
            elif word in self.negative_words:
                if negated:
                    positive_count += 1 * intensifier
                else:
                    negative_count += 1 * intensifier
            
            i += 1
        
        # Calculate net score normalized to -1 to 1 range
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
        else:
            score = (positive_count - negative_count) / total
        
        # Clamp to [-1, 1]
        score = max(-1.0, min(1.0, score))
        
        return score, positive_count, negative_count
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of any text.
        Returns dict with score, label, confidence, and counts.
        """
        if not text or len(text.strip()) < 10:
            return {
                'sentiment_score': 0.0,
                'sentiment_label': 'neutral',
                'confidence_score': 0.0,
                'positive_word_count': 0,
                'negative_word_count': 0
            }
        
        words = self._tokenize_and_clean(text)
        score, pos_count, neg_count = self._calculate_sentiment_score(words)
        
        # Determine label
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Calculate confidence based on word count and score extremity
        total_words = len(words)
        word_confidence = min(1.0, total_words / 100)  # More words = more confidence
        extremity_confidence = abs(score)  # Extreme scores = more confident
        confidence = (word_confidence + extremity_confidence) / 2
        
        # Extract key positive/negative words for context
        positive_found = [w for w in words if w in self.positive_words][:5]
        negative_found = [w for w in words if w in self.negative_words][:5]
        
        return {
            'sentiment_score': score,
            'sentiment_label': label,
            'confidence_score': confidence,
            'positive_word_count': pos_count,
            'negative_word_count': neg_count,
            'key_positive_words': positive_found,
            'key_negative_words': negative_found
        }
    
    def analyze_article(self, title: str, content: str) -> Dict:
        """
        Analyze sentiment of a news article.
        Title is weighted more heavily than content.
        """
        # Weight title more (3x importance)
        title_result = self.analyze_text(title)
        content_result = self.analyze_text(content[:2000])  # Limit content length
        
        # Combine scores: title 40%, content 60%
        combined_score = (title_result['sentiment_score'] * 0.4 + 
                         content_result['sentiment_score'] * 0.6)
        
        # Determine label
        if combined_score > 0.2:
            label = 'positive'
        elif combined_score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Combine confidence
        combined_confidence = (title_result['confidence_score'] * 0.4 + 
                              content_result['confidence_score'] * 0.6)
        
        # Combine key words
        key_phrases = (title_result.get('key_positive_words', []) + 
                      title_result.get('key_negative_words', []) +
                      content_result.get('key_positive_words', []) + 
                      content_result.get('key_negative_words', []))[:10]
        
        return {
            'sentiment_score': combined_score,
            'sentiment_label': label,
            'confidence_score': combined_confidence,
            'key_phrases': key_phrases,
            'title_sentiment': title_result['sentiment_score'],
            'content_sentiment': content_result['sentiment_score']
        }
    
    def aggregate_sentiment(self, articles: List[Dict]) -> Dict:
        """
        Aggregate sentiment across multiple articles.
        Useful for category-level analysis.
        """
        if not articles:
            return {
                'average_sentiment': 0,
                'median_sentiment': 0,
                'std_deviation': 0,
                'positive_ratio': 0,
                'negative_ratio': 0,
                'neutral_ratio': 0,
                'sentiment_trend': 0
            }
        
        scores = [a.get('sentiment_score', 0) for a in articles]
        
        # Calculate statistics
        avg_score = sum(scores) / len(scores)
        
        # Sort for median
        sorted_scores = sorted(scores)
        mid = len(sorted_scores) // 2
        median_score = (sorted_scores[mid] + sorted_scores[~mid]) / 2
        
        # Standard deviation
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = math.sqrt(variance)
        
        # Ratios
        positive_count = sum(1 for s in scores if s > 0.2)
        negative_count = sum(1 for s in scores if s < -0.2)
        neutral_count = len(scores) - positive_count - negative_count
        
        return {
            'average_sentiment': round(avg_score, 3),
            'median_sentiment': round(median_score, 3),
            'std_deviation': round(std_dev, 3),
            'positive_ratio': round(positive_count / len(scores), 3),
            'negative_ratio': round(negative_count / len(scores), 3),
            'neutral_ratio': round(neutral_count / len(scores), 3),
            'sentiment_trend': self._calculate_trend(scores)
        }
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """Simple trend calculation (recent vs older)"""
        if len(scores) < 4:
            return 0
        
        # Compare most recent 1/3 vs oldest 1/3
        split_point = len(scores) // 3
        recent = sum(scores[:split_point]) / split_point if split_point > 0 else 0
        older = sum(scores[-split_point:]) / split_point if split_point > 0 else 0
        
        return round(recent - older, 3)
    
    def get_sentiment_summary(self, text: str) -> str:
        """Get human-readable sentiment summary"""
        result = self.analyze_text(text)
        
        if result['sentiment_score'] > 0.5:
            return "Very Positive"
        elif result['sentiment_score'] > 0.2:
            return "Positive"
        elif result['sentiment_score'] < -0.5:
            return "Very Negative"
        elif result['sentiment_score'] < -0.2:
            return "Negative"
        else:
            return "Neutral"


# Example usage and testing
if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    
    # Test cases
    test_articles = [
        ("Stock market surges to all-time high", 
         "The stock market reached record levels today as investor confidence grows."),
        
        ("Company reports massive losses", 
         "The company announced disappointing earnings, with profits down 50%."),
        
        ("Federal reserve announces rate decision", 
         "The Fed kept interest rates unchanged as expected."),
        
        ("Bitcoin rallies 20% after positive regulatory news", 
         "Cryptocurrency markets saw a massive surge following favorable regulations."),
        
        ("Oil prices crash amid demand concerns", 
         "Crude oil prices plummeted as global demand weakens significantly.")
    ]
    
    for title, content in test_articles:
        result = analyzer.analyze_article(title, content)
        print(f"\nTitle: {title}")
        print(f"Sentiment: {result['sentiment_label']} (score: {result['sentiment_score']:.2f})")
        print(f"Confidence: {result['confidence_score']:.2f}")
        print(f"Key phrases: {result['key_phrases'][:3]}")

import re
from typing import Tuple, List, Dict, Set
from collections import Counter
import math

class SentimentAnalyzer:
    """
    Sentiment analyzer with advanced lexicon and context awareness.
    """
    
    def __init__(self):
        # Expanded positive word lists
        self.positive_words = self._load_positive_words()
        self.negative_words = self._load_negative_words()
        
        # Intensifiers with different weights
        self.intensifiers = {
            'very': 1.5, 'extremely': 2.0, 'incredibly': 1.8, 'absolutely': 1.7,
            'really': 1.4, 'highly': 1.5, 'particularly': 1.4, 'exceptionally': 1.8,
            'remarkably': 1.6, 'completely': 1.5, 'totally': 1.4, 'utterly': 1.7,
            'strongly': 1.5, 'deeply': 1.4, 'overwhelmingly': 1.6
        }
        
        # Negations (flip sentiment)
        self.negations = {
            'not', 'no', 'never', 'none', 'nobody', 'nothing', 'neither',
            'hardly', 'scarcely', 'barely', "isn't", "aren't", "wasn't",
            "weren't", "hasn't", "haven't", "hadn't", "won't", "wouldn't",
            "don't", "doesn't", "didn't", "cannot", "can't", "couldn't",
            "shouldn't", "isnt", "arent", "wasnt", "werent", "hasnt",
            "without", "lack", "lacks", "missing"
        }
        
        # Downtoners (reduce sentiment intensity)
        self.downtoners = {
            'slightly': 0.5, 'somewhat': 0.6, 'kind of': 0.6, 'sort of': 0.6,
            'a little': 0.5, 'moderately': 0.7, 'fairly': 0.7, 'quite': 0.8
        }
        
        # Compile regex patterns
        self.word_pattern = re.compile(r'\b[a-z]+\b')
        self.contraction_pattern = re.compile(r"\b\w+(?:n't)\b")
        
    def _load_positive_words(self) -> Set[str]:
        """Load comprehensive positive word list"""
        positive = {
            # Basic positives
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'brilliant', 'awesome', 'incredible', 'outstanding', 'perfect',
            'positive', 'strong', 'growth', 'profit', 'gain', 'up', 'rise',
            'increasing', 'success', 'successful', 'win', 'winning', 'victory',
            'happy', 'pleased', 'satisfied', 'impressed', 'proud', 'optimistic',
            'bullish', 'rally', 'surge', 'boom', 'opportunity', 'advantage',
            'benefit', 'improvement', 'better', 'best', 'leading', 'top',
            'breakthrough', 'innovation', 'award', 'celebrate', 'hope',
            
            # Financial positive
            'surged', 'soared', 'jumped', 'climbed', 'rose', 'gained',
            'upgraded', 'outperform', 'buy', 'overweight', 'bull', 'bullish',
            'dividend', 'profit', 'revenue', 'earnings', 'beat', 'exceeded',
            'record', 'high', 'peak', 'rallying', 'recovery', 'rebound',
            
            # Achievement words
            'achieved', 'accomplished', 'succeeded', 'won', 'earned',
            'advanced', 'improved', 'enhanced', 'strengthened', 'boosted',
            
            # Positive events
            'peace', 'agreement', 'deal', 'partnership', 'collaboration',
            'launch', 'release', 'discovery', 'breakthrough', 'innovation'
        }
        return positive
    
    def _load_negative_words(self) -> Set[str]:
        """Load comprehensive negative word list with strong negatives"""
        negative = {
            # Basic negatives
            'bad', 'terrible', 'awful', 'horrible', 'disaster', 'catastrophic',
            'negative', 'weak', 'loss', 'decline', 'down', 'fall', 'decrease',
            'dropping', 'failure', 'fail', 'losing', 'defeat', 'crisis',
            'angry', 'upset', 'disappointed', 'concerned', 'pessimistic',
            'bearish', 'crash', 'plunge', 'slump', 'risk', 'threat',
            'damage', 'problem', 'issue', 'worst', 'poor', 'low',
            
            # Death and violence (CRITICAL for your use case)
            'death', 'dead', 'died', 'dying', 'kill', 'killed', 'killing',
            'murder', 'murdered', 'murdering', 'homicide', 'slain', 'assassination',
            'assassinated', 'execute', 'executed', 'execution', 'massacre',
            'genocide', 'casualty', 'casualties', 'fatal', 'fatalities',
            'victim', 'victims', 'tragic', 'tragedy', 'suffered', 'suffering',
            'injured', 'wounded', 'injuries', 'wounds', 'critical condition',
            'stampede', 'crushed', 'collapsed', 'explosion', 'blast',
            
            # Violence and conflict
            'attack', 'attacked', 'attacking', 'strike', 'struck', 'hit',
            'bomb', 'bombed', 'bombing', 'explode', 'exploded', 'explosion',
            'war', 'warfare', 'battle', 'conflict', 'fight', 'fighting',
            'violence', 'violent', 'riot', 'riots', 'protest', 'protests',
            'clash', 'clashes', 'assault', 'assaulted', 'abuse', 'abused',
            
            # Financial negative
            'plunged', 'tumbled', 'slumped', 'dropped', 'fell', 'lost',
            'downgraded', 'underperform', 'sell', 'underweight', 'bear',
            'loss', 'debt', 'bankrupt', 'bankruptcy', 'lawsuit', 'investigation',
            'fraud', 'scam', 'collapse', 'default', 'crashing',
            
            # Disease and health
            'disease', 'illness', 'sick', 'infected', 'infection', 'outbreak',
            'pandemic', 'epidemic', 'virus', 'cancer', 'tumor', 'fatal disease',
            
            # Negative events
            'blockade', 'sanctions', 'shortage', 'shortages', 'fuel crisis',
            'blackout', 'outage', 'emergency', 'evacuation', 'evacuate'
        }
        return negative
    
    def _tokenize_and_clean(self, text: str) -> List[str]:
        """Convert text to lowercase words, preserve negations"""
        text = text.lower()
        # Handle common contractions
        text = re.sub(r"n't", " not", text)
        text = re.sub(r"'re", " are", text)
        text = re.sub(r"'ve", " have", text)
        text = re.sub(r"'ll", " will", text)
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Split into words
        words = self.word_pattern.findall(text)
        return words
    
    def _calculate_sentiment_score(self, words: List[str]) -> Tuple[float, int, int, List[str]]:
        """
        Calculate sentiment score with context awareness.
        Returns (score, positive_count, negative_count, key_phrases)
        """
        positive_count = 0
        negative_count = 0
        key_phrases = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # Check for negation (affects current and next word)
            negated = False
            negation_distance = 0
            if word in self.negations:
                negated = True
                # Negation affects up to 3 following words
                negation_distance = 3
                i += 1
                if i >= len(words):
                    break
                word = words[i]
            
            # Check for intensifier/downtoner
            intensity = 1.0
            if word in self.intensifiers:
                intensity = self.intensifiers[word]
                i += 1
                if i >= len(words):
                    break
                word = words[i]
            elif word in self.downtoners:
                intensity = self.downtoners[word]
                i += 1
                if i >= len(words):
                    break
                word = words[i]
            
            # Check for multi-word phrases (e.g., "natural disaster")
            phrase = word
            if i + 1 < len(words):
                phrase = f"{word} {words[i + 1]}"
            
            # Score the word/phrase
            is_positive = word in self.positive_words or phrase in self.positive_words
            is_negative = word in self.negative_words or phrase in self.negative_words
            
            # Special handling for death/violence words (boost negativity)
            if word in {'death', 'dead', 'died', 'dying', 'kill', 'killed', 'murder', 
                       'massacre', 'casualty', 'fatal', 'tragic', 'victim'}:
                is_negative = True
                intensity *= 1.5  # Boost intensity for strong negatives
            
            if is_positive:
                if negated:
                    negative_count += 1 * intensity
                    if intensity > 1.0:
                        key_phrases.append(f"negated_{word}")
                else:
                    positive_count += 1 * intensity
                    if intensity > 1.0:
                        key_phrases.append(word)
            elif is_negative:
                if negated:
                    positive_count += 1 * intensity
                else:
                    negative_count += 1 * intensity
                    if intensity > 1.0 or word in self.negative_words:
                        key_phrases.append(word)
            
            i += 1
        
        # Calculate net score normalized to -1 to 1 range
        total = positive_count + negative_count
        if total == 0:
            score = 0.0
        else:
            # Use hyperbolic tangent for better distribution
            raw_score = (positive_count - negative_count) / total
            # Amplify strong signals
            score = math.tanh(raw_score * 2)
        
        # Clamp to [-1, 1]
        score = max(-1.0, min(1.0, score))
        
        return score, positive_count, negative_count, key_phrases[:10]
    
    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of any text with improved accuracy.
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
        score, pos_count, neg_count, key_phrases = self._calculate_sentiment_score(words)
        
        # Adjust thresholds for better classification
        if score > 0.15:  # Lowered threshold from 0.2
            label = 'positive'
        elif score < -0.15:  # Lowered threshold from -0.2
            label = 'negative'
        else:
            label = 'neutral'
        
        # Special override for strong negative words
        text_lower = text.lower()
        strong_negatives = ['death', 'dead', 'kill', 'murder', 'massacre', 'casualty', 
                           'fatal', 'tragic', 'victim', 'disaster', 'catastrophe']
        if any(word in text_lower for word in strong_negatives):
            if score > -0.3:  # If not already strongly negative
                score = max(score, -0.5)  # Ensure at least moderately negative
                label = 'negative'
        
        # Calculate confidence based on word count, score extremity, and key phrases
        total_words = len(words)
        word_confidence = min(1.0, total_words / 80)  # Lower threshold
        extremity_confidence = abs(score)
        phrase_confidence = min(1.0, len(key_phrases) / 5) * 0.3
        confidence = (word_confidence * 0.3 + extremity_confidence * 0.5 + phrase_confidence)
        confidence = min(1.0, confidence)
        
        return {
            'sentiment_score': round(score, 3),
            'sentiment_label': label,
            'confidence_score': round(confidence, 3),
            'positive_word_count': pos_count,
            'negative_word_count': neg_count,
            'key_positive_words': [p for p in key_phrases if not p.startswith('negated_')][:5],
            'key_negative_words': [p for p in key_phrases if p.startswith('negated_') or p in self.negative_words][:5]
        }
    
    def analyze_article(self, title: str, content: str) -> Dict:
        """
        Analyze sentiment of a news article with weighted scoring.
        """
        # Analyze title (higher weight for headlines)
        title_result = self.analyze_text(title)
        
        # Analyze first 3000 characters of content (more context)
        content_preview = content[:3000] if content else ''
        content_result = self.analyze_text(content_preview)
        
        # Weight: title 35%, content 65% (title is more important for news)
        combined_score = (title_result['sentiment_score'] * 0.35 + 
                         content_result['sentiment_score'] * 0.65)
        
        # Determine label with special consideration for title
        if title_result['sentiment_label'] == 'negative' and combined_score > -0.1:
            combined_score = max(combined_score, -0.2)  # Ensure negativity from title isn't lost
        
        if combined_score > 0.15:
            label = 'positive'
        elif combined_score < -0.15:
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
            'sentiment_score': round(combined_score, 3),
            'sentiment_label': label,
            'confidence_score': round(combined_confidence, 3),
            'key_phrases': key_phrases,
            'title_sentiment': title_result['sentiment_score'],
            'content_sentiment': content_result['sentiment_score']
        }

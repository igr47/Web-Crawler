# processors/category_classifier.py
import re
from typing import List, Tuple
from collections import Counter

class CategoryClassifier:
    def __init__(self):
        # Define keywords for each category
        self.category_keywords = {
            "Politics": ["president", "election", "government", "congress", "senate", "vote", "policy", "democrat", "republican", "white house"],
            "Economy": ["economy", "gdp", "inflation", "unemployment", "interest rate", "federal reserve", "recession", "growth"],
            "Technology": ["ai", "artificial intelligence", "software", "app", "startup", "tech", "digital", "innovation", "cyber"],
            "Crypto": ["bitcoin", "crypto", "ethereum", "blockchain", "nft", "web3", "token", "coinbase", "binance"],
            "Stock Market": ["stock", "market", "shares", "nasdaq", "dow jones", "s&p 500", "investor", "trading", "equity"],
            "Business": ["company", "business", "corporate", "merger", "acquisition", "ceo", "profit", "revenue", "earnings"],
            "Health": ["health", "medical", "disease", "vaccine", "hospital", "covid", "pandemic", "treatment", "doctor"],
            "Sports": ["sport", "game", "match", "tournament", "league", "championship", "team", "player", "olympic"],
            "Entertainment": ["movie", "film", "music", "celebrity", "hollywood", "netflix", "streaming", "award", "entertainment"],
            "Science": ["science", "research", "study", "scientist", "discovery", "space", "climate", "environment", "genetic"],
            "Real Estate": ["housing", "real estate", "property", "mortgage", "rent", "home", "construction", "development"],
            "Energy": ["energy", "oil", "gas", "solar", "renewable", "nuclear", "electricity", "fossil fuel", "wind"]
        }
        
        # Compile regex patterns
        self.patterns = {}
        for category, keywords in self.category_keywords.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def classify_article(self, title: str, content: str) -> Tuple[str, List[str]]:
        """Classify article into category based on content"""
        text = f"{title} {content[:2000]}".lower()
        
        scores = {}
        matched_keywords = {}
        
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            score = len(matches)
            if score > 0:
                scores[category] = score
                matched_keywords[category] = list(set(matches))
        
        if not scores:
            return "General", []
        
        # Get top category
        top_category = max(scores, key=scores.get)
        top_keywords = matched_keywords.get(top_category, [])[:5]
        
        return top_category, top_keywords
    
    def get_sub_category(self, category: str, text: str) -> str:
        """Get more specific sub-category"""
        sub_categories = {
            "Politics": {
                "Elections": ["election", "vote", "poll", "campaign"],
                "Foreign Policy": ["foreign", "international", "diplomacy", "treaty"],
                "Domestic": ["domestic", "local", "state", "municipal"]
            },
            "Crypto": {
                "Bitcoin": ["bitcoin", "btc"],
                "Ethereum": ["ethereum", "eth"],
                "DeFi": ["defi", "decentralized finance"],
                "NFTs": ["nft", "non-fungible"]
            }
        }
        
        if category not in sub_categories:
            return category
        
        text_lower = text.lower()
        for sub_cat, keywords in sub_categories[category].items():
            if any(kw in text_lower for kw in keywords):
                return sub_cat
        
        return category

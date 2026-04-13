import re
from typing import List, Tuple, Dict
from collections import Counter
import math

class CategoryClassifier:
    def __init__(self):
        # Define keywords with weights for each category
        self.category_keywords = {
            "Politics": {
                'keywords': ["president", "election", "government", "congress", "senate", 
                           "vote", "policy", "democrat", "republican", "white house",
                           "parliament", "minister", "party", "political", "campaign",
                           "diplomacy", "treaty", "foreign policy", "legislation"],
                'weight': 1.0
            },
            "Economy": {
                'keywords': ["economy", "gdp", "inflation", "unemployment", "interest rate",
                           "federal reserve", "recession", "growth", "economic", "trade",
                           "tax", "budget", "deficit", "stimulus", "monetary policy"],
                'weight': 1.0
            },
            "Technology": {
                'keywords': ["ai", "artificial intelligence", "software", "app", "startup",
                           "tech", "digital", "innovation", "cyber", "technology",
                           "algorithm", "data", "cloud", "computing", "robot"],
                'weight': 1.0
            },
            "Crypto": {
                'keywords': ["bitcoin", "crypto", "ethereum", "blockchain", "nft",
                           "web3", "token", "coinbase", "binance", "cryptocurrency",
                           "defi", "mining", "wallet", "exchange", "altcoin"],
                'weight': 1.2  # Higher weight for crypto-specific terms
            },
            "Stock Market": {
                'keywords': ["stock", "market", "shares", "nasdaq", "dow jones",
                           "s&p 500", "investor", "trading", "equity", "stocks",
                           "bull market", "bear market", "dividend", "portfolio", "index"],
                'weight': 1.1
            },
            "Business": {
                'keywords': ["company", "business", "corporate", "merger", "acquisition",
                           "ceo", "profit", "revenue", "earnings", "firm",
                           "enterprise", "industry", "market share", "quarterly", "financial"],
                'weight': 1.0
            },
            "Health": {
                'keywords': ["health", "medical", "disease", "vaccine", "hospital",
                           "covid", "pandemic", "treatment", "doctor", "patient",
                           "virus", "infection", "outbreak", "medicine", "clinical"],
                'weight': 1.0
            },
            "Energy": {
                'keywords': ["energy", "oil", "gas", "solar", "renewable", "nuclear",
                           "electricity", "fossil fuel", "wind", "petrol",
                           "fuel", "power", "grid", "refinery", "blockade"],
                'weight': 1.1
            },
            "Real Estate": {
                'keywords': ["housing", "real estate", "property", "mortgage", "rent",
                           "home", "construction", "development", "apartment", "land",
                           "building", "estate", "residential", "commercial property"],
                'weight': 1.0
            },
            "Sports": {
                'keywords': ["sport", "game", "match", "tournament", "league",
                           "championship", "team", "player", "olympic", "athlete",
                           "score", "win", "final", "cup", "tournament"],
                'weight': 1.0
            },
            "Entertainment": {
                'keywords': ["movie", "film", "music", "celebrity", "hollywood",
                           "netflix", "streaming", "award", "entertainment", "actor",
                           "actress", "director", "album", "concert", "show"],
                'weight': 1.0
            },
            "Science": {
                'keywords': ["science", "research", "study", "scientist", "discovery",
                           "space", "climate", "environment", "genetic", "experiment",
                           "laboratory", "findings", "scientific", "data", "analysis"],
                'weight': 1.0
            }
        }
        
        # Compile regex patterns with word boundaries
        self.patterns = {}
        for category, data in self.category_keywords.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in data['keywords']) + r')\b'
            self.patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def classify_article(self, title: str, content: str) -> Tuple[str, List[str]]:
        """Classify article into category with weighted scoring"""
        text = f"{title} {title} {content[:3000]}".lower()  # Title appears twice for higher weight
        
        scores = {}
        matched_keywords = {}
        
        for category, pattern in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Calculate base score with uniqueness factor
                unique_matches = set(matches)
                base_score = len(unique_matches)
                
                # Apply category weight
                weight = self.category_keywords[category]['weight']
                weighted_score = base_score * weight
                
                # Bonus for matches in title (already weighted by repeating title)
                scores[category] = weighted_score
                matched_keywords[category] = list(unique_matches)[:10]
        
        if not scores:
            # Check for general interest content
            if len(text.split()) > 100:  # Substantial content
                return "General", []
            return "Uncategorized", []
        
        # Get top category with highest weighted score
        top_category = max(scores, key=scores.get)
        top_keywords = matched_keywords.get(top_category, [])[:5]
        
        # Handle tie-breaking with more specific categories
        if len(scores) > 1:
            second_category = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1]
            if scores[top_category] - second_category[1] < 0.5:
                # Close tie - check for more specific indicators
                if top_category == "Business" and "stock" in text:
                    top_category = "Stock Market"
                elif top_category == "Technology" and "crypto" in text:
                    top_category = "Crypto"
        
        return top_category, top_keywords
    
    def get_sub_category(self, category: str, text: str) -> str:
        """Get more specific sub-category"""
        sub_categories = {
            "Politics": {
                "Elections": ["election", "vote", "poll", "campaign", "ballot"],
                "Foreign Policy": ["foreign", "international", "diplomacy", "treaty", "embassy"],
                "Domestic": ["domestic", "local", "state", "municipal", "regional"],
                "Conflict/War": ["war", "conflict", "military", "defense", "attack", "blockade"]
            },
            "Crypto": {
                "Bitcoin": ["bitcoin", "btc"],
                "Ethereum": ["ethereum", "eth"],
                "DeFi": ["defi", "decentralized finance", "lending", "staking"],
                "NFTs": ["nft", "non-fungible", "digital art"],
                "Regulation": ["regulation", "sec", "legal", "compliance"]
            },
            "Energy": {
                "Oil & Gas": ["oil", "gas", "petrol", "refinery", "crude"],
                "Renewable": ["solar", "wind", "renewable", "green energy", "hydro"],
                "Nuclear": ["nuclear", "reactor", "atomic"],
                "Crisis": ["blockade", "shortage", "crisis", "price surge"]
            },
            "Health": {
                "Disease Outbreak": ["outbreak", "epidemic", "pandemic", "virus", "infection"],
                "Medical Research": ["research", "study", "trial", "treatment", "therapy"],
                "Healthcare Policy": ["healthcare", "policy", "insurance", "medicare"]
            }
        }
        
        if category not in sub_categories:
            return category
        
        text_lower = text.lower()
        best_sub = category
        best_score = 0
        
        for sub_cat, keywords in sub_categories[category].items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_sub = sub_cat
        
        return best_sub if best_score > 0 else category

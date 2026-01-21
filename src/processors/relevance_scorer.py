"""
Relevance Scorer

Scores papers based on how relevant they are to Leopold's research interests.
Uses keyword matching with weighted categories.
"""
import re
from typing import List, Dict, Tuple
from pathlib import Path
import yaml


class RelevanceScorer:
    """Scores paper relevance based on keyword matching"""
    
    def __init__(self, keywords_config: Dict = None):
        """
        Initialize scorer with keywords
        
        Args:
            keywords_config: Dict with 'primary', 'secondary', 'tertiary', 'exclude' lists
        """
        if keywords_config:
            self.keywords = keywords_config
        else:
            self.keywords = self._load_default_keywords()
        
        # Compile regex patterns for faster matching
        self._compile_patterns()
        
        # Weights for different keyword categories
        self.weights = {
            'primary': 3.0,
            'secondary': 2.0,
            'tertiary': 1.0,
            'exclude': -10.0  # Strong penalty for excluded keywords
        }
        
    def _load_default_keywords(self) -> Dict:
        """Load keywords from config file"""
        config_path = Path(__file__).parent.parent.parent / "config" / "keywords.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            keywords = {
                'primary': [],
                'secondary': [],
                'tertiary': [],
                'exclude': config.get('exclude_keywords', [])
            }
            
            for category, kw_dict in config.get('primary_keywords', {}).items():
                keywords['primary'].extend(kw_dict)
            for category, kw_dict in config.get('secondary_keywords', {}).items():
                keywords['secondary'].extend(kw_dict)
            for category, kw_dict in config.get('tertiary_keywords', {}).items():
                keywords['tertiary'].extend(kw_dict)
                
            return keywords
            
        except Exception as e:
            print(f"Warning: Could not load keywords config: {e}")
            return self._get_fallback_keywords()
    
    def _get_fallback_keywords(self) -> Dict:
        """Fallback keywords if config not found"""
        return {
            'primary': [
                "mechanism design", "auction theory", "capacity market",
                "electricity market", "power market", "peak load pricing",
                "carbon pricing", "emissions trading", "renewable integration"
            ],
            'secondary': [
                "vertical integration", "price regulation", "real options",
                "market power", "welfare economics", "consumer choice"
            ],
            'tertiary': [
                "game theory", "contract theory", "energy policy"
            ],
            'exclude': [
                "machine learning", "deep learning", "neural network",
                "cryptocurrency", "blockchain"
            ]
        }
    
    def _compile_patterns(self):
        """Compile regex patterns for all keywords"""
        self.patterns = {}
        
        for category, keywords in self.keywords.items():
            self.patterns[category] = []
            for keyword in keywords:
                # Create case-insensitive pattern with word boundaries
                pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
                self.patterns[category].append((keyword, pattern))
    
    def score_paper(self, paper) -> Tuple[float, List[str]]:
        """
        Score a paper's relevance
        
        Args:
            paper: Paper object with title and abstract
            
        Returns:
            Tuple of (score, matched_keywords)
        """
        # Combine title and abstract for matching
        text = f"{paper.title} {paper.abstract}"
        
        score = 0.0
        matched_keywords = []
        
        # Check each category
        for category, patterns in self.patterns.items():
            for keyword, pattern in patterns:
                if pattern.search(text):
                    weight = self.weights[category]
                    score += weight
                    
                    if weight > 0:  # Don't include excluded keywords in matches
                        matched_keywords.append(keyword)
        
        # Normalize score (0-100 scale)
        # Max realistic score ~15 keywords * 3 weight = 45
        normalized_score = min(100, max(0, (score / 45) * 100))
        
        return normalized_score, matched_keywords
    
    def filter_and_score_papers(self, papers: list, min_score: float = 5.0) -> list:
        """
        Filter and score a list of papers
        
        Args:
            papers: List of Paper objects
            min_score: Minimum score to include (0-100)
            
        Returns:
            List of papers with relevance scores, sorted by score
        """
        print(f"  Scoring {len(papers)} papers for relevance...")
        
        scored_papers = []
        
        for paper in papers:
            score, keywords = self.score_paper(paper)
            
            if score >= min_score:
                paper.relevance_score = score
                paper.matched_keywords = keywords  # Add as attribute
                scored_papers.append(paper)
        
        # Sort by relevance score (highest first)
        scored_papers.sort(key=lambda p: p.relevance_score, reverse=True)
        
        print(f"  {len(scored_papers)} papers passed relevance threshold (>= {min_score})")
        
        return scored_papers
    
    def get_score_breakdown(self, paper) -> Dict:
        """Get detailed breakdown of why a paper scored as it did"""
        text = f"{paper.title} {paper.abstract}"
        
        breakdown = {
            'primary_matches': [],
            'secondary_matches': [],
            'tertiary_matches': [],
            'exclude_matches': []
        }
        
        for category, patterns in self.patterns.items():
            for keyword, pattern in patterns:
                if pattern.search(text):
                    breakdown[f'{category}_matches'].append(keyword)
        
        return breakdown


def test_scorer():
    """Test the relevance scorer"""
    from collections import namedtuple
    
    print("Testing relevance scorer...")
    scorer = RelevanceScorer()
    
    # Create mock papers
    MockPaper = namedtuple('MockPaper', ['title', 'abstract', 'relevance_score'])
    
    test_papers = [
        MockPaper(
            title="Mechanism Design for Capacity Markets in Electricity Systems",
            abstract="We study the optimal design of capacity mechanisms for ensuring security of supply in power markets.",
            relevance_score=0
        ),
        MockPaper(
            title="Deep Learning for Image Recognition",
            abstract="We present a neural network architecture for computer vision tasks.",
            relevance_score=0
        ),
        MockPaper(
            title="Carbon Pricing and Emissions Trading Schemes",
            abstract="This paper analyzes the welfare effects of carbon markets and their impact on renewable integration.",
            relevance_score=0
        ),
    ]
    
    print("\nScoring test papers:")
    for paper in test_papers:
        score, keywords = scorer.score_paper(paper)
        print(f"\n  Score: {score:.1f}")
        print(f"  Title: {paper.title}")
        print(f"  Keywords: {keywords}")


if __name__ == "__main__":
    test_scorer()

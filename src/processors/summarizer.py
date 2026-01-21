"""
Paper Summarizer using Claude API

Generates concise summaries of academic papers tailored to Leopold's interests.
"""
import os
from typing import List, Optional
import json


class PaperSummarizer:
    """Summarizes papers using Claude API"""
    
    def __init__(self, api_key: str = None):
        """
        Initialize summarizer
        
        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        
        if self.api_key:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=self.api_key)
            except ImportError:
                print("Warning: anthropic package not installed. Summaries disabled.")
        else:
            print("Warning: No ANTHROPIC_API_KEY found. Summaries disabled.")
    
    def summarize_paper(self, paper, max_length: int = 150) -> str:
        """
        Generate a concise summary of a paper
        
        Args:
            paper: Paper object with title and abstract
            max_length: Target summary length in words
            
        Returns:
            Summary string
        """
        if not self.client:
            return self._simple_summary(paper)
        
        try:
            prompt = f"""You are helping a researcher in energy economics and market design. 
Summarize this academic paper in 2-3 sentences. Focus on:
- The main research question
- The methodology (theory/empirical/experiment)
- The key finding or contribution

Be concise and technical. The reader is an expert.

Title: {paper.title}

Abstract: {paper.abstract[:1500]}

Summary:"""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"    Error summarizing paper: {e}")
            return self._simple_summary(paper)
    
    def _simple_summary(self, paper) -> str:
        """Generate a simple summary without AI (first 2 sentences of abstract)"""
        if not paper.abstract:
            return "No abstract available."
        
        sentences = paper.abstract.split('. ')
        summary = '. '.join(sentences[:2])
        
        if len(summary) > 300:
            summary = summary[:297] + "..."
            
        return summary + "."
    
    def summarize_papers_batch(self, papers: list, max_papers: int = 15) -> list:
        """
        Summarize a batch of papers
        
        Args:
            papers: List of Paper objects
            max_papers: Maximum papers to summarize (to control API costs)
            
        Returns:
            Papers with summary field populated
        """
        print(f"  Generating summaries for {min(len(papers), max_papers)} papers...")
        
        for i, paper in enumerate(papers[:max_papers]):
            paper.summary = self.summarize_paper(paper)
            
            # Progress indicator
            if (i + 1) % 5 == 0:
                print(f"    Summarized {i + 1}/{min(len(papers), max_papers)}")
        
        return papers
    
    def generate_digest_intro(self, papers: list, period: str = "daily") -> str:
        """
        Generate an introduction/overview for the digest
        
        Args:
            papers: List of papers to summarize
            period: "daily" or "weekly"
            
        Returns:
            Digest introduction text
        """
        if not self.client or len(papers) == 0:
            return f"Found {len(papers)} relevant papers."
        
        # Group papers by category
        categories = {}
        for paper in papers[:15]:
            # Use first matched keyword or "General" as category
            cat = getattr(paper, 'matched_keywords', ['General'])[0] if hasattr(paper, 'matched_keywords') and paper.matched_keywords else "General"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(paper.title)
        
        try:
            prompt = f"""You are writing a research digest introduction for an energy economics researcher.

Papers found by category:
{json.dumps(categories, indent=2)}

Write a brief 2-3 sentence overview highlighting:
1. How many papers were found
2. The main themes/topics covered
3. Any particularly notable papers

Keep it professional and concise."""

            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            return f"Found {len(papers)} relevant papers across {len(categories)} topic areas."


def test_summarizer():
    """Test the summarizer"""
    from collections import namedtuple
    
    print("Testing summarizer...")
    summarizer = PaperSummarizer()
    
    MockPaper = namedtuple('MockPaper', ['title', 'abstract', 'summary'])
    
    paper = MockPaper(
        title="Optimal Capacity Mechanisms under Uncertainty",
        abstract="""This paper studies the design of capacity markets when demand is uncertain 
        and producers have private information about their costs. We develop a mechanism design 
        framework that characterizes the optimal procurement auction. Our main result shows that 
        the optimal mechanism involves quantity-contingent payments that depend on realized demand. 
        We apply our framework to electricity markets and show that current capacity market designs 
        can be significantly improved.""",
        summary=""
    )
    
    print(f"\nTitle: {paper.title}")
    print(f"\nAbstract: {paper.abstract[:200]}...")
    
    summary = summarizer.summarize_paper(paper)
    print(f"\nSummary: {summary}")


if __name__ == "__main__":
    test_summarizer()

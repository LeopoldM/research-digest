"""
arXiv Paper Collector

Fetches recent papers from arXiv in relevant categories.
Uses the arXiv API: https://arxiv.org/help/api
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import time


@dataclass
class Paper:
    """Represents an academic paper"""
    title: str
    authors: List[str]
    abstract: str
    url: str
    pdf_url: Optional[str]
    source: str
    source_id: str  # arXiv ID, DOI, etc.
    published_date: str
    categories: List[str]
    relevance_score: float = 0.0
    summary: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


class ArxivCollector:
    """Collects papers from arXiv API"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # Categories relevant to Leopold's research
    CATEGORIES = [
        "econ.TH",   # Economic Theory
        "econ.GN",   # General Economics  
        "cs.GT",     # Computer Science - Game Theory
        "q-fin.EC",  # Quantitative Finance - Economics
        "q-fin.GN",  # Quantitative Finance - General
    ]
    
    def __init__(self, categories: List[str] = None):
        self.categories = categories or self.CATEGORIES
        
    def fetch_recent(self, days: int = 1, max_results: int = 100) -> List[Paper]:
        """
        Fetch papers from the last N days
        
        Args:
            days: Number of days to look back
            max_results: Maximum papers to fetch per category
            
        Returns:
            List of Paper objects
        """
        all_papers = []
        
        for category in self.categories:
            print(f"  Fetching arXiv category: {category}")
            papers = self._fetch_category(category, max_results)
            all_papers.extend(papers)
            time.sleep(3)  # Be nice to the API
            
        # Remove duplicates (papers can be in multiple categories)
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper.source_id not in seen_ids:
                seen_ids.add(paper.source_id)
                unique_papers.append(paper)
                
        print(f"  Found {len(unique_papers)} unique papers from arXiv")
        return unique_papers
    
    def _fetch_category(self, category: str, max_results: int) -> List[Paper]:
        """Fetch papers from a specific category"""
        
        # Build query - search for recent papers in category
        query = f"cat:{category}"
        
        params = {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            return self._parse_response(response.text)
        except requests.RequestException as e:
            print(f"    Error fetching {category}: {e}")
            return []
    
    def _parse_response(self, xml_text: str) -> List[Paper]:
        """Parse arXiv API XML response"""
        papers = []
        
        # Parse XML
        root = ET.fromstring(xml_text)
        
        # Define namespace
        ns = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }
        
        for entry in root.findall('atom:entry', ns):
            try:
                paper = self._parse_entry(entry, ns)
                if paper:
                    papers.append(paper)
            except Exception as e:
                print(f"    Error parsing entry: {e}")
                continue
                
        return papers
    
    def _parse_entry(self, entry, ns: dict) -> Optional[Paper]:
        """Parse a single entry from arXiv response"""
        
        # Get basic info
        title = entry.find('atom:title', ns)
        title = title.text.strip().replace('\n', ' ') if title is not None else ""
        
        abstract = entry.find('atom:summary', ns)
        abstract = abstract.text.strip().replace('\n', ' ') if abstract is not None else ""
        
        # Get authors
        authors = []
        for author in entry.findall('atom:author', ns):
            name = author.find('atom:name', ns)
            if name is not None:
                authors.append(name.text)
        
        # Get URL and ID
        arxiv_id = ""
        url = ""
        pdf_url = ""
        
        for link in entry.findall('atom:link', ns):
            href = link.get('href', '')
            link_type = link.get('type', '')
            
            if 'abs' in href:
                url = href
                arxiv_id = href.split('/abs/')[-1]
            elif link_type == 'application/pdf':
                pdf_url = href
        
        # Get publication date
        published = entry.find('atom:published', ns)
        published_date = published.text[:10] if published is not None else ""
        
        # Get categories
        categories = []
        for cat in entry.findall('atom:category', ns):
            term = cat.get('term', '')
            if term:
                categories.append(term)
        
        if not title or not arxiv_id:
            return None
            
        return Paper(
            title=title,
            authors=authors,
            abstract=abstract,
            url=url,
            pdf_url=pdf_url,
            source="arxiv",
            source_id=arxiv_id,
            published_date=published_date,
            categories=categories
        )


def test_arxiv_collector():
    """Test the arXiv collector"""
    print("Testing arXiv collector...")
    collector = ArxivCollector()
    papers = collector.fetch_recent(days=7, max_results=20)
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title[:80]}...")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   Categories: {paper.categories}")
        print(f"   URL: {paper.url}")
    
    return papers


if __name__ == "__main__":
    test_arxiv_collector()

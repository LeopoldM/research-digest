"""
OpenAlex Paper Collector

Fetches recent papers from OpenAlex API.
OpenAlex is free and covers all major academic journals.
API docs: https://docs.openalex.org/
"""
import requests
from datetime import datetime, timedelta
from typing import List, Optional
from dataclasses import dataclass, asdict
import time

from .arxiv_collector import Paper


class OpenAlexCollector:
    """Collects papers from OpenAlex API"""
    
    BASE_URL = "https://api.openalex.org"
    TIMEOUT = 90  # Increased timeout
    MAX_RETRIES = 2
    
    # Top journals for Leopold's research interests
    JOURNALS = [
        # Top Economics
        "American Economic Review",
        "Quarterly Journal of Economics", 
        "Econometrica",
        "Review of Economic Studies",
        "Journal of Political Economy",
        
        # Theory
        "Journal of Economic Theory",
        "Theoretical Economics",
        "Games and Economic Behavior",
        "Economic Theory",
        "RAND Journal of Economics",
        
        # IO
        "Journal of Industrial Economics",
        "International Journal of Industrial Organization",
        "Journal of Economics and Management Strategy",
        
        # Energy & Environmental
        "Energy Economics",
        "The Energy Journal",
        "Energy Policy",
        "Journal of Environmental Economics and Management",
        "Environmental and Resource Economics",
        "Resource and Energy Economics",
        "Utilities Policy",
    ]
    
    def __init__(self, email: str = "leopold.monjoie@aalto.fi", journals: List[str] = None):
        """
        Initialize collector
        
        Args:
            email: Email for OpenAlex polite pool (faster rate limits)
            journals: List of journal names to monitor
        """
        self.email = email
        self.journals = journals or self.JOURNALS
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"ResearchDigest/1.0 (mailto:{email})"
        })
    
    def _make_request(self, url: str, params: dict) -> Optional[dict]:
        """Make request with retry logic"""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = self.session.get(url, params=params, timeout=self.TIMEOUT)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                print(f"    Timeout (attempt {attempt + 1}/{self.MAX_RETRIES}), retrying...")
                time.sleep(2)
            except Exception as e:
                print(f"    Error: {e}")
                break
        return None
        
    def fetch_recent(self, days: int = 7, max_results: int = 200) -> List[Paper]:
        """
        Fetch recent papers from monitored journals
        
        Args:
            days: Number of days to look back
            max_results: Maximum total papers to fetch
            
        Returns:
            List of Paper objects
        """
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        from_date = start_date.strftime("%Y-%m-%d")
        to_date = end_date.strftime("%Y-%m-%d")
        
        print(f"  Fetching OpenAlex papers from {from_date} to {to_date}")
        
        all_papers = []
        
        # Method 1: Search by keywords in relevant concepts
        keyword_papers = self._fetch_by_concepts(from_date, to_date, max_results // 2)
        all_papers.extend(keyword_papers)
        
        # Method 2: Search top journals
        journal_papers = self._fetch_from_journals(from_date, to_date, max_results // 2)
        all_papers.extend(journal_papers)
        
        # Remove duplicates
        seen_ids = set()
        unique_papers = []
        for paper in all_papers:
            if paper.source_id not in seen_ids:
                seen_ids.add(paper.source_id)
                unique_papers.append(paper)
        
        print(f"  Found {len(unique_papers)} unique papers from OpenAlex")
        return unique_papers
    
    def _fetch_by_concepts(self, from_date: str, to_date: str, max_results: int) -> List[Paper]:
        """Fetch papers by relevant concepts/keywords"""
        
        # OpenAlex concept IDs for relevant topics
        concepts = [
            "C162324750",  # Economics
            "C10138342",   # Mechanism design
            "C107457646",  # Auction theory
            "C2776384193", # Energy economics
            "C39549134",   # Environmental economics
            "C175444787",  # Industrial organization
        ]
        
        papers = []
        
        for concept_id in concepts[:3]:  # Limit to avoid too many requests
            try:
                url = f"{self.BASE_URL}/works"
                params = {
                    "filter": f"concepts.id:{concept_id},from_publication_date:{from_date},to_publication_date:{to_date}",
                    "sort": "publication_date:desc",
                    "per_page": min(50, max_results // 3),
                    "mailto": self.email
                }
                
                data = self._make_request(url, params)
                if data:
                    for work in data.get("results", []):
                        paper = self._parse_work(work)
                        if paper:
                            papers.append(paper)
                        
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"    Error fetching concept {concept_id}: {e}")
                continue
                
        return papers
    
    def _fetch_from_journals(self, from_date: str, to_date: str, max_results: int) -> List[Paper]:
        """Fetch recent papers from top journals"""
        
        papers = []
        papers_per_journal = max(5, max_results // len(self.journals))
        
        for journal_name in self.journals[:10]:  # Limit to top 10 journals
            try:
                url = f"{self.BASE_URL}/works"
                
                # Search by journal name in source
                params = {
                    "filter": f"primary_location.source.display_name.search:{journal_name},from_publication_date:{from_date},to_publication_date:{to_date}",
                    "sort": "publication_date:desc",
                    "per_page": papers_per_journal,
                    "mailto": self.email
                }
                
                data = self._make_request(url, params)
                if data:
                    for work in data.get("results", []):
                        paper = self._parse_work(work)
                        if paper:
                            papers.append(paper)
                            
                time.sleep(0.3)  # Rate limiting
                
            except Exception as e:
                print(f"    Error fetching journal {journal_name}: {e}")
                continue
                
        return papers
    
    def _parse_work(self, work: dict) -> Optional[Paper]:
        """Parse an OpenAlex work into a Paper object"""
        
        try:
            # Get basic info
            title = work.get("title", "")
            if not title:
                return None
                
            # Get abstract
            abstract = ""
            if work.get("abstract_inverted_index"):
                # OpenAlex returns inverted index, need to reconstruct
                abstract = self._reconstruct_abstract(work["abstract_inverted_index"])
            
            # Get authors
            authors = []
            for authorship in work.get("authorships", [])[:10]:
                author = authorship.get("author", {})
                name = author.get("display_name", "")
                if name:
                    authors.append(name)
            
            # Get URL and DOI
            doi = work.get("doi", "")
            url = doi if doi else work.get("id", "")
            
            # Get source ID (OpenAlex ID)
            source_id = work.get("id", "").replace("https://openalex.org/", "")
            
            # Get publication date
            pub_date = work.get("publication_date", "")
            
            # Get categories/concepts
            categories = []
            for concept in work.get("concepts", [])[:5]:
                categories.append(concept.get("display_name", ""))
            
            # Get journal name
            source_name = ""
            primary_location = work.get("primary_location", {})
            if primary_location:
                source = primary_location.get("source", {})
                if source:
                    source_name = source.get("display_name", "")
            
            if source_name:
                categories.insert(0, f"Journal: {source_name}")
            
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract[:2000],  # Limit abstract length
                url=url,
                pdf_url=work.get("open_access", {}).get("oa_url", ""),
                source="openalex",
                source_id=source_id,
                published_date=pub_date,
                categories=categories
            )
            
        except Exception as e:
            print(f"    Error parsing work: {e}")
            return None
    
    def _reconstruct_abstract(self, inverted_index: dict) -> str:
        """Reconstruct abstract from OpenAlex inverted index format"""
        if not inverted_index:
            return ""
            
        try:
            # Create list of (position, word) tuples
            words = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    words.append((pos, word))
            
            # Sort by position and join
            words.sort(key=lambda x: x[0])
            return " ".join(word for _, word in words)
        except:
            return ""


def test_openalex_collector():
    """Test the OpenAlex collector"""
    print("Testing OpenAlex collector...")
    collector = OpenAlexCollector()
    papers = collector.fetch_recent(days=14, max_results=50)
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title[:80]}...")
        print(f"   Authors: {', '.join(paper.authors[:3])}")
        print(f"   Source: {paper.categories[0] if paper.categories else 'N/A'}")
        print(f"   URL: {paper.url}")
    
    return papers


if __name__ == "__main__":
    test_openalex_collector()

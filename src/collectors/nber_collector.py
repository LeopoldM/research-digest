"""
NBER Working Papers Collector

Fetches recent working papers from NBER RSS feed.
"""
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Optional
import re

from .arxiv_collector import Paper


class NBERCollector:
    """Collects working papers from NBER"""
    
    RSS_URL = "https://www.nber.org/rss/new.xml"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ResearchDigest/1.0"
        })
        
    def fetch_recent(self, days: int = 7, max_results: int = 50) -> List[Paper]:
        """
        Fetch recent NBER working papers
        
        Args:
            days: Number of days to look back (note: RSS feed is limited)
            max_results: Maximum papers to fetch
            
        Returns:
            List of Paper objects
        """
        print(f"  Fetching NBER working papers...")
        
        try:
            response = self.session.get(self.RSS_URL, timeout=30)
            response.raise_for_status()
            papers = self._parse_rss(response.text, max_results)
            print(f"  Found {len(papers)} papers from NBER")
            return papers
            
        except Exception as e:
            print(f"  Error fetching NBER: {e}")
            return []
    
    def _parse_rss(self, xml_text: str, max_results: int) -> List[Paper]:
        """Parse NBER RSS feed"""
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            
            # Find all items in the RSS feed
            for item in root.findall(".//item")[:max_results]:
                paper = self._parse_item(item)
                if paper:
                    papers.append(paper)
                    
        except ET.ParseError as e:
            print(f"  Error parsing RSS: {e}")
            
        return papers
    
    def _parse_item(self, item) -> Optional[Paper]:
        """Parse a single RSS item"""
        
        try:
            title = item.find("title")
            title = title.text.strip() if title is not None else ""
            
            link = item.find("link")
            url = link.text.strip() if link is not None else ""
            
            description = item.find("description")
            abstract = description.text.strip() if description is not None else ""
            
            # Clean up abstract (remove HTML tags)
            abstract = re.sub(r'<[^>]+>', '', abstract)
            
            pub_date = item.find("pubDate")
            pub_date_str = pub_date.text if pub_date is not None else ""
            
            # Try to parse the date
            published_date = ""
            if pub_date_str:
                try:
                    # NBER format: "Mon, 01 Jan 2024 00:00:00 -0500"
                    dt = datetime.strptime(pub_date_str[:16], "%a, %d %b %Y")
                    published_date = dt.strftime("%Y-%m-%d")
                except:
                    published_date = pub_date_str[:10]
            
            # Extract NBER ID from URL
            nber_id = ""
            if url:
                match = re.search(r'/papers/w(\d+)', url)
                if match:
                    nber_id = f"w{match.group(1)}"
            
            # Try to extract authors from title or description
            # NBER titles often have authors
            authors = []
            
            if not title:
                return None
                
            return Paper(
                title=title,
                authors=authors,
                abstract=abstract[:2000],
                url=url,
                pdf_url=url.replace("/papers/", "/system/files/working_papers/") + ".pdf" if url else "",
                source="nber",
                source_id=nber_id or url,
                published_date=published_date,
                categories=["NBER Working Paper"]
            )
            
        except Exception as e:
            print(f"    Error parsing NBER item: {e}")
            return None


def test_nber_collector():
    """Test the NBER collector"""
    print("Testing NBER collector...")
    collector = NBERCollector()
    papers = collector.fetch_recent(days=7, max_results=20)
    
    print(f"\nFound {len(papers)} papers:")
    for i, paper in enumerate(papers[:5], 1):
        print(f"\n{i}. {paper.title[:80]}...")
        print(f"   URL: {paper.url}")
        print(f"   Date: {paper.published_date}")
    
    return papers


if __name__ == "__main__":
    test_nber_collector()

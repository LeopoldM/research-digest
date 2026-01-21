"""
DOI and Paper Validator

⚠️ CRITICAL: This module prevents the "kryptonite" issue that Dimant discovered.
Every paper must be validated as REAL before inclusion in the digest.

We validate papers exist by checking:
1. DOI resolution via doi.org
2. arXiv ID existence via arXiv API
3. OpenAlex ID existence via OpenAlex API
"""
import requests
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class PaperValidator:
    """Validates that papers actually exist"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ResearchDigest/1.0 (paper-validator)"
        })
        # Cache validation results to avoid repeated checks
        self._cache = {}
        
    def validate_paper(self, paper) -> Tuple[bool, str]:
        """
        Validate that a paper exists
        
        Args:
            paper: Paper object with source and source_id
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Check cache first
        cache_key = f"{paper.source}:{paper.source_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = (False, "Unknown source")
        
        if paper.source == "arxiv":
            result = self._validate_arxiv(paper.source_id)
        elif paper.source == "openalex":
            result = self._validate_openalex(paper.source_id)
        elif paper.source == "nber":
            result = self._validate_nber(paper.url)
        elif paper.url and "doi.org" in paper.url:
            doi = paper.url.replace("https://doi.org/", "")
            result = self._validate_doi(doi)
        else:
            # For papers with URLs, just check the URL is accessible
            result = self._validate_url(paper.url)
        
        # Cache result
        self._cache[cache_key] = result
        return result
    
    def _validate_doi(self, doi: str) -> Tuple[bool, str]:
        """Validate a DOI exists via doi.org"""
        if not doi:
            return (False, "No DOI provided")
        
        # Clean DOI
        doi = doi.replace("https://doi.org/", "").strip()
        
        try:
            # Use DOI content negotiation
            url = f"https://doi.org/{doi}"
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                return (True, "DOI validated")
            else:
                return (False, f"DOI not found (status {response.status_code})")
                
        except requests.Timeout:
            return (False, "DOI validation timeout")
        except Exception as e:
            return (False, f"DOI validation error: {str(e)}")
    
    def _validate_arxiv(self, arxiv_id: str) -> Tuple[bool, str]:
        """Validate an arXiv paper exists"""
        if not arxiv_id:
            return (False, "No arXiv ID provided")
        
        try:
            url = f"https://arxiv.org/abs/{arxiv_id}"
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                return (True, "arXiv ID validated")
            else:
                return (False, f"arXiv paper not found (status {response.status_code})")
                
        except Exception as e:
            return (False, f"arXiv validation error: {str(e)}")
    
    def _validate_openalex(self, openalex_id: str) -> Tuple[bool, str]:
        """Validate an OpenAlex work exists"""
        if not openalex_id:
            return (False, "No OpenAlex ID provided")
        
        try:
            url = f"https://api.openalex.org/works/{openalex_id}"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return (True, "OpenAlex ID validated")
            else:
                return (False, f"OpenAlex work not found (status {response.status_code})")
                
        except Exception as e:
            return (False, f"OpenAlex validation error: {str(e)}")
    
    def _validate_nber(self, url: str) -> Tuple[bool, str]:
        """Validate an NBER paper exists"""
        if not url:
            return (False, "No NBER URL provided")
        
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                return (True, "NBER paper validated")
            else:
                return (False, f"NBER paper not found (status {response.status_code})")
                
        except Exception as e:
            return (False, f"NBER validation error: {str(e)}")
    
    def _validate_url(self, url: str) -> Tuple[bool, str]:
        """Generic URL validation"""
        if not url:
            return (False, "No URL provided")
        
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10)
            
            if response.status_code == 200:
                return (True, "URL validated")
            else:
                return (False, f"URL not accessible (status {response.status_code})")
                
        except Exception as e:
            return (False, f"URL validation error: {str(e)}")
    
    def validate_papers_batch(self, papers: list, max_workers: int = 5) -> list:
        """
        Validate a batch of papers in parallel
        
        Args:
            papers: List of Paper objects
            max_workers: Number of parallel threads
            
        Returns:
            List of validated papers (invalid papers are filtered out)
        """
        print(f"  Validating {len(papers)} papers...")
        
        validated_papers = []
        invalid_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all validation tasks
            future_to_paper = {
                executor.submit(self.validate_paper, paper): paper 
                for paper in papers
            }
            
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                try:
                    is_valid, reason = future.result()
                    if is_valid:
                        validated_papers.append(paper)
                    else:
                        invalid_count += 1
                        # Uncomment for debugging:
                        # print(f"    ❌ Invalid: {paper.title[:50]}... - {reason}")
                except Exception as e:
                    invalid_count += 1
                    print(f"    Error validating paper: {e}")
        
        print(f"  ✓ Validated: {len(validated_papers)}, ❌ Invalid: {invalid_count}")
        return validated_papers


def test_validator():
    """Test the paper validator"""
    print("Testing paper validator...")
    
    validator = PaperValidator()
    
    # Test DOI validation
    print("\nTesting DOI validation:")
    test_dois = [
        "10.1257/aer.20190623",  # Real AER paper
        "10.1111/fake.12345",     # Fake DOI
    ]
    
    for doi in test_dois:
        is_valid, reason = validator._validate_doi(doi)
        status = "✓" if is_valid else "❌"
        print(f"  {status} {doi}: {reason}")
    
    # Test arXiv validation
    print("\nTesting arXiv validation:")
    test_arxiv = [
        "2401.00001",   # Real paper
        "9999.99999",   # Fake ID
    ]
    
    for arxiv_id in test_arxiv:
        is_valid, reason = validator._validate_arxiv(arxiv_id)
        status = "✓" if is_valid else "❌"
        print(f"  {status} {arxiv_id}: {reason}")


if __name__ == "__main__":
    test_validator()

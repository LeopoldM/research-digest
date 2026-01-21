#!/usr/bin/env python3
"""
Research Digest - Main Runner

This is the main script that orchestrates the entire digest pipeline:
1. Collect papers from various sources
2. Validate papers are real (DOI check)
3. Score relevance based on keywords
4. Generate AI summaries
5. Format and send email digest

Run daily via GitHub Actions or locally with:
    python run_digest.py --daily
    python run_digest.py --weekly
"""
import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from collectors.arxiv_collector import ArxivCollector, Paper
from collectors.openalex_collector import OpenAlexCollector
from collectors.nber_collector import NBERCollector
from processors.doi_validator import PaperValidator
from processors.relevance_scorer import RelevanceScorer
from processors.summarizer import PaperSummarizer
from outputs.digest_formatter import DigestFormatter
from outputs.email_sender import EmailSender


class ResearchDigest:
    """Main orchestrator for the research digest pipeline"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        # Initialize components
        self.arxiv_collector = ArxivCollector()
        self.openalex_collector = OpenAlexCollector()
        self.nber_collector = NBERCollector()
        self.validator = PaperValidator()
        self.scorer = RelevanceScorer()
        self.summarizer = PaperSummarizer()
        self.formatter = DigestFormatter(researcher_name="Leopold")
        self.email_sender = EmailSender()
        
        # Data directory
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
    
    def run_daily(self) -> dict:
        """Run daily digest pipeline"""
        print("\n" + "="*60)
        print("🔬 RESEARCH DIGEST - DAILY RUN")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Step 1: Collect papers
        print("\n📥 Step 1: Collecting papers...")
        papers = self._collect_all_papers(days=1)
        
        if not papers:
            print("No papers found. Exiting.")
            return {"status": "no_papers", "count": 0}
        
        # Step 2: Validate papers
        print("\n✅ Step 2: Validating papers...")
        papers = self.validator.validate_papers_batch(papers)
        
        if not papers:
            print("No valid papers after validation. Exiting.")
            return {"status": "no_valid_papers", "count": 0}
        
        # Step 3: Score relevance
        print("\n📊 Step 3: Scoring relevance...")
        papers = self.scorer.filter_and_score_papers(papers, min_score=5.0)
        
        if not papers:
            print("No relevant papers found. Exiting.")
            return {"status": "no_relevant_papers", "count": 0}
        
        # Step 4: Generate summaries (for top papers)
        print("\n📝 Step 4: Generating summaries...")
        papers = self.summarizer.summarize_papers_batch(papers, max_papers=15)
        
        # Step 5: Generate digest intro
        intro = self.summarizer.generate_digest_intro(papers, period="daily")
        
        # Step 6: Format digest
        print("\n📧 Step 5: Formatting digest...")
        html_digest = self.formatter.format_email_html(papers[:15], intro=intro, period="daily")
        plain_digest = self.formatter.format_plaintext(papers[:15], intro=intro)
        
        # Step 7: Save and send
        print("\n📤 Step 6: Saving and sending...")
        self._save_digest(papers, "daily")
        self._save_html(html_digest, "daily")
        
        # Send email
        to_email = os.getenv("DIGEST_EMAIL", "leopold.monjoie@aalto.fi")
        subject = f"📚 Research Digest - {datetime.now().strftime('%B %d, %Y')}"
        
        self.email_sender.send_digest(
            to_email=to_email,
            subject=subject,
            html_content=html_digest,
            plain_content=plain_digest
        )
        
        print("\n" + "="*60)
        print(f"✅ Daily digest complete! Found {len(papers)} relevant papers.")
        print("="*60)
        
        return {
            "status": "success",
            "count": len(papers),
            "papers": [p.to_dict() for p in papers[:15]]
        }
    
    def run_weekly(self) -> dict:
        """Run weekly digest pipeline (more comprehensive)"""
        print("\n" + "="*60)
        print("🔬 RESEARCH DIGEST - WEEKLY RUN")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Similar to daily but with 7 days lookback and more papers
        papers = self._collect_all_papers(days=7)
        
        if papers:
            papers = self.validator.validate_papers_batch(papers)
            papers = self.scorer.filter_and_score_papers(papers, min_score=10.0)
            papers = self.summarizer.summarize_papers_batch(papers, max_papers=30)
            
            intro = self.summarizer.generate_digest_intro(papers, period="weekly")
            html_digest = self.formatter.format_email_html(papers[:30], intro=intro, period="weekly")
            plain_digest = self.formatter.format_plaintext(papers[:30], intro=intro)
            
            self._save_digest(papers, "weekly")
            self._save_html(html_digest, "weekly")
            
            to_email = os.getenv("DIGEST_EMAIL", "leopold.monjoie@aalto.fi")
            subject = f"📚 Weekly Research Digest - Week of {datetime.now().strftime('%B %d, %Y')}"
            
            self.email_sender.send_digest(
                to_email=to_email,
                subject=subject,
                html_content=html_digest,
                plain_content=plain_digest
            )
        
        return {
            "status": "success" if papers else "no_papers",
            "count": len(papers) if papers else 0
        }
    
    def _collect_all_papers(self, days: int) -> list:
        """Collect papers from all sources"""
        all_papers = []
        
        # arXiv
        print("\n  [arXiv]")
        try:
            arxiv_papers = self.arxiv_collector.fetch_recent(days=days, max_results=100)
            all_papers.extend(arxiv_papers)
        except Exception as e:
            print(f"  Error collecting from arXiv: {e}")
        
        # OpenAlex
        print("\n  [OpenAlex]")
        try:
            openalex_papers = self.openalex_collector.fetch_recent(days=max(7, days), max_results=100)
            all_papers.extend(openalex_papers)
        except Exception as e:
            print(f"  Error collecting from OpenAlex: {e}")
        
        # NBER
        print("\n  [NBER]")
        try:
            nber_papers = self.nber_collector.fetch_recent(days=days, max_results=50)
            all_papers.extend(nber_papers)
        except Exception as e:
            print(f"  Error collecting from NBER: {e}")
        
        # Remove duplicates by title similarity
        unique_papers = self._deduplicate_papers(all_papers)
        
        print(f"\n  Total: {len(unique_papers)} unique papers collected")
        return unique_papers
    
    def _deduplicate_papers(self, papers: list) -> list:
        """Remove duplicate papers based on title"""
        seen_titles = set()
        unique = []
        
        for paper in papers:
            # Normalize title for comparison
            title_key = paper.title.lower().strip()[:100]
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique.append(paper)
        
        return unique
    
    def _save_digest(self, papers: list, period: str):
        """Save papers to JSON file"""
        filename = f"{period}_digest_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = self.data_dir / filename
        
        data = {
            "generated_at": datetime.now().isoformat(),
            "period": period,
            "paper_count": len(papers),
            "papers": [p.to_dict() for p in papers]
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"  Saved digest data to: {filepath}")
    
    def _save_html(self, html_content: str, period: str):
        """Save HTML digest to file"""
        filename = f"{period}_digest_{datetime.now().strftime('%Y%m%d')}.html"
        filepath = self.data_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"  Saved HTML digest to: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Research Digest Generator")
    parser.add_argument("--daily", action="store_true", help="Run daily digest")
    parser.add_argument("--weekly", action="store_true", help="Run weekly digest")
    parser.add_argument("--test", action="store_true", help="Run in test mode (no email)")
    
    args = parser.parse_args()
    
    digest = ResearchDigest()
    
    if args.weekly:
        result = digest.run_weekly()
    else:
        # Default to daily
        result = digest.run_daily()
    
    # Exit with appropriate code
    sys.exit(0 if result["status"] == "success" else 1)


if __name__ == "__main__":
    main()

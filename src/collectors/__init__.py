"""Paper collectors from various academic sources"""
from .arxiv_collector import ArxivCollector, Paper
from .openalex_collector import OpenAlexCollector
from .nber_collector import NBERCollector

__all__ = ['ArxivCollector', 'OpenAlexCollector', 'NBERCollector', 'Paper']

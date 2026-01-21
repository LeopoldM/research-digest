"""
Configuration loader for the Research Digest system
"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"


def load_yaml(filename: str) -> dict:
    """Load a YAML configuration file"""
    filepath = CONFIG_DIR / filename
    with open(filepath, 'r') as f:
        return yaml.safe_load(f)


@dataclass
class Config:
    """Main configuration class"""
    
    # API Keys (from environment variables)
    anthropic_api_key: Optional[str] = None
    sendgrid_api_key: Optional[str] = None
    
    # Email settings
    email_from: str = "digest@research-digest.com"
    email_to: str = "leopold.monjoie@aalto.fi"
    
    # Digest settings
    max_papers_daily: int = 15
    max_papers_weekly: int = 30
    
    def __post_init__(self):
        # Load from environment
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        

def get_config() -> Config:
    """Get the configuration instance"""
    return Config()


def get_keywords() -> Dict[str, List[str]]:
    """Load and flatten all keywords"""
    keywords_config = load_yaml("keywords.yaml")
    
    all_keywords = {
        'primary': [],
        'secondary': [],
        'tertiary': [],
        'exclude': keywords_config.get('exclude_keywords', [])
    }
    
    # Flatten nested keyword structures
    for category, keywords in keywords_config.get('primary_keywords', {}).items():
        all_keywords['primary'].extend(keywords)
        
    for category, keywords in keywords_config.get('secondary_keywords', {}).items():
        all_keywords['secondary'].extend(keywords)
        
    for category, keywords in keywords_config.get('tertiary_keywords', {}).items():
        all_keywords['tertiary'].extend(keywords)
    
    return all_keywords


def get_sources() -> dict:
    """Load sources configuration"""
    return load_yaml("sources.yaml")


def get_journals() -> List[str]:
    """Get flat list of all monitored journals"""
    sources = get_sources()
    journals = []
    for category, journal_list in sources.get('journals', {}).items():
        journals.extend(journal_list)
    return journals

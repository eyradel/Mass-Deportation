import os
from dotenv import load_dotenv

load_dotenv()
# Configuration file for Deportation News Searcher

# Google Custom Search API credentials
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Custom Search Engine ID (cx parameter)
# You need to create this at: https://cse.google.com/cse/
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID")

# Search settings
MAX_RESULTS = 100
RATE_LIMIT_DELAY = 1  # seconds between API calls

# Output settings
OUTPUT_FILENAME = "deportation_news_results.json"

# Search sites to include (government and news sources)
SEARCH_SITES = [
    "site:gov.uk",
    "site:ice.gov", 
    "site:homeoffice.gov.uk",
    "site:reuters.com",
    "site:bbc.com",
    "site:theguardian.com",
    "site:apnews.com",
    "site:cnn.com",
    "site:nytimes.com",
    "site:uscis.gov",
    "site:justice.gov",
    "site:state.gov"
]

# Deportation-related keywords to search for
DEPORTATION_KEYWORDS = [
    "deportation",
    "deportees", 
    "deported",
    "removal",
    "returned migrants",
    "forced return",
    "repatriation",
    "expulsion",
    "removal order",
    "deportation order",
    "immigration removal",
    "administrative removal"
]

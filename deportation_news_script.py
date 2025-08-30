import os
import json
import httpx
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass
import re
from datetime import datetime
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    SEARCH_ENGINE_ID: str = os.getenv("SEARCH_ENGINE_ID", "")

class DeportationDataExtractor:
    """Extracts deportation-specific information from text"""
    
    @staticmethod
    def extract_deportee_count(text: str) -> int:
        """Extract the number of deportees mentioned"""
        patterns = [
            r'(\d+)\s+(?:deportees?|deported|returned|removed)',
            r'(?:deportees?|deported|returned|removed)\s+(\d+)',
            r'(\d+)\s+(?:people|individuals?|migrants?)\s+(?:deported|returned|removed)',
            r'(\d+)\s+(?:on|aboard|in)\s+(?:deportation|removal|return)\s+(?:flight|transport)',
            r'(\d+)\s+(?:immigrants?|foreign nationals?)\s+(?:deported|returned|removed)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue
        return 0
    
    @staticmethod
    def extract_countries(text: str) -> Dict[str, str]:
        """Extract origin and destination countries"""
        countries = {"origin": None, "destination": None}
        
        # Origin country patterns (from USA)
        origin_patterns = [
            r'from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'deported\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'removed\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'returned\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'expelled\s+from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        # Destination country patterns (to)
        dest_patterns = [
            r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'arrived\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'landed\s+in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'returned\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'deported\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'sent\s+back\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                countries["origin"] = match.group(1).strip()
                break
        
        for pattern in dest_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                countries["destination"] = match.group(1).strip()
                break
        
        return countries
    
    @staticmethod
    def extract_agency(text: str) -> str:
        """Extract conducting US government agency"""
        agency_keywords = {
            "ICE": ["ice", "immigration and customs enforcement", "u.s. ice", "immigration customs enforcement"],
            "CBP": ["customs and border protection", "cbp", "u.s. border patrol", "border patrol"],
            "USCIS": ["uscis", "u.s. citizenship and immigration services", "citizenship immigration services"],
            "DOJ": ["department of justice", "doj", "justice department", "u.s. department of justice"],
            "DHS": ["department of homeland security", "dhs", "homeland security", "u.s. homeland security"],
            "Border Patrol": ["border patrol", "u.s. border patrol", "american border patrol"],
            "Immigration Court": ["immigration court", "immigration judge", "immigration hearing"],
            "Federal Court": ["federal court", "u.s. district court", "federal judge"]
        }
        
        text_lower = text.lower()
        for agency, keywords in agency_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return agency
        return "Unknown"
    
    @staticmethod
    def extract_transport_mode(text: str) -> str:
        """Extract transport mode used"""
        transport_keywords = {
            "charter_flight": ["charter flight", "chartered flight", "deportation flight", "ice flight", "removal flight"],
            "commercial_flight": ["commercial flight", "regular flight", "scheduled flight", "airline flight"],
            "bus": ["bus", "coach", "ground transport", "greyhound", "motor coach"],
            "ship": ["ship", "boat", "vessel", "ferry", "cargo ship"],
            "train": ["train", "railway", "rail transport", "amtrak"],
            "private_vehicle": ["private vehicle", "car", "van", "escorted", "under escort"]
        }
        
        text_lower = text.lower()
        for mode, keywords in transport_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return mode
        return "unknown"
    
    @staticmethod
    def analyze_urgency(text: str) -> str:
        """Analyze text for urgency indicators"""
        text_lower = text.lower()
        
        high_urgency = ["urgent", "immediate", "emergency", "crisis", "critical", "deadline", "expedited", "fast-track"]
        medium_urgency = ["soon", "quickly", "asap", "priority", "important", "accelerated", "rushed"]
        
        if any(word in text_lower for word in high_urgency):
            return "High"
        elif any(word in text_lower for word in medium_urgency):
            return "Medium"
        else:
            return "Low"
    
    @staticmethod
    def analyze_deportation_type(text: str) -> str:
        """Analyze text for deportation type"""
        text_lower = text.lower()
        
        if "mass" in text_lower or "group" in text_lower or "multiple" in text_lower or "batch" in text_lower:
            return "Mass"
        elif "individual" in text_lower or "single" in text_lower or "one person" in text_lower:
            return "Individual"
        elif "administrative" in text_lower or "paperwork" in text_lower or "overstay" in text_lower:
            return "Administrative"
        elif "criminal" in text_lower or "convicted" in text_lower or "felony" in text_lower or "crime" in text_lower:
            return "Criminal"
        elif "family" in text_lower or "parent" in text_lower or "child" in text_lower:
            return "Family"
        else:
            return "Group"
    
    @staticmethod
    def extract_legal_status(text: str) -> str:
        """Extract legal status of deportees"""
        text_lower = text.lower()
        
        if "undocumented" in text_lower or "illegal" in text_lower or "unauthorized" in text_lower:
            return "Undocumented"
        elif "legal" in text_lower or "lawful" in text_lower or "permanent resident" in text_lower:
            return "Legal"
        elif "visa" in text_lower or "temporary" in text_lower or "nonimmigrant" in text_lower:
            return "Temporary"
        elif "asylum" in text_lower or "refugee" in text_lower:
            return "Asylum Seeker"
        else:
            return "Unknown"

class GoogleSearchClient:
    def __init__(self, api_key: str, search_engine_id: str):
        self.api_key = api_key
        self.search_engine_id = search_engine_id
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def search(self, query: str, start_index: int = 1) -> Dict:
        params = {
            "key": self.api_key,
            "cx": self.search_engine_id,
            "q": query,
            "start": start_index,
            "num": 10,  # Google CSE max per request
            "dateRestrict": "m1",  # Last month
            "sort": "date"
        }
        
        try:
            with httpx.Client() as client:
                response = client.get(self.base_url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Search Error: {str(e)}")
            return {}

class DeportationNewsSearcher:
    def __init__(self):
        config = Config()
        self.search_client = GoogleSearchClient(config.GOOGLE_API_KEY, config.SEARCH_ENGINE_ID)
        self.data_extractor = DeportationDataExtractor()
        
        # US-focused deportation search keywords
        self.deportation_keywords = [
            "deportation from USA", "deportees from United States", "ICE deportation", "US deportation",
            "immigration removal USA", "deported from America", "US immigration enforcement",
            "ICE removal order", "US border deportation", "American deportation",
            "immigration court USA", "US immigration judge", "federal deportation",
            "ICE charter flight", "US removal flight", "immigration detention deportation"
        ]
        
        # US government and news sites to search
        self.search_sites = [
            "site:ice.gov", "site:uscis.gov", "site:justice.gov", "site:dhs.gov",
            "site:cbp.gov", "site:whitehouse.gov", "site:congress.gov",
            "site:reuters.com", "site:apnews.com", "site:cnn.com", "site:nytimes.com",
            "site:usatoday.com", "site:wsj.com", "site:latimes.com", "site:chicagotribune.com",
            "site:miamiherald.com", "site:houstonchronicle.com", "site:azcentral.com"
        ]
    
    def search_deportation_news(self, max_results_per_query: int = 20) -> List[Dict]:
        """Search for deportation news articles from USA"""
        print("🔍 Starting USA deportation news search...")
        print("Focus: Deportees being removed FROM the United States")
        
        all_results = []
        total_queries = len(self.deportation_keywords) * len(self.search_sites)
        query_count = 0
        
        for keyword in self.deportation_keywords:
            for site in self.search_sites:
                query = f"{keyword} {site}"
                print(f"Searching: {query}")
                
                # Search across multiple pages
                for start_index in range(1, max_results_per_query + 1, 10):
                    response = self.search_client.search(query, start_index)
                    if "items" in response:
                        all_results.extend(response["items"])
                
                query_count += 1
                print(f"Progress: {query_count}/{total_queries} queries completed")
        
        # Remove duplicates
        unique_results = {item['link']: item for item in all_results}.values()
        print(f"✅ Found {len(unique_results)} unique articles")
        
        return list(unique_results)
    
    def analyze_articles(self, articles: List[Dict]) -> List[Dict]:
        """Analyze articles and extract deportation data"""
        print("🔍 Analyzing USA deportation articles...")
        
        analyzed_data = []
        total_articles = len(articles)
        
        for i, article in enumerate(articles):
            analysis = self._analyze_article(
                article.get('snippet', ''),
                article.get('title', '')
            )
            
            if analysis:
                item_data = {
                    "source_url": article.get("link", ""),
                    "publisher_domain": urlparse(article.get("link", "")).netloc,
                    "headline": article.get("title", ""),
                    "snippet": article.get("snippet", ""),
                    **analysis
                }
                analyzed_data.append(item_data)
            
            # Progress indicator
            if (i + 1) % 10 == 0 or i == total_articles - 1:
                print(f"Progress: {i + 1}/{total_articles} articles analyzed")
        
        return analyzed_data
    
    def _analyze_article(self, text: str, title: str) -> Dict:
        """Analyze article using pattern matching and heuristics"""
        full_text = f"{title}\n{text}"
        
        # Extract basic deportation data
        deportee_count = self.data_extractor.extract_deportee_count(full_text)
        countries = self.data_extractor.extract_countries(full_text)
        agency = self.data_extractor.extract_agency(full_text)
        transport_mode = self.data_extractor.extract_transport_mode(full_text)
        urgency = self.data_extractor.analyze_urgency(full_text)
        deportation_type = self.data_extractor.analyze_deportation_type(full_text)
        legal_status = self.data_extractor.extract_legal_status(full_text)
        
        return {
            "deportee_count": deportee_count,
            "origin_country": countries["origin"] or "United States",  # Default to USA as origin
            "destination_country": countries["destination"],
            "conducting_agency": agency,
            "transport_mode": transport_mode,
            "date_discovered": datetime.utcnow().isoformat() + "Z",
            "Urgency": urgency,
            "DeportationType": deportation_type,
            "LegalStatus": legal_status
        }
    
    def save_results(self, results: List[Dict], filename: str = "usa_deportation_news_results.json"):
        """Save results to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(results)} results to {filename}")
    
    def save_csv(self, results: List[Dict], filename: str = "usa_deportation_news_results.csv"):
        """Save results to CSV file"""
        df = pd.DataFrame(results)
        df.to_csv(filename, index=False)
        print(f"💾 Saved {len(results)} results to {filename}")
    
    def display_summary(self, results: List[Dict]):
        """Display summary statistics for USA deportations"""
        if not results:
            print("❌ No results to display")
            return
        
        df = pd.DataFrame(results)
        
        print("\n" + "="*70)
        print("📊 USA DEPORTATION NEWS ANALYSIS SUMMARY")
        print("="*70)
        
        # Basic metrics
        print(f"Total Articles: {len(df)}")
        print(f"Total Deportees: {df['deportee_count'].sum()}")
        print(f"Average Deportees per Article: {df['deportee_count'].mean():.1f}")
        
        # Agency distribution
        print(f"\n🔍 US Agency Distribution:")
        agency_counts = df['conducting_agency'].value_counts()
        for agency, count in agency_counts.items():
            print(f"  {agency}: {count}")
        
        # Transport mode distribution
        print(f"\n🚗 Transport Mode Distribution:")
        transport_counts = df['transport_mode'].value_counts()
        for mode, count in transport_counts.items():
            print(f"  {mode}: {count}")
        
        # Urgency distribution
        print(f"\n⚡ Urgency Distribution:")
        urgency_counts = df['Urgency'].value_counts()
        for urgency, count in urgency_counts.items():
            print(f"  {urgency}: {count}")
        
        # Deportation type distribution
        print(f"\n📋 Deportation Type Distribution:")
        type_counts = df['DeportationType'].value_counts()
        for dtype, count in type_counts.items():
            print(f"  {dtype}: {count}")
        
        # Legal status distribution
        print(f"\n⚖️ Legal Status Distribution:")
        legal_counts = df['LegalStatus'].value_counts()
        for status, count in legal_counts.items():
            print(f"  {status}: {count}")
        
        # Top destination countries
        print(f"\n🌍 Top Destination Countries (where deportees are sent):")
        dest_counts = df['destination_country'].value_counts().head(10)
        for country, count in dest_counts.items():
            if country and country != "United States":
                print(f"  {country}: {count}")
        
        print("="*70)
    
    def display_sample_results(self, results: List[Dict], sample_size: int = 3):
        """Display sample results"""
        if not results:
            print("❌ No results to display")
            return
        
        print(f"\n📰 SAMPLE RESULTS (showing {min(sample_size, len(results))} articles):")
        print("-" * 70)
        
        for i, article in enumerate(results[:sample_size]):
            print(f"\n--- Article {i+1} ---")
            print(f"Headline: {article['headline']}")
            print(f"Source: {article['publisher_domain']}")
            print(f"Deportee Count: {article['deportee_count']}")
            print(f"From: {article['origin_country']}")
            print(f"To: {article['destination_country'] or 'Unknown'}")
            print(f"US Agency: {article['conducting_agency']}")
            print(f"Transport: {article['transport_mode']}")
            print(f"Type: {article['DeportationType']}")
            print(f"Urgency: {article['Urgency']}")
            print(f"Legal Status: {article['LegalStatus']}")
            print(f"Link: {article['source_url']}")

def main():
    """Main function to run the USA deportation news searcher"""
    print("🇺🇸 USA DEPORTATION NEWS SEARCHER")
    print("Focus: Deportees being removed FROM the United States")
    print("=" * 70)
    
    # Check configuration
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY not found in environment variables")
        print("Please create a .env file with your API credentials")
        return
    
    if not os.getenv("SEARCH_ENGINE_ID"):
        print("❌ Error: SEARCH_ENGINE_ID not found in environment variables")
        print("Please create a .env file with your Search Engine ID")
        return
    
    # Initialize searcher
    searcher = DeportationNewsSearcher()
    
    try:
        # Search for articles
        articles = searcher.search_deportation_news()
        
        if not articles:
            print("❌ No articles found. Try adjusting your search parameters.")
            return
        
        # Analyze articles
        analyzed_results = searcher.analyze_articles(articles)
        
        if not analyzed_results:
            print("❌ No valid USA deportation articles found after analysis.")
            return
        
        # Display summary
        searcher.display_summary(analyzed_results)
        
        # Display sample results
        searcher.display_sample_results(analyzed_results)
        
        # Save results
        searcher.save_results(analyzed_results)
        searcher.save_csv(analyzed_results)
        
        print(f"\n✅ Successfully processed {len(analyzed_results)} USA deportation news articles!")
        print("Results saved to:")
        print("  - usa_deportation_news_results.json")
        print("  - usa_deportation_news_results.csv")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Search interrupted by user")
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")

if __name__ == "__main__":
    main()

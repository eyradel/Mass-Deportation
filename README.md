# Deportation News Searcher

A Python-based system that uses the Google Custom Search API (CSE) to search for deportation-related news articles from government and news websites. The system extracts structured data from search results and saves them in JSON format.

## Features

- **Comprehensive Search**: Searches across multiple government and news websites
- **Intelligent Data Extraction**: Automatically extracts key information from search results
- **Structured Output**: Saves results in a standardized JSON format
- **Rate Limiting**: Built-in API rate limiting to avoid quota issues
- **Duplicate Removal**: Automatically removes duplicate articles based on URL

## Extracted Fields

For each article found, the system extracts:

- `source_url`: The article link
- `publisher_domain`: Domain of the source website
- `headline`: Article title
- `snippet`: Short summary from Google search results
- `date_discovered`: Current datetime when the article was found
- `deportee_count`: Number of deportees mentioned (extracted using regex)
- `origin_country`: Country deportees are being removed from
- `destination_country`: Country deportees are sent to
- `conducting_agency`: Government agency conducting the deportation
- `transport_mode`: Mode of transportation used

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Create Google Custom Search Engine

1. Go to [Google Custom Search Engine](https://cse.google.com/cse/)
2. Click "Create a search engine"
3. Enter any website in the "Sites to search" field (e.g., `example.com`)
4. Give your search engine a name
5. Click "Create"
6. Copy the **Search Engine ID** (cx parameter) from the setup page

### 3. Configure the System

Edit `config.py` and update the `SEARCH_ENGINE_ID`:

```python
SEARCH_ENGINE_ID = "YOUR_ACTUAL_SEARCH_ENGINE_ID_HERE"
```

The API key is already configured in the file.

### 4. Run the System

```bash
python deportation_searcher_simple.py
```

## Usage

### Basic Usage

The system will automatically:
1. Search across all configured websites using deportation-related keywords
2. Extract relevant information from each search result
3. Save results to `deportation_news_results.json`
4. Display sample results in the console

### Customization

You can customize the search by editing `config.py`:

- **Search Sites**: Add or remove websites to search
- **Keywords**: Modify deportation-related search terms
- **Output Settings**: Change output filename and result limits
- **Rate Limiting**: Adjust delay between API calls

### Output Format

Results are saved in JSON format:

```json
{
  "source_url": "https://example.com/news/ghana-receives-45-deportees",
  "publisher_domain": "example.com",
  "headline": "Ghana receives 45 deportees from UK",
  "snippet": "A charter flight carrying 45 Ghanaians deported from the UK landed in Accra yesterday.",
  "date_discovered": "2025-01-30T15:20:00Z",
  "deportee_count": 45,
  "origin_country": "United Kingdom",
  "destination_country": "Ghana",
  "conducting_agency": "UK Home Office",
  "transport_mode": "charter_flight"
}
```

## Supported Websites

The system searches across:

### Government Sites
- UK Government (gov.uk)
- US Immigration and Customs Enforcement (ice.gov)
- UK Home Office (homeoffice.gov.uk)
- US Citizenship and Immigration Services (uscis.gov)
- US Department of Justice (justice.gov)
- US State Department (state.gov)

### News Sites
- Reuters (reuters.com)
- BBC News (bbc.com)
- The Guardian (theguardian.com)
- Associated Press (apnews.com)
- CNN (cnn.com)
- The New York Times (nytimes.com)

## Transport Mode Detection

The system automatically detects transport modes:
- `charter_flight`: Charter flights, deportation flights
- `commercial_flight`: Regular commercial flights
- `bus`: Bus or coach transport
- `ship`: Ship, boat, or ferry transport
- `train`: Railway transport
- `unknown`: When transport mode cannot be determined

## Agency Detection

Recognized government agencies:
- UK Home Office
- ICE (US Immigration and Customs Enforcement)
- Border Force (UK)
- CBP (US Customs and Border Protection)
- USCIS (US Citizenship and Immigration Services)
- DOJ (US Department of Justice)

## Country Normalization

The system normalizes country names to standard formats:
- "UK", "Britain", "England" → "United Kingdom"
- "USA", "America", "US" → "United States"
- And many more common variations

## API Quota Management

- Google Custom Search API has daily quotas
- Built-in rate limiting (1 second between requests)
- Configurable delays in `config.py`
- Results are limited to recent articles (last month)

## Error Handling

The system includes comprehensive error handling:
- API rate limit errors
- Network connection issues
- Data extraction failures
- Invalid search results

## Troubleshooting

### Common Issues

1. **"Please set your Search Engine ID"**
   - Follow the setup instructions to create a Custom Search Engine
   - Update the `SEARCH_ENGINE_ID` in `config.py`

2. **API Quota Exceeded**
   - Wait until the next day for quota reset
   - Reduce the number of search sites or keywords
   - Increase the rate limiting delay

3. **No Results Found**
   - Check if your search terms are too specific
   - Verify the websites you're searching are accessible
   - Try different deportation-related keywords

### Getting Help

If you encounter issues:
1. Check the console output for error messages
2. Verify your API key and Search Engine ID
3. Ensure all dependencies are installed
4. Check your internet connection

## License

This project is provided as-is for educational and research purposes.

## Contributing

Feel free to:
- Add more search websites
- Improve the data extraction algorithms
- Add new deportation-related keywords
- Enhance the country and agency detection
- Optimize the search strategies


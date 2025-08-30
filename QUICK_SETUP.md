# 🚀 Quick Setup Guide

## Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

## Step 2: Create Google Custom Search Engine
1. Go to [https://cse.google.com/cse/](https://cse.google.com/cse/)
2. Click "Create a search engine"
3. Enter any website (e.g., `example.com`) in "Sites to search"
4. Give it a name (e.g., "Deportation News Searcher")
5. Click "Create"
6. **Copy the Search Engine ID** (cx parameter) from the setup page

## Step 3: Create .env File
Create a file named `.env` in your project directory with this content:
```env
GOOGLE_API_KEY=AIzaSyBJaeu2Jp5cEtAzgTXp7o_-QByBzYg0uRY
SEARCH_ENGINE_ID=YOUR_ACTUAL_SEARCH_ENGINE_ID_HERE
```

**Replace `YOUR_ACTUAL_SEARCH_ENGINE_ID_HERE` with the ID you copied in Step 2.**

## Step 4: Test Your Setup
```bash
python test_setup.py
```

## Step 5: Run the Searcher
```bash
python deportation_searcher_simple.py
```

## 🔍 What You'll Get
- **JSON file** with deportation news articles
- **Structured data** including deportee counts, countries, agencies, transport modes
- **Automatic extraction** from government and news websites
- **Rate-limited API calls** to avoid quota issues

## 📁 Files Created
- `deportation_news_results.json` - Your extracted data
- Console output showing sample results

## 🆘 Need Help?
- Check the console output for error messages
- Verify your `.env` file exists and has correct values
- Ensure all dependencies are installed
- Run `python test_setup.py` to diagnose issues


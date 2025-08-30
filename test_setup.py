#!/usr/bin/env python3
"""
Test script to verify the deportation news searcher setup
"""

import os
import requests
import json

def test_environment_variables():
    """Test if environment variables are properly set"""
    print("Testing environment variables...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("   Please create a .env file with your credentials")
        print("   Use env_template.txt as a reference")
        return False
    
    # Try to import config (this will load the .env file)
    try:
        from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID
    except ImportError as e:
        print(f"❌ Error importing config: {e}")
        return False
    
    # Check API key
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == "YOUR_API_KEY_HERE":
        print("❌ GOOGLE_API_KEY not set in .env file")
        return False
    else:
        print("✅ GOOGLE_API_KEY configured")
    
    # Check Search Engine ID
    if not SEARCH_ENGINE_ID or SEARCH_ENGINE_ID == "YOUR_SEARCH_ENGINE_ID_HERE":
        print("❌ SEARCH_ENGINE_ID not set in .env file")
        print("   Please create a Google Custom Search Engine and get the ID")
        return False
    else:
        print("✅ SEARCH_ENGINE_ID configured")
    
    return True

def test_api_connection():
    """Test if the Google Custom Search API is accessible"""
    print("\nTesting Google Custom Search API connection...")
    
    try:
        from config import GOOGLE_API_KEY, SEARCH_ENGINE_ID
    except ImportError:
        print("❌ Cannot import config - check your .env file")
        return False
    
    # Test API with a simple search
    test_url = "https://www.googleapis.com/customsearch/v1"
    test_params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': 'test',
        'num': 1
    }
    
    try:
        response = requests.get(test_url, params=test_params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data:
                print("✅ API connection successful!")
                print(f"   Found {len(data['items'])} test results")
                return True
            else:
                print("❌ API returned no results")
                return False
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network Error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parse Error: {e}")
        return False

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("\nTesting dependencies...")
    
    try:
        import requests
        print("✅ requests library installed")
    except ImportError:
        print("❌ requests library not installed")
        print("   Run: pip install requests")
        return False
    
    try:
        import urllib3
        print("✅ urllib3 library installed")
    except ImportError:
        print("❌ urllib3 library not installed")
        print("   Run: pip install urllib3")
        return False
    
    try:
        import python_dotenv
        print("✅ python-dotenv library installed")
    except ImportError:
        print("❌ python-dotenv library not installed")
        print("   Run: pip install python-dotenv")
        return False
    
    try:
        from datetime import datetime
        print("✅ datetime library available")
    except ImportError:
        print("❌ datetime library not available")
        return False
    
    try:
        import re
        print("✅ re library available")
    except ImportError:
        print("❌ re library not available")
        return False
    
    try:
        from urllib.parse import urlparse
        print("✅ urllib.parse library available")
    except ImportError:
        print("❌ urllib.parse library not available")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("DEPORTATION NEWS SEARCHER - SETUP TEST")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test dependencies
    if not test_dependencies():
        all_tests_passed = False
    
    # Test environment variables
    if not test_environment_variables():
        all_tests_passed = False
    
    # Test API connection (only if config is correct)
    if all_tests_passed:
        if not test_api_connection():
            all_tests_passed = False
    
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED!")
        print("Your setup is ready to use.")
        print("\nTo run the deportation news searcher:")
        print("python deportation_searcher_simple.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("\nTo fix the issues:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Create a .env file with your credentials (use env_template.txt)")
        print("3. Get your Search Engine ID from: https://cse.google.com/cse/")
        print("4. Run this test again: python test_setup.py")
    print("=" * 60)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Simple script to run the CoinMarketCap Selenium Scraper
"""

from selenium_coinmarketcap_scraper import CoinMarketCapSeleniumScraper

def main():
    print("🚀 CoinMarketCap Selenium Scraper")
    print("=" * 40)
    
    # Choose mode
    print("\nChoose execution mode:")
    print("1. Normal mode (with browser visible)")
    print("2. Headless mode (background execution)")
    
    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        headless = choice == "2"
        
        if choice not in ["1", "2"]:
            print("Invalid choice. Using normal mode.")
            headless = False
        
        print(f"\nStarting scraper in {'headless' if headless else 'normal'} mode...")
        print("This may take several minutes depending on the number of coins.")
        print("The script will:")
        print("- Fetch top 100 non-stablecoin cryptocurrencies")
        print("- Navigate to each coin's detail page")
        print("- Extract SVG charts with maximum timeframe and log scale")
        print("- Generate an HTML table with embedded charts")
        print("- Save all data to timestamped files")
        
        # Initialize and run scraper
        scraper = CoinMarketCapSeleniumScraper(headless=headless, timeout=30)
        scraper.run(headless=headless)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()

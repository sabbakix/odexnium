# CoinMarketCap Selenium Scraper

A Python script that uses Selenium WebDriver to scrape cryptocurrency data from CoinMarketCap, extract SVG price charts with maximum timeframe and log scale, and generate an HTML table with embedded visualizations.

## Features

- 🚀 **Selenium-based scraping** for dynamic content
- 📊 **SVG chart extraction** with maximum timeframe and log scale
- 🎯 **Stablecoin filtering** to exclude USDT, USDC, BUSD, etc.
- 📱 **Responsive HTML output** with modern styling
- 💾 **Multiple output formats** (JSON, HTML, individual SVG files)
- 🛡️ **Anti-detection measures** to avoid blocking
- ⚡ **Configurable options** (headless mode, timeouts)

## Requirements

- Python 3.7+
- Chrome browser installed
- Internet connection

## Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify installation:**
   ```bash
   python -c "import selenium; import webdriver_manager; print('✅ Dependencies installed successfully')"
   ```

## Usage

### Method 1: Interactive Script
```bash
python run_selenium_scraper.py
```
This will prompt you to choose between normal mode (visible browser) or headless mode (background execution).

### Method 2: Direct Script Execution
```bash
# Normal mode (with browser visible)
python selenium_coinmarketcap_scraper.py

# Headless mode (background execution)
python selenium_coinmarketcap_scraper.py --headless

# Custom timeout
python selenium_coinmarketcap_scraper.py --timeout 45
```

### Method 3: Import as Module
```python
from selenium_coinmarketcap_scraper import CoinMarketCapSeleniumScraper

# Initialize scraper
scraper = CoinMarketCapSeleniumScraper(headless=True, timeout=30)

# Run scraping
scraper.run(headless=True)
```

## Output Files

The script generates several output files with timestamps:

1. **`coins_data_selenium_YYYYMMDD_HHMMSS.json`**
   - Raw coin data in JSON format
   - Includes coin information and SVG chart content

2. **`cryptocurrency_charts_YYYYMMDD_HHMMSS.html`**
   - Complete HTML table with embedded charts
   - Responsive design with modern styling
   - Statistics and metadata

3. **`svg_charts_YYYYMMDD_HHMMSS/`** (directory)
   - Individual SVG files for each coin
   - Named as `{slug}_{id}.svg`

## How It Works

### Phase 1: Setup & Navigation
- Initializes Chrome WebDriver with anti-detection options
- Navigates to CoinMarketCap homepage
- Waits for dynamic content to load

### Phase 2: Coin Discovery
- Extracts top 100 cryptocurrencies from the main page
- Filters out stablecoins using keyword detection
- Collects profile URLs and basic information

### Phase 3: Chart Extraction
- Navigates to each coin's detail page
- Attempts to set maximum timeframe (MAX/ALL)
- Enables log scale visualization
- Extracts SVG chart content

### Phase 4: Data Processing
- Creates responsive HTML table
- Embeds SVG charts directly into table cells
- Generates statistics and metadata

### Phase 5: File Output
- Saves data in multiple formats
- Creates timestamped files for organization
- Provides progress feedback

## Configuration Options

### WebDriver Options
- `headless`: Run browser in background (default: False)
- `timeout`: Maximum wait time for elements (default: 30 seconds)

### Anti-Detection Features
- Custom user agent
- Disabled automation flags
- Realistic delays between requests
- Browser fingerprint masking

### Chart Settings
- Maximum timeframe selection (MAX/ALL/1Y/6M)
- Log scale enablement
- Multiple fallback selectors for different page layouts

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**
   ```
   Solution: The script uses webdriver-manager to automatically download and manage ChromeDriver
   ```

2. **Page elements not found**
   ```
   Solution: CoinMarketCap may have updated their layout. The script includes multiple fallback selectors.
   ```

3. **Rate limiting/blocking**
   ```
   Solution: The script includes delays and anti-detection measures. Try running in headless mode.
   ```

4. **SVG charts not extracted**
   ```
   Solution: Some coins may not have charts available. The script will continue with other coins.
   ```

### Performance Tips

- Use headless mode for faster execution
- Increase timeout for slower connections
- Run during off-peak hours to avoid rate limiting
- Monitor system resources during execution

## Technical Details

### Dependencies
- `selenium`: Web automation framework
- `webdriver-manager`: Automatic ChromeDriver management
- `beautifulsoup4`: HTML parsing
- `requests`: HTTP requests (fallback)

### Browser Requirements
- Chrome browser (latest version recommended)
- Sufficient RAM (2GB+ recommended)
- Stable internet connection

### File Structure
```
project/
├── selenium_coinmarketcap_scraper.py  # Main scraper script
├── run_selenium_scraper.py            # Interactive runner
├── requirements.txt                   # Dependencies
├── README_selenium_scraper.md         # This file
└── output_files/                      # Generated files
    ├── coins_data_selenium_*.json
    ├── cryptocurrency_charts_*.html
    └── svg_charts_*/
```

## Limitations

- **Dynamic content**: CoinMarketCap uses JavaScript rendering, requiring Selenium
- **Rate limiting**: May be blocked if too many requests are made
- **Layout changes**: Website updates may break selectors
- **Chart availability**: Not all coins have charts available
- **Processing time**: Can take 10-30 minutes for 100 coins

## Contributing

To improve the scraper:

1. **Add new selectors** for different page layouts
2. **Enhance anti-detection** measures
3. **Optimize performance** with better waiting strategies
4. **Add more output formats** (CSV, Excel, etc.)
5. **Improve error handling** and recovery

## License

This project is for educational purposes. Please respect CoinMarketCap's terms of service and rate limits.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the console output for error messages
3. Ensure all dependencies are installed
4. Verify Chrome browser is up to date

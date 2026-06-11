# CoinMarketCap Top 100 Cryptocurrencies Scraper

This Python script scrapes the top 100 cryptocurrencies from [CoinMarketCap](https://coinmarketcap.com/) and creates an HTML table with their names, profile links, and 7-day price charts.

## Features

- Scrapes the top 100 cryptocurrencies by market cap
- Extracts coin names and profile links
- Captures 7-day price chart SVG images
- Creates a beautiful HTML table with the data
- Saves data in both HTML and JSON formats
- Includes proper error handling and user-agent headers

## Requirements

- Python 3.6 or higher
- Internet connection

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python scrape_coinmarketcap.py
```

The script will:
1. Fetch data from CoinMarketCap
2. Process the top 100 cryptocurrencies
3. Create an HTML file: `top_100_cryptocurrencies.html`
4. Save raw data as JSON: `coins_data.json`

## Output Files

### `top_100_cryptocurrencies.html`
A complete HTML page with:
- Responsive table design
- Clickable coin names linking to their profiles
- Embedded 7-day price charts
- Timestamp of when data was scraped

### `coins_data.json`
Raw data in JSON format containing:
- Rank
- Coin name
- Profile link
- SVG chart URL

## Features of the HTML Output

- **Responsive Design**: Works on desktop and mobile devices
- **Interactive Elements**: Hover effects and clickable links
- **Professional Styling**: Clean, modern appearance
- **Chart Integration**: Embedded SVG price charts
- **External Links**: Direct links to CoinMarketCap profiles

## Notes

- The script respects CoinMarketCap's robots.txt and uses proper headers
- Includes error handling for network issues and parsing problems
- SVG charts are loaded directly from CoinMarketCap's CDN
- Data is timestamped for reference

## Legal Notice

This script is for educational purposes. Please respect CoinMarketCap's terms of service and rate limiting. Consider adding delays between requests if making multiple calls.

## Troubleshooting

If you encounter issues:

1. **Network errors**: Check your internet connection
2. **Parsing errors**: CoinMarketCap may have updated their HTML structure
3. **Missing charts**: Some coins may not have chart data available
4. **Rate limiting**: Add delays between requests if needed

## Example Output

The generated HTML will display a table like:

| Rank | Name | 7-Day Price Chart |
|------|------|-------------------|
| 1 | Bitcoin | [SVG Chart] |
| 2 | Ethereum | [SVG Chart] |
| ... | ... | ... |

Each coin name is clickable and links to its CoinMarketCap profile page.

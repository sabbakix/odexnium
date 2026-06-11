import requests
from bs4 import BeautifulSoup
import time
import json
import re
from urllib.parse import urljoin

def get_coin_chart_url(coin_id: int, slug: str) -> str:
    """
    Get the maximum timeframe chart URL for a specific coin.
    Tries different timeframes: MAX, ALL, 1Y, 6M, 3M, 1M
    """
    timeframes = ['MAX', 'ALL', '1Y', '6M', '3M', '1M']
    
    for timeframe in timeframes:
        # Try different URL patterns for maximum timeframe charts
        chart_urls = [
            f"https://s3.coinmarketcap.com/generated/sparklines/web/{timeframe.lower()}/2781/{coin_id}.svg",
            f"https://s3.coinmarketcap.com/generated/sparklines/web/{timeframe}/2781/{coin_id}.svg",
            f"https://s3.coinmarketcap.com/generated/sparklines/web/{timeframe.lower()}/2781/{coin_id}.svg",
        ]
        
        for url in chart_urls:
            try:
                response = requests.head(url, timeout=10)
                if response.status_code == 200:
                    print(f"  Found {timeframe} chart for {coin_id}")
                    return url
                time.sleep(0.1)  # Small delay to avoid rate limiting
            except:
                continue
    
    # Fallback to 7D if no max timeframe found
    print(f"  Using 7D fallback for {coin_id}")
    return f"https://s3.coinmarketcap.com/generated/sparklines/web/7d/2781/{coin_id}.svg"

def scrape_coinmarketcap():
    """
    Scrape the top 100 coins from CoinMarketCap and extract their names, 
    profile links, and SVG graph URLs.
    """
    url = "https://coinmarketcap.com/"
    
    # Headers to mimic a real browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        print("Fetching CoinMarketCap data...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Prefer parsing Next.js embedded data since the table is rendered client-side
        next_data_script = soup.find('script', id='__NEXT_DATA__')

        coins_data: list[dict] = []

        def traverse_and_collect(obj):
            nonlocal coins_data
            if isinstance(obj, dict):
                # Heuristic: objects that look like coins have at least id, name, slug
                if {'id', 'name', 'slug'}.issubset(set(obj.keys())):
                    coin_id = obj.get('id')
                    name = obj.get('name')
                    slug = obj.get('slug')
                    cmc_rank = obj.get('cmcRank') or obj.get('rank')
                    tags = obj.get('tags') if isinstance(obj.get('tags'), list) else None
                    if isinstance(coin_id, int) and isinstance(name, str) and isinstance(slug, str):
                        coins_data.append({
                            'id': coin_id,
                            'name': name,
                            'slug': slug,
                            'cmc_rank': cmc_rank,
                            'tags': tags
                        })
                for value in obj.values():
                    traverse_and_collect(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse_and_collect(item)

        if next_data_script and next_data_script.string:
            try:
                next_data_json = json.loads(next_data_script.string)
                traverse_and_collect(next_data_json)
            except Exception:
                pass

        # Fallback: try to parse any data attributes containing JSON (defensive)
        if not coins_data:
            for script in soup.find_all('script'):
                if script.string and 'cryptoCurrency' in script.string and 'slug' in script.string:
                    try:
                        # Extract first JSON object substring conservatively
                        text = script.string
                        start = text.find('{')
                        end = text.rfind('}')
                        if start != -1 and end != -1 and end > start:
                            maybe_json = text[start:end+1]
                            data = json.loads(maybe_json)
                            traverse_and_collect(data)
                            if coins_data:
                                break
                    except Exception:
                        continue

        if not coins_data:
            print("Unable to locate embedded coin data on the page.")
            return []

        # Helper: detect stablecoins via tags or name/slug patterns
        stable_patterns = re.compile(r"(^|[^a-z])(usd|usdt|usdc|usdd|usdp|gusd|pyusd|tusd|fdusd|usde|dai|busd|frax|lusd|pax|paxg|tether|trueusd|first[- ]digital[- ]usd|paypal[- ]usd|binance[- ]usd|world[- ]liberty[- ]financial[- ]usd)([^a-z]|$)", re.IGNORECASE)

        def is_stablecoin(coin: dict) -> bool:
            tags = coin.get('tags') or []
            if isinstance(tags, list) and any('stable' in str(t).lower() for t in tags):
                return True
            name = coin.get('name', '')
            slug = coin.get('slug', '')
            if stable_patterns.search(name.lower()) or stable_patterns.search(slug.lower()):
                return True
            return False

        # Deduplicate by id while preserving first occurrence
        seen = set()
        unique: list[dict] = []
        for c in coins_data:
            if c['id'] not in seen:
                seen.add(c['id'])
                unique.append(c)

        # Sort by cmc_rank if available; else keep original order
        unique.sort(key=lambda x: (x['cmc_rank'] if isinstance(x.get('cmc_rank'), (int, float)) else float('inf')))

        # Filter out stablecoins, then take top 100 non-stable
        filtered = [c for c in unique if not is_stablecoin(c)]
        top = filtered[:100]

        # Build final structure with profile link and max timeframe SVG URL
        final: list[dict] = []
        for idx, c in enumerate(top, 1):
            coin_id = c['id']
            slug = c['slug']
            name = c['name']
            profile_link = f"https://coinmarketcap.com/currencies/{slug}/"
            
            print(f"Processing {idx}: {name} (ID: {coin_id})")
            # Get maximum timeframe chart URL
            svg_url = get_coin_chart_url(coin_id, slug)
            
            final.append({
                'rank': idx,
                'name': name,
                'profile_link': profile_link,
                'svg_url': svg_url
            })

        print(f"Successfully processed {len(final)} coins with maximum timeframe charts.")

        return final
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def create_html_table(coins_data):
    """
    Create an HTML table with the coin data and SVG graphs.
    """
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top 100 Cryptocurrencies - CoinMarketCap</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f8f9fa;
            font-weight: bold;
            color: #333;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .coin-name {
            font-weight: bold;
            color: #007bff;
            text-decoration: none;
        }
        .coin-name:hover {
            text-decoration: underline;
        }
        .rank {
            font-weight: bold;
            color: #666;
            text-align: center;
        }
        .chart-container {
            width: 200px;
            height: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .chart-container img {
            max-width: 100%;
            max-height: 100%;
        }
        .no-chart {
            color: #999;
            font-style: italic;
        }
        .timestamp {
            text-align: center;
            color: #666;
            font-size: 12px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Top 100 Cryptocurrencies (Excluding Stablecoins)</h1>
        <p style="text-align: center; color: #666;">Data from <a href="https://coinmarketcap.com/" target="_blank">CoinMarketCap</a> - Maximum Timeframe Charts</p>
        
        <table>
            <thead>
                <tr>
                    <th>Rank</th>
                    <th>Name</th>
                    <th>Maximum Timeframe Price Chart</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for coin in coins_data:
        chart_html = ""
        if coin['svg_url']:
            chart_html = f'<div class="chart-container"><img src="{coin["svg_url"]}" alt="{coin["name"]} max timeframe chart" title="{coin["name"]} maximum timeframe price chart"></div>'
        else:
            chart_html = '<div class="chart-container"><span class="no-chart">No chart available</span></div>'
        
        html_content += f"""
                <tr>
                    <td class="rank">{coin['rank']}</td>
                    <td><a href="{coin['profile_link']}" class="coin-name" target="_blank">{coin['name']}</a></td>
                    <td>{chart_html}</td>
                </tr>
"""
    
    html_content += """
            </tbody>
        </table>
        
        <div class="timestamp">
            Last updated: """ + time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()) + """
        </div>
    </div>
</body>
</html>
"""
    
    return html_content

def main():
    """
    Main function to scrape data and create HTML file.
    """
    print("Starting CoinMarketCap scraper...")
    
    # Scrape the data
    coins_data = scrape_coinmarketcap()
    
    if not coins_data:
        print("No data was scraped. Exiting.")
        return
    
    print(f"Successfully scraped {len(coins_data)} coins.")
    
    # Create HTML content
    html_content = create_html_table(coins_data)
    
    # Save to file
    filename = "top_100_cryptocurrencies.html"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML file created successfully: {filename}")
    except Exception as e:
        print(f"Error saving file: {e}")
    
    # Also save the raw data as JSON for reference
    json_filename = "coins_data.json"
    try:
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(coins_data, f, indent=2, ensure_ascii=False)
        print(f"JSON data saved: {json_filename}")
    except Exception as e:
        print(f"Error saving JSON file: {e}")

if __name__ == "__main__":
    main()

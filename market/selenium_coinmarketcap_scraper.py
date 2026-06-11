import time
import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class CoinMarketCapSeleniumScraper:
    def __init__(self, headless: bool = False, timeout: int = 30):
        """
        Initialize the CoinMarketCap scraper with Selenium.
        
        Args:
            headless: Run browser in headless mode
            timeout: Timeout for webdriver operations
        """
        self.timeout = timeout
        self.coins_data = []
        self.driver = None
        self.setup_driver(headless)
        
    def setup_driver(self, headless: bool):
        """Setup Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if headless:
            chrome_options.add_argument("--headless")
        
        # Add options to avoid detection
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set user agent
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(10)
            print("✅ WebDriver initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize WebDriver: {e}")
            raise
    
    def is_stablecoin(self, coin: Dict) -> bool:
        """
        Check if a coin is a stablecoin based on its tags or name.
        
        Args:
            coin: Dictionary containing coin information
            
        Returns:
            True if the coin is a stablecoin, False otherwise
        """
        stablecoin_keywords = [
            'usdt', 'usdc', 'busd', 'dai', 'tusd', 'usdp', 'usdd', 'frax', 'gusd', 'husd',
            'stablecoin', 'stable', 'peg', 'tethered'
        ]
        
        # Check tags
        tags = coin.get('tags', [])
        if isinstance(tags, list):
            for tag in tags:
                if isinstance(tag, str) and any(keyword in tag.lower() for keyword in stablecoin_keywords):
                    return True
        
        # Check name
        name = coin.get('name', '').lower()
        if any(keyword in name for keyword in stablecoin_keywords):
            return True
        
        # Check slug
        slug = coin.get('slug', '').lower()
        if any(keyword in slug for keyword in stablecoin_keywords):
            return True
        
        return False
    
    def get_top_100_coins(self) -> List[Dict]:
        """
        Scrape the top 100 coins from CoinMarketCap homepage.
        
        Returns:
            List of dictionaries containing coin information
        """
        print("🔍 Fetching top 100 coins from CoinMarketCap...")
        
        try:
            self.driver.get("https://coinmarketcap.com/")
            time.sleep(3)  # Wait for page to load
            
            # Wait for the table to be present
            wait = WebDriverWait(self.driver, self.timeout)
            table = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table[class*='table']")))
            
            # Scroll to load more coins if needed
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Parse the page with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Try to extract data from Next.js embedded data
            next_data_script = soup.find('script', id='__NEXT_DATA__')
            coins_data = []
            
            if next_data_script and next_data_script.string:
                try:
                    next_data_json = json.loads(next_data_script.string)
                    coins_data = self.extract_coins_from_json(next_data_json)
                except json.JSONDecodeError:
                    print("⚠️ Failed to parse Next.js data, falling back to table parsing")
            
            # Fallback: parse table directly
            if not coins_data:
                coins_data = self.parse_table_directly(soup)
            
            # Filter stablecoins and limit to top 100
            non_stablecoins = [coin for coin in coins_data if not self.is_stablecoin(coin)]
            non_stablecoins = non_stablecoins[:100]
            
            print(f"✅ Found {len(non_stablecoins)} non-stablecoin coins")
            return non_stablecoins
            
        except Exception as e:
            print(f"❌ Error fetching top 100 coins: {e}")
            return []
    
    def extract_coins_from_json(self, data: Dict) -> List[Dict]:
        """Extract coin data from Next.js JSON data."""
        coins = []
        
        def traverse_and_collect(obj):
            if isinstance(obj, dict):
                if {'id', 'name', 'slug'}.issubset(set(obj.keys())):
                    coin_id = obj.get('id')
                    name = obj.get('name')
                    slug = obj.get('slug')
                    cmc_rank = obj.get('cmcRank') or obj.get('rank')
                    tags = obj.get('tags') if isinstance(obj.get('tags'), list) else []
                    
                    if isinstance(coin_id, int) and isinstance(name, str) and isinstance(slug, str):
                        coins.append({
                            'id': coin_id,
                            'name': name,
                            'slug': slug,
                            'cmc_rank': cmc_rank,
                            'tags': tags,
                            'profile_url': f"https://coinmarketcap.com/currencies/{slug}/"
                        })
                
                for value in obj.values():
                    traverse_and_collect(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse_and_collect(item)
        
        traverse_and_collect(data)
        return coins
    
    def parse_table_directly(self, soup: BeautifulSoup) -> List[Dict]:
        """Parse coin data directly from the HTML table."""
        coins = []
        table = soup.find('table')
        
        if not table:
            return coins
        
        rows = table.find_all('tr')[1:]  # Skip header row
        
        for row in rows[:100]:  # Limit to top 100
            try:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    # Extract rank
                    rank_cell = cells[0]
                    rank_text = rank_cell.get_text(strip=True)
                    rank = int(rank_text) if rank_text.isdigit() else None
                    
                    # Extract name and link
                    name_cell = cells[1]
                    name_link = name_cell.find('a')
                    if name_link:
                        name = name_link.get_text(strip=True)
                        href = name_link.get('href')
                        slug = href.split('/')[-2] if href else None
                        
                        coins.append({
                            'id': len(coins) + 1,  # Fallback ID
                            'name': name,
                            'slug': slug,
                            'cmc_rank': rank,
                            'tags': [],
                            'profile_url': urljoin("https://coinmarketcap.com", href) if href else None
                        })
            except Exception as e:
                print(f"⚠️ Error parsing table row: {e}")
                continue
        
        return coins
    
    def get_coin_chart_svg(self, coin: Dict) -> Optional[str]:
        """
        Navigate to coin detail page and extract SVG chart with maximum timeframe and log scale.
        
        Args:
            coin: Dictionary containing coin information
            
        Returns:
            SVG content as string or None if failed
        """
        if not coin.get('profile_url'):
            print(f"⚠️ No profile URL for {coin['name']}")
            return None
        
        try:
            print(f"📊 Processing {coin['name']} ({coin['slug']})...")
            
            # Navigate to coin detail page
            self.driver.get(coin['profile_url'])
            time.sleep(3)
            
            # Wait for page to load
            wait = WebDriverWait(self.driver, self.timeout)
            
            # Try to find and interact with chart controls via <li> tabs
            try:
                def _click_li_tab(label_text_upper: str, data_index_value: str) -> bool:
                    # Robust XPaths for matching <li data-index="tab-X"><h5>Label</h5></li>
                    uppercase = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    lowercase = "abcdefghijklmnopqrstuvwxyz"
                    xpaths = [
                        f"//li[contains(@data-index, '{data_index_value}')]//h5[normalize-space(translate(., '{lowercase}', '{uppercase}'))='{label_text_upper}']/ancestor::li[1]",
                        f"//ul//li[.//h5[normalize-space(translate(., '{lowercase}', '{uppercase}'))='{label_text_upper}']]",
                        f"//ul//li[contains(@data-index, '{data_index_value}')]",
                    ]

                    for xp in xpaths:
                        try:
                            el = wait.until(EC.element_to_be_clickable((By.XPATH, xp)))
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
                            time.sleep(0.2)
                            el.click()
                            # Wait for active/selected state if available
                            try:
                                WebDriverWait(self.driver, 5).until(
                                    lambda d: (
                                        'active' in (el.get_attribute('class') or '').lower()
                                        or 'selected' in (el.get_attribute('class') or '').lower()
                                        or (el.get_attribute('aria-selected') or '').lower() == 'true'
                                    )
                                )
                            except Exception:
                                pass
                            return True
                        except TimeoutException:
                            continue
                        except WebDriverException:
                            continue
                    return False

                # Select All timeframe (data-index=tab-4, label "All")
                if _click_li_tab(label_text_upper="ALL", data_index_value="tab-4"):
                    print("  ✅ Set timeframe to All via <li> tab")
                else:
                    print("  ⚠️ Could not find 'All' tab; will continue with default timeframe")

                time.sleep(1)

                # Enable LOG scale (data-index=tab-5, label "LOG")
                if _click_li_tab(label_text_upper="LOG", data_index_value="tab-5"):
                    print("  ✅ Enabled LOG scale via <li> tab")
                else:
                    print("  ⚠️ Could not find 'LOG' tab; proceeding without log scale")
                
            except Exception as e:
                print(f"  ⚠️ Could not interact with chart tabs: {e}")
            
            # Wait for chart to render
            time.sleep(5)
            
            # Try to find SVG chart
            svg_selectors = [
                "svg[class*='chart']",
                "svg[data-testid*='chart']",
                "div[class*='chart'] svg",
                "canvas[class*='chart']",
                "[data-testid='price-chart'] svg"
            ]
            
            svg_element = None
            for selector in svg_selectors:
                try:
                    svg_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    break
                except TimeoutException:
                    continue
            
            if svg_element:
                svg_content = svg_element.get_attribute('outerHTML')
                if svg_content:
                    print(f"  ✅ Successfully extracted SVG chart")
                    return svg_content
            
            # Fallback: try to get chart from embedded data
            try:
                chart_data_script = self.driver.find_element(By.XPATH, "//script[contains(text(), 'chart')]")
                if chart_data_script:
                    print(f"  ⚠️ Found chart data script, but SVG extraction failed")
            except NoSuchElementException:
                pass
            
            print(f"  ❌ Could not extract SVG chart")
            return None
            
        except Exception as e:
            print(f"  ❌ Error processing {coin['name']}: {e}")
            return None
    
    def create_html_table(self, coins_data: List[Dict]) -> str:
        """
        Create HTML table with embedded SVG charts.
        
        Args:
            coins_data: List of dictionaries containing coin data and SVG charts
            
        Returns:
            HTML content as string
        """
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Top 100 Cryptocurrencies - Price Charts</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }
        .stat {
            text-align: center;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.8;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th {
            background-color: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #495057;
            border-bottom: 2px solid #dee2e6;
        }
        td {
            padding: 15px;
            border-bottom: 1px solid #dee2e6;
            vertical-align: top;
        }
        .coin-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .coin-rank {
            background-color: #007bff;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 0.9em;
        }
        .coin-name {
            font-weight: 600;
            color: #212529;
        }
        .coin-slug {
            color: #6c757d;
            font-size: 0.9em;
        }
        .chart-container {
            width: 300px;
            height: 150px;
            border: 1px solid #e9ecef;
            border-radius: 5px;
            overflow: hidden;
            background-color: #f8f9fa;
        }
        .chart-container svg {
            width: 100%;
            height: 100%;
        }
        .no-chart {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #6c757d;
            font-style: italic;
        }
        .tags {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        .tag {
            background-color: #e9ecef;
            color: #495057;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.8em;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
        }
        @media (max-width: 768px) {
            .container {
                margin: 10px;
                border-radius: 5px;
            }
            .header {
                padding: 20px;
            }
            .header h1 {
                font-size: 2em;
            }
            .stats {
                flex-direction: column;
                gap: 15px;
            }
            .chart-container {
                width: 200px;
                height: 100px;
            }
            table {
                font-size: 0.9em;
            }
            th, td {
                padding: 10px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Top 100 Cryptocurrencies</h1>
            <p>Price charts with maximum timeframe and log scale visualization</p>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{total_coins}</div>
                    <div class="stat-label">Total Coins</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{charts_extracted}</div>
                    <div class="stat-label">Charts Extracted</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{success_rate}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th style="width: 80px;">Rank</th>
                    <th style="width: 200px;">Coin</th>
                    <th style="width: 350px;">Price Chart</th>
                    <th style="width: 150px;">Tags</th>
                </tr>
            </thead>
            <tbody>
                {table_rows}
            </tbody>
        </table>
        
        <div class="footer">
            <p>Data extracted from CoinMarketCap on {timestamp}</p>
            <p>Charts displayed with maximum timeframe and log scale where available</p>
        </div>
    </div>
</body>
</html>
        """
        
        table_rows = ""
        charts_extracted = 0
        
        for coin in coins_data:
            rank = coin.get('cmc_rank', 'N/A')
            name = coin.get('name', 'Unknown')
            slug = coin.get('slug', '')
            tags = coin.get('tags', [])
            svg_chart = coin.get('svg_chart', '')
            
            if svg_chart:
                charts_extracted += 1
                chart_html = f'<div class="chart-container">{svg_chart}</div>'
            else:
                chart_html = '<div class="chart-container"><div class="no-chart">Chart not available</div></div>'
            
            tags_html = ""
            if tags:
                tags_html = '<div class="tags">'
                for tag in tags[:3]:  # Limit to 3 tags
                    tags_html += f'<span class="tag">{tag}</span>'
                tags_html += '</div>'
            
            table_rows += f"""
                <tr>
                    <td><div class="coin-rank">{rank}</div></td>
                    <td>
                        <div class="coin-info">
                            <div>
                                <div class="coin-name">{name}</div>
                                <div class="coin-slug">{slug}</div>
                            </div>
                        </div>
                    </td>
                    <td>{chart_html}</td>
                    <td>{tags_html}</td>
                </tr>
            """
        
        total_coins = len(coins_data)
        success_rate = round((charts_extracted / total_coins) * 100, 1) if total_coins > 0 else 0
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return html_template.format(
            total_coins=total_coins,
            charts_extracted=charts_extracted,
            success_rate=success_rate,
            table_rows=table_rows,
            timestamp=timestamp
        )
    
    def save_data(self, coins_data: List[Dict], html_content: str):
        """Save the scraped data to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON data
        json_filename = f"coins_data_selenium_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(coins_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved coin data to {json_filename}")
        
        # Save HTML file
        html_filename = f"cryptocurrency_charts_{timestamp}.html"
        with open(html_filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 Saved HTML table to {html_filename}")
        
        # Save raw SVG files
        svg_dir = f"svg_charts_{timestamp}"
        os.makedirs(svg_dir, exist_ok=True)
        
        for coin in coins_data:
            if coin.get('svg_chart'):
                svg_filename = f"{coin['slug']}_{coin['id']}.svg"
                svg_path = os.path.join(svg_dir, svg_filename)
                with open(svg_path, 'w', encoding='utf-8') as f:
                    f.write(coin['svg_chart'])
        
        print(f"💾 Saved {len([c for c in coins_data if c.get('svg_chart')])} SVG files to {svg_dir}/")
    
    def run(self, headless: bool = False):
        """
        Main execution method.
        
        Args:
            headless: Run browser in headless mode
        """
        try:
            print("🚀 Starting CoinMarketCap Selenium Scraper...")
            print("=" * 50)
            
            # Get top 100 coins
            coins = self.get_top_100_coins()
            if not coins:
                print("❌ No coins found. Exiting.")
                return
            
            # Process each coin to get SVG charts
            processed_coins = []
            for i, coin in enumerate(coins, 1):
                print(f"\n[{i}/{len(coins)}] Processing {coin['name']}...")
                
                svg_chart = self.get_coin_chart_svg(coin)
                coin['svg_chart'] = svg_chart
                processed_coins.append(coin)
                
                # Add delay to avoid rate limiting
                time.sleep(2)
            
            # Create HTML table
            print("\n📊 Generating HTML table...")
            html_content = self.create_html_table(processed_coins)
            
            # Save data
            print("\n💾 Saving data...")
            self.save_data(processed_coins, html_content)
            
            print("\n✅ Scraping completed successfully!")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error during scraping: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                print("🔒 WebDriver closed")

def main():
    """Main function to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape CoinMarketCap with Selenium')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    parser.add_argument('--timeout', type=int, default=30, help='Timeout for webdriver operations')
    
    args = parser.parse_args()
    
    scraper = CoinMarketCapSeleniumScraper(headless=args.headless, timeout=args.timeout)
    scraper.run(headless=args.headless)

if __name__ == "__main__":
    main()

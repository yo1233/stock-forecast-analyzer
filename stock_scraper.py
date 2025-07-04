import requests
import time
from typing import Dict, List, Optional
import re
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
import random

class StockScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Rate limiting settings - being very conservative
        self.min_delay = 2.0  # Minimum 2 seconds between requests
        self.max_delay = 4.0  # Maximum 4 seconds between requests  
        self.last_request_time = {}  # Track per-domain
        
        # Cache for robots.txt
        self.robots_cache = {}
        
    def _check_robots_txt(self, url: str) -> bool:
        """Check if scraping is allowed by robots.txt"""
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if domain not in self.robots_cache:
            try:
                robots_url = urljoin(domain, '/robots.txt')
                rp = RobotFileParser()
                rp.set_url(robots_url)
                rp.read()
                self.robots_cache[domain] = rp
            except Exception as e:
                print(f"Could not fetch robots.txt for {domain}: {e}")
                # If we can't fetch robots.txt, be conservative and deny
                return False
        
        rp = self.robots_cache[domain]
        user_agent = '*'  # Check for general user agent restrictions
        
        return rp.can_fetch(user_agent, url)
    
    def _rate_limit(self, domain: str):
        """Implement respectful rate limiting per domain"""
        current_time = time.time()
        
        if domain in self.last_request_time:
            time_since_last = current_time - self.last_request_time[domain]
            delay_needed = random.uniform(self.min_delay, self.max_delay)
            
            if time_since_last < delay_needed:
                sleep_time = delay_needed - time_since_last
                print(f"Rate limiting: waiting {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def _make_request(self, url: str) -> Optional[str]:
        """Make HTTP request with proper rate limiting and robots.txt respect"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Check robots.txt first
        if not self._check_robots_txt(url):
            print(f"Robots.txt disallows scraping {url}")
            return None
        
        # Apply rate limiting
        self._rate_limit(domain)
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {url}: {e}")
            return None
    
    def get_stock_price_yahoo(self, symbol: str) -> Optional[float]:
        """Get stock price from Yahoo Finance with ethical scraping"""
        url = f"https://finance.yahoo.com/quote/{symbol}"
        
        html = self._make_request(url)
        if not html:
            return None
        
        try:
            # Look for price in common patterns
            price_patterns = [
                r'data-symbol="' + symbol + r'"[^>]*data-field="regularMarketPrice"[^>]*>([\d,]+\.[\d]+)',
                r'"regularMarketPrice":\{"raw":([\d.]+)',
                r'<fin-streamer[^>]*data-field="regularMarketPrice"[^>]*>([\d,]+\.[\d]+)',
                r'<span[^>]*class="[^"]*Fw\(b\)[^"]*"[^>]*>\$?([\d,]+\.[\d]+)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    price_str = match.group(1).replace(',', '')
                    return float(price_str)
            
            print(f"Could not extract price for {symbol} from Yahoo Finance")
            return None
            
        except (ValueError, AttributeError) as e:
            print(f"Error parsing price for {symbol}: {e}")
            return None
    
    def get_analyst_targets_yahoo(self, symbol: str) -> Optional[Dict]:
        """Get analyst price targets from Yahoo Finance"""
        url = f"https://finance.yahoo.com/quote/{symbol}/analysis"
        
        html = self._make_request(url)
        if not html:
            return None
        
        try:
            # Look for analyst price targets in the analysis page
            target_patterns = [
                r'Mean Target Price[^>]*>\$?([\d,]+\.[\d]+)',
                r'Average Target Price[^>]*>\$?([\d,]+\.[\d]+)',
                r'"targetMeanPrice":\{"raw":([\d.]+)',
                r'data-field="targetMeanPrice"[^>]*>([\d,]+\.[\d]+)'
            ]
            
            for pattern in target_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    target_mean = float(match.group(1).replace(',', ''))
                    
                    # Try to find high and low targets
                    high_match = re.search(r'High Target Price[^>]*>\$?([\d,]+\.[\d]+)', html, re.IGNORECASE)
                    low_match = re.search(r'Low Target Price[^>]*>\$?([\d,]+\.[\d]+)', html, re.IGNORECASE)
                    
                    return {
                        'target_mean': target_mean,
                        'target_high': float(high_match.group(1).replace(',', '')) if high_match else target_mean * 1.15,
                        'target_low': float(low_match.group(1).replace(',', '')) if low_match else target_mean * 0.85,
                        'source': 'Yahoo_Scraped'
                    }
            
            print(f"Could not extract analyst targets for {symbol} from Yahoo Finance")
            return None
            
        except (ValueError, AttributeError) as e:
            print(f"Error parsing analyst targets for {symbol}: {e}")
            return None
    
    def get_analyst_targets_seeking_alpha(self, symbol: str) -> Optional[Dict]:
        """Get analyst targets from Seeking Alpha"""
        url = f"https://seekingalpha.com/symbol/{symbol}/analysis"
        
        html = self._make_request(url)
        if not html:
            return None
        
        try:
            # Look for price targets on Seeking Alpha
            target_patterns = [
                r'Price Target[^>]*>\$?([\d,]+\.[\d]+)',
                r'Analyst Target[^>]*>\$?([\d,]+\.[\d]+)',
                r'Average Target[^>]*>\$?([\d,]+\.[\d]+)',
                r'"priceTarget"[^>]*>\$?([\d,]+\.[\d]+)'
            ]
            
            for pattern in target_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    target_mean = float(match.group(1).replace(',', ''))
                    
                    return {
                        'target_mean': target_mean,
                        'target_high': target_mean * 1.20,  # Estimate
                        'target_low': target_mean * 0.80,   # Estimate
                        'source': 'SeekingAlpha_Scraped'
                    }
            
            print(f"Could not extract analyst targets for {symbol} from Seeking Alpha")
            return None
            
        except (ValueError, AttributeError) as e:
            print(f"Error parsing Seeking Alpha targets for {symbol}: {e}")
            return None
    
    def get_stock_data(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive stock data from multiple sources"""
        print(f"Fetching data for {symbol}...")
        
        # Get current price
        current_price = self.get_stock_price_yahoo(symbol)
        if not current_price:
            print(f"Could not get current price for {symbol}")
            return None
        
        # Try to get analyst targets from multiple sources
        analyst_data = None
        
        # Try Yahoo Finance first
        analyst_data = self.get_analyst_targets_yahoo(symbol)
        
        # If Yahoo fails, try Seeking Alpha
        if not analyst_data:
            analyst_data = self.get_analyst_targets_seeking_alpha(symbol)
        
        # If all fail, create conservative estimate
        if not analyst_data:
            # Conservative estimate based on typical analyst behavior
            growth_rate = 0.10  # 10% default
            
            # Adjust for tech stocks
            tech_symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC']
            if symbol.upper() in tech_symbols:
                growth_rate = 0.15  # 15% for tech
            
            estimated_target = current_price * (1 + growth_rate)
            analyst_data = {
                'target_mean': estimated_target,
                'target_high': current_price * (1 + growth_rate + 0.10),
                'target_low': current_price * (1 + growth_rate - 0.05),
                'source': 'Conservative_Estimate'
            }
        
        # Calculate forecast percentage
        forecast_percentage = ((analyst_data['target_mean'] - current_price) / current_price) * 100
        
        return {
            'symbol': symbol.upper(),
            'current_price': current_price,
            'target_mean': analyst_data['target_mean'],
            'target_high': analyst_data['target_high'],
            'target_low': analyst_data['target_low'],
            'forecast_percentage': forecast_percentage,
            'source': analyst_data['source']
        }
    
    def get_popular_stocks(self) -> List[str]:
        """Get list of popular stocks to analyze"""
        return [
            # Major technology stocks
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
            
            # Financial services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA', 'BLK', 'AXP',
            
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR',
            
            # Consumer goods
            'WMT', 'COST', 'TGT', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'KO', 'PEP',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG',
            
            # Industrial
            'GE', 'BA', 'CAT', 'DE', 'MMM', 'HON'
        ]
    
    def analyze_single_stock(self, symbol: str):
        """Analyze a single stock"""
        data = self.get_stock_data(symbol)
        if not data:
            print(f"Could not analyze {symbol}")
            return
        
        print(f"\n--- {data['symbol']} Analysis ---")
        print(f"Current Price: ${data['current_price']:.2f}")
        print(f"12-Month Price Target: ${data['target_mean']:.2f}")
        print(f"Forecast: {data['forecast_percentage']:+.1f}%")
        print(f"Target Range: ${data['target_low']:.2f} - ${data['target_high']:.2f}")
        
        # Show data source
        source = data['source']
        if 'Scraped' in source:
            print(f"✓ Data scraped from {source.replace('_Scraped', '')}")
        elif 'Estimate' in source:
            print(f"⚠ {source} (real data unavailable)")
    
    def screen_stocks(self, min_percentage: float):
        """Screen stocks by minimum forecast percentage"""
        print(f"\nScreening stocks with forecast ≥ {min_percentage}%...")
        print("This will take several minutes due to respectful rate limiting...")
        
        stocks = self.get_popular_stocks()
        qualifying_stocks = []
        
        for i, symbol in enumerate(stocks):
            print(f"\nAnalyzing {symbol} ({i+1}/{len(stocks)})...")
            
            data = self.get_stock_data(symbol)
            if data and data['forecast_percentage'] >= min_percentage:
                qualifying_stocks.append(data)
        
        # Display results
        print(f"\n--- Stocks with ≥{min_percentage}% 12-Month Forecast ---")
        if qualifying_stocks:
            qualifying_stocks.sort(key=lambda x: x['forecast_percentage'], reverse=True)
            
            for stock in qualifying_stocks:
                source_indicator = "✓" if 'Scraped' in stock['source'] else "⚠"
                print(f"{source_indicator} {stock['symbol']}: ${stock['current_price']:.2f} → ${stock['target_mean']:.2f} ({stock['forecast_percentage']:+.1f}%)")
        else:
            print("No stocks found meeting the criteria.")

def main():
    scraper = StockScraper()
    
    print("Ethical Stock Scraper - 12-month forecasts via web scraping")
    print("Respects robots.txt and implements conservative rate limiting")
    print("=" * 65)
    print("✓ = Scraped real data  |  ⚠ = Estimated when scraping blocked")
    print("=" * 65)
    
    while True:
        stock_input = input("\nEnter a stock symbol (or 'all' to screen stocks, 'quit' to exit): ").strip()
        
        if stock_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif stock_input.lower() == 'all':
            try:
                percentage = float(input("Enter minimum forecast percentage (e.g., 15 for 15%): "))
                scraper.screen_stocks(percentage)
            except ValueError:
                print("Invalid percentage. Please enter a number.")
        elif stock_input:
            scraper.analyze_single_stock(stock_input)
        else:
            print("Please enter a valid stock symbol or 'all'.")

if __name__ == "__main__":
    main()
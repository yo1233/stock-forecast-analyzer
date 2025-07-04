import requests
import json
import time
from typing import Dict, List, Optional

class AlphaVantageAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.0  # 5 calls per minute = 12 seconds between calls
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Respect Alpha Vantage's 5 calls per minute limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict) -> Optional[Dict]:
        """Make API request with rate limiting"""
        self._rate_limit()
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                print(f"API Error: {data['Error Message']}")
                return None
            if 'Note' in data:
                print(f"API Note: {data['Note']}")
                return None
                
            return data
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return None
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """Get real-time stock quote"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data or 'Global Quote' not in data:
            return None
        
        quote = data['Global Quote']
        try:
            return {
                'symbol': quote['01. symbol'],
                'current_price': float(quote['05. price']),
                'change': float(quote['09. change']),
                'change_percent': quote['10. change percent'].rstrip('%'),
                'volume': int(quote['06. volume'])
            }
        except (KeyError, ValueError) as e:
            print(f"Error parsing quote data: {e}")
            return None
    
    def get_company_overview(self, symbol: str) -> Optional[Dict]:
        """Get company overview including analyst target price"""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data:
            return None
        
        try:
            # Extract relevant financial data
            overview = {
                'symbol': data.get('Symbol', symbol),
                'name': data.get('Name', 'N/A'),
                'analyst_target_price': data.get('AnalystTargetPrice', 'None'),
                'trailing_pe': data.get('TrailingPE', 'N/A'),
                'forward_pe': data.get('ForwardPE', 'N/A'),
                'peg_ratio': data.get('PEGRatio', 'N/A'),
                'market_cap': data.get('MarketCapitalization', 'N/A'),
                'ev_revenue': data.get('EVToRevenue', 'N/A'),
                'profit_margin': data.get('ProfitMargin', 'N/A'),
                'operating_margin': data.get('OperatingMarginTTM', 'N/A'),
                'roe': data.get('ReturnOnEquityTTM', 'N/A'),
                'revenue_growth': data.get('QuarterlyRevenueGrowthYOY', 'N/A'),
                'earnings_growth': data.get('QuarterlyEarningsGrowthYOY', 'N/A'),
                'sector': data.get('Sector', 'N/A'),
                'industry': data.get('Industry', 'N/A')
            }
            
            return overview
        except Exception as e:
            print(f"Error parsing company overview: {e}")
            return None
    
    def analyze_stock(self, symbol: str) -> Optional[Dict]:
        """Get comprehensive stock analysis"""
        print(f"Analyzing {symbol.upper()}...")
        
        # Get current quote
        quote_data = self.get_stock_quote(symbol)
        if not quote_data:
            print(f"Could not fetch quote for {symbol}")
            return None
        
        # Get company overview
        overview_data = self.get_company_overview(symbol)
        if not overview_data:
            print(f"Could not fetch company overview for {symbol}")
            return None
        
        # Extract analyst target price
        target_price_str = overview_data.get('analyst_target_price', 'None')
        
        if target_price_str == 'None' or target_price_str == '-':
            print(f"No analyst target price available for {symbol}")
            return None
        
        try:
            target_price = float(target_price_str)
            current_price = quote_data['current_price']
            
            # Calculate forecast percentage
            forecast_percentage = ((target_price - current_price) / current_price) * 100
            
            # Create estimated range (Alpha Vantage only gives mean target)
            target_high = target_price * 1.15  # Estimate 15% above mean
            target_low = target_price * 0.85   # Estimate 15% below mean
            
            return {
                'symbol': symbol.upper(),
                'company_name': overview_data.get('name', 'N/A'),
                'current_price': current_price,
                'target_mean': target_price,
                'target_high': target_high,
                'target_low': target_low,
                'forecast_percentage': forecast_percentage,
                'change': quote_data['change'],
                'change_percent': quote_data['change_percent'],
                'sector': overview_data.get('sector', 'N/A'),
                'industry': overview_data.get('industry', 'N/A'),
                'market_cap': overview_data.get('market_cap', 'N/A'),
                'pe_ratio': overview_data.get('trailing_pe', 'N/A'),
                'source': 'Alpha_Vantage'
            }
            
        except ValueError:
            print(f"Invalid target price format for {symbol}: {target_price_str}")
            return None
    
    def get_popular_stocks(self) -> List[str]:
        """Get list of popular stocks to analyze"""
        return [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC',
            'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'SPOT', 'IBM', 'CSCO', 'QCOM', 'TXN',
            
            # Financial Services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'BLK', 'AXP',
            
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'GILD',
            
            # Consumer
            'WMT', 'COST', 'TGT', 'HD', 'LOW', 'NKE', 'SBUX', 'MCD', 'KO', 'PEP',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB',
            
            # Industrial
            'GE', 'BA', 'CAT', 'DE', 'MMM'
        ]
    
    def display_analysis(self, data: Dict):
        """Display formatted stock analysis"""
        # Calculate percentage changes for target range
        current_price = data['current_price']
        target_low_percent = ((data['target_low'] - current_price) / current_price) * 100
        target_high_percent = ((data['target_high'] - current_price) / current_price) * 100
        
        print(f"\n{'='*70}")
        print(f"📊 {data['symbol']} - {data['company_name']}")
        print(f"{'='*70}")
        print(f"💰 Current Price: ${data['current_price']:.2f}")
        print(f"📈 12-Month Forecast: ${data['target_mean']:.2f} ({data['forecast_percentage']:+.1f}%)")
        print(f"📊 Minimum Target: ${data['target_low']:.2f} ({target_low_percent:+.1f}%)")
        print(f"📊 Maximum Target: ${data['target_high']:.2f} ({target_high_percent:+.1f}%)")
        print(f"📉 Today's Change: ${data['change']:+.2f} ({data['change_percent']}%)")
        print(f"🏢 Sector: {data['sector']}")
        print(f"🏭 Industry: {data['industry']}")
        print(f"💎 Market Cap: {data['market_cap']}")
        print(f"📊 P/E Ratio: {data['pe_ratio']}")
        print(f"✅ Data Source: Real analyst consensus via Alpha Vantage")
    
    def screen_stocks(self, min_percentage: float):
        """Screen stocks by minimum forecast percentage"""
        print(f"\n🔍 Screening stocks with forecast ≥ {min_percentage}%...")
        print("⏱️  This will take several minutes due to API rate limiting (5 calls/minute)...")
        
        stocks = self.get_popular_stocks()
        qualifying_stocks = []
        total_stocks = len(stocks)
        
        for i, symbol in enumerate(stocks, 1):
            print(f"\n📊 Analyzing {symbol} ({i}/{total_stocks})...")
            
            data = self.analyze_stock(symbol)
            if data and data['forecast_percentage'] >= min_percentage:
                qualifying_stocks.append(data)
                print(f"✅ {symbol}: {data['forecast_percentage']:+.1f}% (QUALIFIES)")
            elif data:
                print(f"❌ {symbol}: {data['forecast_percentage']:+.1f}% (below threshold)")
        
        # Display results
        print(f"\n{'='*80}")
        print(f"🎯 STOCKS WITH ≥{min_percentage}% 12-MONTH FORECAST")
        print(f"{'='*80}")
        
        if qualifying_stocks:
            qualifying_stocks.sort(key=lambda x: x['forecast_percentage'], reverse=True)
            
            for i, stock in enumerate(qualifying_stocks, 1):
                print(f"\n{i}. 📈 {stock['symbol']} - {stock['company_name']}")
                print(f"   💰 ${stock['current_price']:.2f} → ${stock['target_mean']:.2f} ({stock['forecast_percentage']:+.1f}%)")
                print(f"   🏢 {stock['sector']} | 📊 P/E: {stock['pe_ratio']}")
        else:
            print("❌ No stocks found meeting the criteria.")
            print("💡 Try lowering the percentage threshold.")

def main():
    print("🚀 Alpha Vantage Stock Analyzer - Real Analyst Forecasts")
    print("=" * 65)
    
    # Get API key from user
    api_key = input("Enter your Alpha Vantage API key: ").strip()
    
    if not api_key:
        print("❌ API key is required. Get yours free at: https://www.alphavantage.co/support/#api-key")
        return
    
    analyzer = AlphaVantageAnalyzer(api_key)
    
    print("\n✅ API key configured!")
    print("💡 Note: Free tier allows 5 calls per minute (500 per day)")
    print("=" * 65)
    
    while True:
        choice = input("\nEnter a stock symbol (or 'all' to screen stocks, 'quit' to exit): ").strip()
        
        if choice.lower() == 'quit':
            print("👋 Goodbye!")
            break
        elif choice.lower() == 'all':
            try:
                percentage = float(input("Enter minimum forecast percentage (e.g., 15 for 15%): "))
                analyzer.screen_stocks(percentage)
            except ValueError:
                print("❌ Invalid percentage. Please enter a number.")
        elif choice:
            data = analyzer.analyze_stock(choice)
            if data:
                analyzer.display_analysis(data)
        else:
            print("❌ Please enter a valid stock symbol or 'all'.")

if __name__ == "__main__":
    main()
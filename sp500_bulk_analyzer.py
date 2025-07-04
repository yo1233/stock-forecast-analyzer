import requests
import json
import time
import csv
from datetime import datetime
from typing import Dict, List, Optional

class SP500BulkAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.rate_limit_delay = 12.5  # 12.5 seconds = ~4.8 calls per minute (safely under 5)
        self.last_request_time = 0
        self.results = []
        self.failed_symbols = []
        
    def _rate_limit(self):
        """Respect Alpha Vantage's rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"⏱️  Rate limiting: waiting {sleep_time:.1f}s...")
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
                print(f"❌ API Error: {data['Error Message']}")
                return None
            if 'Note' in data and 'call frequency' in data['Note'].lower():
                print(f"⚠️  Rate limit hit: {data['Note']}")
                print("😴 Sleeping for 70 seconds...")
                time.sleep(70)  # Wait longer when rate limited
                return self._make_request(params)  # Retry
                
            return data
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return None
    
    def get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 company symbols"""
        # Major S&P 500 companies (you can expand this list)
        sp500_companies = [
            # Technology (mega caps)
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'ADBE', 'CRM',
            'ORCL', 'INTC', 'AMD', 'QCOM', 'TXN', 'AVGO', 'CSCO', 'IBM', 'INTU', 'NOW',
            
            # Financial Services  
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP', 'BLK', 'SCHW', 'USB',
            'PNC', 'TFC', 'COF', 'BK', 'STT', 'DFS', 'SYF', 'ALLY',
            
            # Healthcare
            'UNH', 'JNJ', 'PFE', 'ABBV', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD',
            'CVS', 'ANTM', 'CI', 'HUM', 'SYK', 'BSX', 'MDT', 'ISRG', 'VRTX',
            
            # Consumer Discretionary
            'AMZN', 'TSLA', 'HD', 'MCD', 'NKE', 'SBUX', 'TJX', 'LOW', 'TGT', 'CMG',
            'BKNG', 'DIS', 'GM', 'F', 'MAR', 'HLT', 'MGM', 'WYNN', 'LVS', 'RCL',
            
            # Consumer Staples
            'WMT', 'PG', 'KO', 'PEP', 'COST', 'WBA', 'EL', 'CL', 'KMB', 'GIS',
            'K', 'HSY', 'MDLZ', 'CPB', 'SJM', 'CAG', 'HRL', 'MKC', 'CHD', 'CLX',
            
            # Energy
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'KMI', 'OKE', 'WMB', 'MPC',
            'VLO', 'PSX', 'HES', 'DVN', 'FANG', 'APA', 'EQT', 'CNX', 'AR', 'SM',
            
            # Industrials
            'GE', 'BA', 'CAT', 'DE', 'UNP', 'UPS', 'HON', 'LMT', 'RTX', 'NOC',
            'GD', 'MMM', 'EMR', 'ETN', 'ITW', 'PH', 'CMI', 'ROK', 'DOV', 'FLR',
            
            # Materials
            'LIN', 'APD', 'SHW', 'ECL', 'FCX', 'NEM', 'CF', 'LYB', 'DOW', 'DD',
            'PPG', 'ALB', 'IFF', 'FMC', 'MLM', 'VMC', 'NUE', 'STLD', 'RS', 'PKG',
            
            # Real Estate
            'AMT', 'PLD', 'CCI', 'EQIX', 'PSA', 'WELL', 'DLR', 'EXR', 'AVB', 'EQR',
            'UDR', 'ESS', 'MAA', 'CPT', 'BXP', 'VTR', 'ARE', 'SPG', 'O', 'CBRE',
            
            # Utilities
            'NEE', 'SO', 'D', 'DUK', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'ED',
            'FE', 'ES', 'AES', 'PPL', 'CMS', 'DTE', 'NI', 'LNT', 'EVRG', 'AEE',
            
            # Communication
            'GOOGL', 'META', 'NFLX', 'DIS', 'VZ', 'T', 'TMUS', 'CHTR', 'CMCSA', 'DISH'
        ]
        
        # Remove duplicates and return first 500 (or all if less)
        unique_symbols = list(dict.fromkeys(sp500_companies))
        return unique_symbols[:200]  # Start with 200 for testing
    
    def analyze_stock_quick(self, symbol: str) -> Optional[Dict]:
        """Quick analysis focusing on company overview (1 API call vs 2)"""
        print(f"📊 Analyzing {symbol}...")
        
        # Get company overview (includes analyst target price)
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if not data:
            self.failed_symbols.append(symbol)
            return None
        
        try:
            # Extract key data
            name = data.get('Name', 'N/A')
            analyst_target = data.get('AnalystTargetPrice', 'None')
            
            if analyst_target == 'None' or analyst_target == '-':
                print(f"❌ {symbol}: No analyst target available")
                self.failed_symbols.append(symbol)
                return None
            
            # Get current price from 52-week high/low data (approximate)
            week_52_high = data.get('52WeekHigh', 'None')
            week_52_low = data.get('52WeekLow', 'None')
            
            if week_52_high == 'None' or week_52_low == 'None':
                print(f"❌ {symbol}: No price data available")
                self.failed_symbols.append(symbol)
                return None
            
            # Estimate current price as midpoint (not perfect but workable)
            current_price_est = (float(week_52_high) + float(week_52_low)) / 2
            target_price = float(analyst_target)
            
            # Calculate forecast percentage
            forecast_percentage = ((target_price - current_price_est) / current_price_est) * 100
            
            result = {
                'symbol': symbol,
                'company_name': name,
                'estimated_current_price': current_price_est,
                'analyst_target': target_price,
                'forecast_percentage': forecast_percentage,
                'sector': data.get('Sector', 'N/A'),
                'industry': data.get('Industry', 'N/A'),
                'market_cap': data.get('MarketCapitalization', 'N/A'),
                'pe_ratio': data.get('TrailingPE', 'N/A'),
                'profit_margin': data.get('ProfitMargin', 'N/A'),
                'roe': data.get('ReturnOnEquityTTM', 'N/A'),
                'revenue_growth': data.get('QuarterlyRevenueGrowthYOY', 'N/A'),
                'earnings_growth': data.get('QuarterlyEarningsGrowthYOY', 'N/A')
            }
            
            print(f"✅ {symbol}: {forecast_percentage:+.1f}%")
            return result
            
        except (ValueError, TypeError) as e:
            print(f"❌ {symbol}: Error parsing data - {e}")
            self.failed_symbols.append(symbol)
            return None
    
    def bulk_analyze(self, min_forecast: float = None) -> List[Dict]:
        """Analyze all S&P 500 companies"""
        symbols = self.get_sp500_symbols()
        total_symbols = len(symbols)
        
        print(f"🚀 Starting bulk analysis of {total_symbols} S&P 500 companies")
        print(f"⏱️  Estimated time: {(total_symbols * 12.5) / 60:.1f} minutes")
        print(f"📊 Rate limit: 1 request every 12.5 seconds")
        print("=" * 70)
        
        start_time = time.time()
        successful_analyses = 0
        
        for i, symbol in enumerate(symbols, 1):
            print(f"\n[{i}/{total_symbols}] ", end="")
            
            result = self.analyze_stock_quick(symbol)
            if result:
                # Apply filter if specified
                if min_forecast is None or result['forecast_percentage'] >= min_forecast:
                    self.results.append(result)
                    successful_analyses += 1
            
            # Progress update every 10 stocks
            if i % 10 == 0:
                elapsed = (time.time() - start_time) / 60
                remaining = ((total_symbols - i) * 12.5) / 60
                print(f"\n📈 Progress: {i}/{total_symbols} ({i/total_symbols*100:.1f}%)")
                print(f"⏱️  Elapsed: {elapsed:.1f}m | Remaining: {remaining:.1f}m")
                print(f"✅ Successful: {successful_analyses} | ❌ Failed: {len(self.failed_symbols)}")
        
        print(f"\n{'='*70}")
        print(f"🎉 Bulk analysis complete!")
        print(f"✅ Successful analyses: {successful_analyses}")
        print(f"❌ Failed analyses: {len(self.failed_symbols)}")
        print(f"⏱️  Total time: {(time.time() - start_time) / 60:.1f} minutes")
        
        return self.results
    
    def save_results(self, filename: str = None):
        """Save results to CSV file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"sp500_forecasts_{timestamp}.csv"
        
        if not self.results:
            print("❌ No results to save")
            return
        
        # Sort by forecast percentage (highest first)
        sorted_results = sorted(self.results, key=lambda x: x['forecast_percentage'], reverse=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'symbol', 'company_name', 'estimated_current_price', 'analyst_target',
                'forecast_percentage', 'sector', 'industry', 'market_cap', 'pe_ratio',
                'profit_margin', 'roe', 'revenue_growth', 'earnings_growth'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(sorted_results)
        
        print(f"💾 Results saved to: {filename}")
        return filename
    
    def display_top_forecasts(self, top_n: int = 20):
        """Display top N forecasts"""
        if not self.results:
            print("❌ No results to display")
            return
        
        sorted_results = sorted(self.results, key=lambda x: x['forecast_percentage'], reverse=True)
        
        print(f"\n{'='*80}")
        print(f"🎯 TOP {min(top_n, len(sorted_results))} STOCK FORECASTS")
        print(f"{'='*80}")
        
        for i, stock in enumerate(sorted_results[:top_n], 1):
            print(f"\n{i:2d}. 📈 {stock['symbol']} - {stock['company_name']}")
            print(f"    💰 Est. Price: ${stock['estimated_current_price']:.2f} → ${stock['analyst_target']:.2f}")
            print(f"    🎯 Forecast: {stock['forecast_percentage']:+.1f}%")
            print(f"    🏢 {stock['sector']} | 📊 P/E: {stock['pe_ratio']}")

def main():
    print("🏆 S&P 500 Bulk Stock Forecast Analyzer")
    print("=" * 50)
    
    api_key = input("Enter your Alpha Vantage API key: ").strip()
    if not api_key:
        print("❌ API key required")
        return
    
    analyzer = SP500BulkAnalyzer(api_key)
    
    print("\nOptions:")
    print("1. Analyze ALL stocks (takes ~40+ minutes)")
    print("2. Analyze stocks with forecast ≥ X%")
    print("3. Quick test (first 10 stocks)")
    
    choice = input("\nEnter choice (1/2/3): ").strip()
    
    if choice == '1':
        results = analyzer.bulk_analyze()
    elif choice == '2':
        try:
            min_forecast = float(input("Enter minimum forecast % (e.g., 15): "))
            results = analyzer.bulk_analyze(min_forecast)
        except ValueError:
            print("❌ Invalid percentage")
            return
    elif choice == '3':
        # Test with first 10 stocks
        analyzer.get_sp500_symbols = lambda: analyzer.get_sp500_symbols()[:10]
        results = analyzer.bulk_analyze()
    else:
        print("❌ Invalid choice")
        return
    
    if results:
        analyzer.display_top_forecasts(20)
        filename = analyzer.save_results()
        print(f"\n📄 Full results saved to: {filename}")
        print("\n💡 You can open this CSV file in Excel or Google Sheets for further analysis")

if __name__ == "__main__":
    main()
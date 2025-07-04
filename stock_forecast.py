import yfinance as yf
import pandas as pd
import time
import json
from datetime import datetime

# Predefined sector lists
SECTOR_STOCKS = {
    'tech': ['AAPL', 'MSFT', 'GOOGL', 'META', 'NVDA', 'AMD', 'ADBE', 'CRM', 'ORCL', 'INTC', 'CSCO', 'AVGO', 'QCOM', 'TXN', 'INTU', 'NOW', 'PANW', 'ANET', 'SNPS', 'CDNS', 'KEYS', 'FTNT', 'EPAM', 'COIN', 'SMCI'],
    'healthcare': ['JNJ', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'DHR', 'BMY', 'AMGN', 'GILD', 'BIIB', 'REGN', 'VRTX', 'ISRG', 'MDT', 'BSX', 'SYK', 'ELV', 'CVS'],
    'financial': ['JPM', 'BAC', 'WFC', 'C', 'GS', 'MS', 'AXP', 'BLK', 'SCHW', 'PNC', 'USB', 'TFC', 'COF', 'AIG', 'AON', 'SPGI', 'ICE', 'CME', 'MCO', 'V'],
    'consumer': ['AMZN', 'TSLA', 'HD', 'WMT', 'PG', 'KO', 'PEP', 'COST', 'TGT', 'SBUX', 'NKE', 'MCD', 'TJX', 'LOW', 'LULU'],
    'energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO', 'MPC', 'OXY', 'HAL', 'DVN', 'FANG', 'APA', 'EQT', 'CTRA'],
    'industrial': ['CAT', 'BA', 'HON', 'RTX', 'UNP', 'LMT', 'GE', 'MMM', 'DE', 'UPS', 'GD', 'NOC', 'FDX', 'EMR', 'ETN'],
    'utilities': ['NEE', 'DUK', 'SO', 'D', 'EXC', 'AEP', 'SRE', 'PEG', 'XEL', 'ED', 'EIX', 'ES', 'FE', 'AEE', 'CMS']
}

def get_stock_forecast(symbol):
    try:
        stock = yf.Ticker(symbol)
        
        print(f"\n=== Analyst Forecast for {symbol.upper()} ===")
        
        # Get analyst price targets using upgrades_downgrades
        try:
            upgrades_downgrades = stock.upgrades_downgrades
            if upgrades_downgrades is not None and not upgrades_downgrades.empty:
                print("\nRecent Analyst Actions:")
                recent_actions = upgrades_downgrades.head(10)
                for _, action in recent_actions.iterrows():
                    print(f"  {action.name.strftime('%Y-%m-%d')}: {action['Firm']} - {action['ToGrade']} (from {action['FromGrade']})")
            else:
                print("No recent analyst actions available.")
        except:
            print("Unable to fetch analyst actions.")
        
        # Get analyst recommendations
        try:
            recommendations = stock.recommendations
            if recommendations is not None and not recommendations.empty:
                print("\nRecent Analyst Recommendations:")
                recent_recs = recommendations.head(5)
                for _, rec in recent_recs.iterrows():
                    print(f"  {rec['period']}: {rec['strongBuy']} Strong Buy, {rec['buy']} Buy, {rec['hold']} Hold, {rec['sell']} Sell, {rec['strongSell']} Strong Sell")
        except:
            print("Unable to fetch analyst recommendations.")
        
        # Get current stock price and info
        try:
            info = stock.info
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            if current_price:
                print(f"\nCurrent Stock Price: ${current_price:.2f}")
                
                # Get analyst price targets from info
                target_high = info.get('targetHighPrice')
                target_low = info.get('targetLowPrice')
                target_mean = info.get('targetMeanPrice')
                target_median = info.get('targetMedianPrice')
                
                if target_mean:
                    print(f"Mean Price Target: ${target_mean:.2f}")
                    upside_potential = ((target_mean - current_price) / current_price) * 100
                    print(f"Upside Potential: {upside_potential:.2f}%")
                
                if target_high:
                    print(f"High Price Target: ${target_high:.2f}")
                if target_low:
                    print(f"Low Price Target: ${target_low:.2f}")
                if target_median:
                    print(f"Median Price Target: ${target_median:.2f}")
                
                # Additional analyst info
                recommendation_mean = info.get('recommendationMean')
                recommendation_key = info.get('recommendationKey')
                number_of_analyst_opinions = info.get('numberOfAnalystOpinions')
                
                if recommendation_key:
                    print(f"Overall Recommendation: {recommendation_key.upper()}")
                if recommendation_mean:
                    print(f"Recommendation Score: {recommendation_mean:.2f} (1=Strong Buy, 5=Strong Sell)")
                if number_of_analyst_opinions:
                    print(f"Number of Analyst Opinions: {number_of_analyst_opinions}")
            else:
                print("Unable to fetch current stock price.")
        except Exception as e:
            print(f"Error fetching stock info: {str(e)}")
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
        print("Please check if the stock symbol is correct and try again.")

def process_stock_chunk(stock_list, delay=5, chunk_info=""):
    """Process a chunk of stocks with progress tracking"""
    results = []
    total_stocks = len(stock_list)
    
    print(f"Processing {chunk_info}{total_stocks} stocks with {delay}s delay between requests...")
    print("This may take a while. Press Ctrl+C to stop.\n")
    
    for i, symbol in enumerate(stock_list, 1):
        print(f"[{i}/{total_stocks}] Processing {symbol}...")
        
        try:
            # Get basic info first (faster)
            stock = yf.Ticker(symbol)
            info = stock.info
            
            # Extract key data
            current_price = info.get('currentPrice', info.get('regularMarketPrice'))
            target_mean = info.get('targetMeanPrice')
            target_high = info.get('targetHighPrice')
            target_low = info.get('targetLowPrice')
            recommendation_key = info.get('recommendationKey')
            recommendation_mean = info.get('recommendationMean')
            
            result = {
                'symbol': symbol,
                'current_price': current_price,
                'target_mean': target_mean,
                'target_high': target_high,
                'target_low': target_low,
                'upside_potential': None,
                'downside_risk': None,
                'max_upside': None,
                'recommendation': recommendation_key,
                'rec_score': recommendation_mean,
                'status': 'success'
            }
            
            if current_price and target_mean:
                result['upside_potential'] = ((target_mean - current_price) / current_price) * 100
            
            if current_price and target_low:
                result['downside_risk'] = ((target_low - current_price) / current_price) * 100
            
            if current_price and target_high:
                result['max_upside'] = ((target_high - current_price) / current_price) * 100
            
            results.append(result)
            
            if current_price and target_mean and target_low and target_high:
                print(f"  ✓ {symbol}: ${current_price:.2f} | Target: ${target_low:.2f}-${target_high:.2f} (Mean: ${target_mean:.2f}) | {result['downside_risk']:.1f}% to {result['max_upside']:.1f}%")
            elif current_price and target_mean:
                print(f"  ✓ {symbol}: ${current_price:.2f} -> ${target_mean:.2f} ({result['upside_potential']:.1f}% upside)")
            else:
                print(f"  ✓ {symbol}: Data retrieved")
            
        except Exception as e:
            print(f"  ✗ {symbol}: Error - {str(e)}")
            results.append({
                'symbol': symbol,
                'status': 'error',
                'error': str(e)
            })
        
        # Rate limiting delay
        if i < total_stocks:
            time.sleep(delay)
    
    return results

def process_stock_list(stock_list, delay=5):
    """Wrapper for backward compatibility"""
    return process_stock_chunk(stock_list, delay)

def process_all_sectors_chunked(delay=5, chunk_break=30):
    """Process all sectors in chunks with breaks between them"""
    all_results = []
    total_sectors = len(SECTOR_STOCKS)
    
    print(f"\n🚀 COMPREHENSIVE MARKET ANALYSIS")
    print("="*60)
    print(f"Processing {sum(len(stocks) for stocks in SECTOR_STOCKS.values())} stocks across {total_sectors} sectors")
    print(f"Estimated time: ~{(sum(len(stocks) for stocks in SECTOR_STOCKS.values()) * delay + total_sectors * chunk_break) // 60} minutes")
    print("="*60)
    
    for i, (sector_name, stock_list) in enumerate(SECTOR_STOCKS.items(), 1):
        print(f"\n📊 SECTOR {i}/{total_sectors}: {sector_name.upper()}")
        print("-" * 40)
        
        chunk_info = f"[Sector {i}/{total_sectors}] {sector_name.upper()} - "
        sector_results = process_stock_chunk(stock_list, delay, chunk_info)
        all_results.extend(sector_results)
        
        # Save progress after each sector
        temp_filename = f"market_analysis_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(temp_filename, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n💾 Progress saved to: {temp_filename}")
        
        # Break between sectors (except for the last one)
        if i < total_sectors:
            print(f"\n⏸️  Taking {chunk_break}s break before next sector...")
            time.sleep(chunk_break)
    
    print(f"\n🎉 ANALYSIS COMPLETE!")
    print(f"Total stocks processed: {len([r for r in all_results if r['status'] == 'success'])}")
    print(f"Failed: {len([r for r in all_results if r['status'] == 'error'])}")
    
    return all_results

def display_batch_results(results):
    print("\n" + "="*80)
    print("BATCH PROCESSING RESULTS")
    print("="*80)
    
    successful = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] == 'error']
    
    print(f"\nSUMMARY: {len(successful)} successful, {len(failed)} failed")
    
    if successful:
        print("\nTOP OPPORTUNITIES (by average upside potential):")
        print("Rank | Symbol | Current  | Avg Forecast     | Low-High Range    | Low-High Range (%) | Rec")
        print("-" * 100)
        
        # Sort by upside potential
        sorted_results = sorted([r for r in successful if r.get('upside_potential')], 
                              key=lambda x: x['upside_potential'], reverse=True)
        
        for i, result in enumerate(sorted_results, 1):
            symbol = result['symbol']
            current = result['current_price']
            target_low = result.get('target_low')
            target_high = result.get('target_high')
            target_mean = result['target_mean']
            downside = result.get('downside_risk')
            upside = result['upside_potential']
            max_upside = result.get('max_upside')
            rec = result['recommendation'] or 'N/A'
            
            # Format average forecast (price and percent)
            if target_mean and upside is not None:
                avg_forecast = f"${target_mean:6.2f} ({upside:+5.1f}%)"
            else:
                avg_forecast = "N/A".center(16)
            
            # Format price range
            if target_low and target_high:
                price_range = f"${target_low:6.2f}-${target_high:6.2f}"
            else:
                price_range = "N/A".center(15)
            
            # Format percentage range
            if downside is not None and max_upside is not None:
                percent_range = f"{downside:+5.1f}% to {max_upside:+5.1f}%"
            else:
                percent_range = "N/A".center(16)
            
            print(f"{i:2d}   | {symbol:6s} | ${current:7.2f} | {avg_forecast} | {price_range} | {percent_range} | {rec}")
        
        # Show highest and lowest targets
        print("\n" + "="*80)
        print("EXTREME FORECASTS:")
        
        # Highest upside potential
        max_upside_stocks = sorted([r for r in successful if r.get('max_upside')], 
                                 key=lambda x: x['max_upside'], reverse=True)[:5]
        if max_upside_stocks:
            print("\nHIGHEST MAXIMUM UPSIDE POTENTIAL:")
            for i, result in enumerate(max_upside_stocks, 1):
                print(f"{i}. {result['symbol']:6s}: ${result['current_price']:7.2f} -> ${result['target_high']:7.2f} ({result['max_upside']:+5.1f}%)")
        
        # Highest downside risk
        max_downside_stocks = sorted([r for r in successful if r.get('downside_risk')], 
                                   key=lambda x: x['downside_risk'])[:5]
        if max_downside_stocks:
            print("\nHIGHEST DOWNSIDE RISK:")
            for i, result in enumerate(max_downside_stocks, 1):
                print(f"{i}. {result['symbol']:6s}: ${result['current_price']:7.2f} -> ${result['target_low']:7.2f} ({result['downside_risk']:+5.1f}%)")
    
    if failed:
        print(f"\nFAILED STOCKS ({len(failed)}):")
        for result in failed:
            print(f"  {result['symbol']}: {result['error']}")

def save_results_to_file(results, filename=None):
    if filename is None:
        filename = f"stock_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\nResults saved to: {filename}")

def parse_stock_list(input_string):
    # Handle comma-separated, space-separated, or newline-separated lists
    symbols = []
    for delimiter in [',', ' ', '\n']:
        if delimiter in input_string:
            symbols = [s.strip().upper() for s in input_string.split(delimiter) if s.strip()]
            break
    
    if not symbols:
        symbols = [input_string.strip().upper()]
    
    return symbols

def show_sector_menu():
    print("\n" + "="*50)
    print("SECTOR ANALYSIS MENU")
    print("="*50)
    print("Available sectors:")
    for i, (sector, stocks) in enumerate(SECTOR_STOCKS.items(), 1):
        print(f"{i}. {sector.upper():12s} ({len(stocks)} stocks)")
    print("="*50)
    
    while True:
        try:
            choice = input("\nEnter sector number (1-7): ").strip()
            sector_num = int(choice)
            if 1 <= sector_num <= len(SECTOR_STOCKS):
                sector_name = list(SECTOR_STOCKS.keys())[sector_num - 1]
                return sector_name, SECTOR_STOCKS[sector_name]
            else:
                print("Invalid choice. Please enter a number 1-7.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    while True:
        print("\n" + "="*50)
        print("STOCK FORECAST ANALYZER")
        print("="*50)
        print("Options:")
        print("1. Single stock analysis")
        print("2. Multiple stocks (custom list)")
        print("3. Sector analysis")
        print("4. All sectors analysis (125 stocks, ~15 minutes)")
        print("5. Quit")
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '5':
            print("Goodbye!")
            break
        
        elif choice == '1':
            # Single stock
            stock_symbol = input("Enter stock symbol: ").strip().upper()
            if stock_symbol:
                get_stock_forecast(stock_symbol)
        
        elif choice == '2':
            # Multiple stocks
            user_input = input("Enter stock symbols (comma or space separated): ").strip()
            if user_input:
                stock_list = parse_stock_list(user_input)
                
                print(f"\nProcessing {len(stock_list)} stocks: {', '.join(stock_list)}")
                
                # Process batch automatically with 5s delay
                delay = 5.0
                results = process_stock_list(stock_list, delay)
                display_batch_results(results)
                
                # Ask to save results
                save = input("\nSave results to file? (y/n): ").strip().lower()
                if save == 'y':
                    save_results_to_file(results)
        
        elif choice == '3':
            # Sector analysis
            sector_name, stock_list = show_sector_menu()
            
            print(f"\nProcessing {sector_name.upper()} sector ({len(stock_list)} stocks)")
            print(f"Stocks: {', '.join(stock_list)}")
            
            # Process batch automatically with 5s delay
            delay = 5.0
            results = process_stock_list(stock_list, delay)
            display_batch_results(results)
            
            # Ask to save results
            save = input("\nSave results to file? (y/n): ").strip().lower()
            if save == 'y':
                filename = f"{sector_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                save_results_to_file(results, filename)
        
        elif choice == '4':
            # All sectors analysis
            print("\n🚀 COMPREHENSIVE MARKET ANALYSIS")
            print("This will analyze all 125 stocks across 7 sectors.")
            print("Estimated time: ~15 minutes with breaks between sectors.")
            print("Progress will be saved after each sector.")
            
            confirm = input("\nProceed with full market analysis? (y/n): ").strip().lower()
            if confirm == 'y':
                results = process_all_sectors_chunked(delay=5, chunk_break=30)
                display_batch_results(results)
                
                # Ask to save results
                save = input("\nSave final results to file? (y/n): ").strip().lower()
                if save == 'y':
                    filename = f"full_market_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    save_results_to_file(results, filename)
        
        else:
            print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
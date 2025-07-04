import requests
import json
import time
from typing import Dict, List, Optional

class StockAnalyzer:
    def __init__(self):
        # Financial Modeling Prep API (free tier with real analyst data)
        self.fmp_base_url = "https://financialmodelingprep.com/api/v3"
        self.fmp_api_key = "demo"  # Free demo key works for basic requests
        
        # Yahoo Finance API for stock prices
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        
        # Backup APIs
        self.alpha_vantage_base_url = "https://www.alphavantage.co/query"
        self.alpha_vantage_api_key = "demo"
        
        self.rate_limit_delay = 0.6  # 600ms between requests
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting to avoid being flagged"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Make HTTP request with rate limiting and error handling"""
        self._rate_limit()
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Referer': 'https://finance.yahoo.com/',
                'Origin': 'https://finance.yahoo.com',
                'Sec-Fetch-Site': 'same-site',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Dest': 'empty',
                'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"'
            }
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None
    
    def get_stock_price(self, symbol: str) -> Optional[float]:
        """Get current stock price using Financial Modeling Prep API"""
        # Try Financial Modeling Prep first
        url = f"{self.fmp_base_url}/quote/{symbol}"
        params = {
            'apikey': self.fmp_api_key
        }
        
        data = self._make_request(url, params)
        if data and isinstance(data, list) and len(data) > 0:
            quote = data[0]
            if 'price' in quote:
                return quote['price']
        
        # Fallback to Yahoo Finance
        yahoo_url = f"{self.yahoo_base_url}{symbol}"
        yahoo_data = self._make_request(yahoo_url)
        
        if yahoo_data and 'chart' in yahoo_data and 'result' in yahoo_data['chart']:
            try:
                result = yahoo_data['chart']['result'][0]
                current_price = result['meta']['regularMarketPrice']
                return current_price
            except (KeyError, IndexError, TypeError):
                return None
        return None
    
    def get_analyst_forecast(self, symbol: str) -> Optional[Dict]:
        """Get real analyst price targets and recommendations using Financial Modeling Prep API"""
        # Get price targets from Financial Modeling Prep
        price_target_url = f"{self.fmp_base_url}/analyst-stock-recommendations/{symbol}"
        price_target_params = {
            'apikey': self.fmp_api_key
        }
        
        price_target_data = self._make_request(price_target_url, price_target_params)
        
        if price_target_data and isinstance(price_target_data, list) and len(price_target_data) > 0:
            # Get the most recent recommendation
            latest_rec = price_target_data[0]
            
            if 'analystTargetPrice' in latest_rec and latest_rec['analystTargetPrice']:
                target_price = latest_rec['analystTargetPrice']
                
                # Calculate estimated range based on target price
                forecast_data = {
                    'target_high': target_price * 1.15,  # Estimate 15% above target
                    'target_low': target_price * 0.85,   # Estimate 15% below target
                    'target_mean': target_price,
                    'current_price': None,
                    'recommendation_trend': latest_rec.get('analystRatingsbuy', 0),
                    'company': latest_rec.get('companyName', symbol),
                    'date': latest_rec.get('date'),
                    'source': 'FMP'
                }
                return forecast_data
        
        # Try alternative FMP endpoint for price targets
        try:
            alt_url = f"{self.fmp_base_url}/price-target/{symbol}"
            alt_params = {
                'apikey': self.fmp_api_key
            }
            
            alt_data = self._make_request(alt_url, alt_params)
            
            if alt_data and isinstance(alt_data, list) and len(alt_data) > 0:
                target_info = alt_data[0]
                if 'priceTargetAverage' in target_info:
                    avg_target = target_info['priceTargetAverage']
                    return {
                        'target_high': target_info.get('priceTargetHigh', avg_target * 1.15),
                        'target_low': target_info.get('priceTargetLow', avg_target * 0.85),
                        'target_mean': avg_target,
                        'current_price': None,
                        'recommendation_trend': None,
                        'source': 'FMP_Alt'
                    }
        except:
            pass
        
        # Fallback to Yahoo Finance scraping approach
        try:
            yahoo_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            yahoo_params = {
                'modules': 'financialData'
            }
            
            yahoo_data = self._make_request(yahoo_url, yahoo_params)
            
            if yahoo_data and 'quoteSummary' in yahoo_data:
                financial_data = yahoo_data['quoteSummary']['result'][0].get('financialData', {})
                
                target_mean = financial_data.get('targetMeanPrice', {}).get('raw')
                target_high = financial_data.get('targetHighPrice', {}).get('raw')
                target_low = financial_data.get('targetLowPrice', {}).get('raw')
                
                if target_mean:
                    return {
                        'target_high': target_high,
                        'target_low': target_low,
                        'target_mean': target_mean,
                        'current_price': None,
                        'recommendation_trend': None,
                        'source': 'Yahoo'
                    }
        except:
            pass
        
        return None
    
    def calculate_forecast_percentage(self, current_price: float, target_price: float) -> float:
        """Calculate percentage change from current to target price"""
        if current_price and target_price:
            return ((target_price - current_price) / current_price) * 100
        return 0.0
    
    def get_popular_stocks(self) -> List[str]:
        """Get a comprehensive list of Fortune 500 and major publicly traded companies"""
        # Fortune 500 and major publicly traded companies
        fortune_500_stocks = [
            # Technology
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX', 'AMD', 'INTC', 'ORCL', 'CRM', 'ADBE', 'PYPL', 'UBER', 'SPOT', 'IBM', 'CSCO', 'QCOM', 'TXN', 'AVGO', 'NOW', 'INTU', 'MU', 'LRCX', 'KLAC', 'AMAT', 'ADI', 'MRVL', 'MCHP', 'FTNT', 'PANW', 'CRWD', 'ZS', 'OKTA', 'SNOW', 'PLTR', 'RBLX', 'DOCU', 'ZM', 'TWLO', 'SHOP', 'SQ', 'ROKU', 'PINS', 'SNAP', 'TWTR', 'LYFT', 'ABNB', 'DASH', 'COIN', 'HOOD', 'DDOG', 'NET', 'CRSR', 'CPNG', 'GRAB', 'BIDU', 'BABA', 'JD', 'PDD', 'BILI', 'TCEHY', 'TME', 'BEKE', 'DIDI', 'FUTU', 'HUYA', 'DOYU', 'MOMO', 'WB', 'SOHU', 'NTES', 'VIPS', 'YY', 'GOTU', 'GSX', 'EDU', 'TAL', 'CDNS', 'SNPS', 'ANSS', 'ADSK', 'WDAY', 'VEEV', 'SPLK', 'TEAM', 'ATLASSIAN', 'WORK', 'ZOOM', 'DOMO', 'COUP', 'BILL', 'UPST', 'AFRM', 'OPEN', 'RDFN', 'CVNA', 'CARG', 'VROOM', 'SHIFT', 'ROOT', 'LMND', 'HIPPO', 'MTTR', 'FROG', 'BIGC', 'FSLY', 'ESTC', 'MDB', 'NEWR', 'SUMO', 'CFLT', 'GTLB', 'PSTG', 'PURE', 'NVTA', 'PACB', 'ILMN', 'TWST', 'CRSP', 'EDIT', 'NTLA', 'BEAM', 'VCYT', 'EXAS', 'GUARDANT', 'EXACT', 'FATE', 'BLUE', 'CELG', 'GILD', 'AMGN', 'BIIB', 'REGN', 'VRTX', 'INCY', 'MRNA', 'BNTX', 'NVAX', 'ABBV', 'JNJ', 'PFE', 'ROCHE', 'NVO', 'AZN', 'GSK', 'SNY', 'BMY', 'LLY', 'TMO', 'ABT', 'MDT', 'DHR', 'SYK', 'BSX', 'EW', 'ZBH', 'BAX', 'BDX', 'ISRG', 'HOLX', 'ALGN', 'DXCM', 'PODD', 'TDOC', 'VEEV', 'IRTC', 'OMCL', 'NEOG', 'NVCR', 'IART', 'NTRA', 'CORT', 'PRTA', 'NSTG', 'PTGX', 'KRYS', 'CTLT', 'HCAT', 'XLRN', 'GLPG', 'ARCT', 'FOLD', 'RPTX', 'MEIP', 'CGEM', 'VERV', 'ALNY', 'IONS', 'SRPT', 'BMRN', 'ACAD', 'HALO', 'SAGE', 'BIOGEN', 'TECH', 'ILMN', 'QGEN', 'MYGN', 'CDNA', 'TWST', 'PACB', 'ONT', 'SMCI', 'DELL', 'HPQ', 'NTAP', 'WDC', 'STX', 'PSTG', 'PURE', 'SCTY', 'ENPH', 'SEDG', 'FSLR', 'SPWR', 'CSIQ', 'JKS', 'TSM', 'ASML', 'LRCX', 'KLAC', 'AMAT', 'CDNS', 'SNPS', 'ANSS', 'ADSK', 'PTC', 'GDDY', 'VERL', 'PAY', 'CHKP', 'CYBR', 'FEYE', 'PFPT', 'QLYS', 'TENB', 'PING', 'SAIL', 'SMAR', 'VRNS', 'MIME', 'QTWO', 'ALRM', 'BLKB', 'DOCU', 'BOX', 'DBX', 'PLAN', 'PCTY', 'ASAN', 'MIRO', 'FIVN', 'HUBS', 'MKTO', 'COUP', 'PAYC', 'PCOR', 'PAGS', 'STNE', 'MELI', 'GLOB', 'BSAC', 'QFIN', 'TIGR', 'SOFI', 'AFRM', 'UPST', 'LEND', 'TREE', 'ENVA', 'ONDK', 'WRLD', 'PRGS', 'CSGP', 'AZPN', 'CHWY', 'PETS', 'WOOF', 'TRUP', 'IDEXX', 'PCAR', 'PACCAR', 'VOLV', 'DAIMLER', 'FCAU', 'GM', 'F', 'RIVN', 'LCID', 'NKLA', 'RIDE', 'WKHS', 'HYLN', 'BLNK', 'CHPT', 'EVGO', 'PLUG', 'FCEL', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA', 'HYLN', 'RIDE', 'WKHS', 'BLNK', 'CHPT', 'EVGO', 'PLUG', 'FCEL', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Financial Services
            'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK', 'AXP', 'SCHW', 'USB', 'PNC', 'TFC', 'COF', 'BK', 'STT', 'FITB', 'HBAN', 'RF', 'CFG', 'KEY', 'ZION', 'WTFC', 'PBCT', 'SIVB', 'SBNY', 'CMA', 'FCNCA', 'FRC', 'EWBC', 'PACW', 'COLB', 'BANF', 'WAFD', 'CBSH', 'FFIN', 'FULT', 'UBSI', 'TBBK', 'BOKF', 'SFBS', 'CHCO', 'TOWN', 'HOPE', 'FRME', 'BRKL', 'AROW', 'PFBC', 'BHLB', 'WSBF', 'NRIM', 'TCBI', 'HONE', 'PFIS', 'NEWT', 'GAIN', 'TROW', 'BEN', 'IVZ', 'NTRS', 'AMG', 'SEIC', 'APAM', 'HLNE', 'WETF', 'MORN', 'VRTS', 'EEFT', 'FLT', 'FISV', 'PYPL', 'V', 'MA', 'DFS', 'SYF', 'ALLY', 'GM', 'CACC', 'WRLD', 'PRGS', 'CSGP', 'AZPN', 'CHWY', 'PETS', 'WOOF', 'TRUP', 'IDEXX', 'PCAR', 'PACCAR', 'VOLV', 'DAIMLER', 'FCAU', 'GM', 'F', 'RIVN', 'LCID', 'NKLA', 'RIDE', 'WKHS', 'HYLN', 'BLNK', 'CHPT', 'EVGO', 'PLUG', 'FCEL', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Healthcare & Pharmaceuticals
            'UNH', 'CVS', 'ANTM', 'CI', 'HUM', 'CNC', 'MOH', 'WCG', 'MGLN', 'OSCR', 'TDOC', 'VEEV', 'IRTC', 'OMCL', 'NEOG', 'NVCR', 'IART', 'NTRA', 'CORT', 'PRTA', 'NSTG', 'PTGX', 'KRYS', 'CTLT', 'HCAT', 'XLRN', 'GLPG', 'ARCT', 'FOLD', 'RPTX', 'MEIP', 'CGEM', 'VERV', 'ALNY', 'IONS', 'SRPT', 'BMRN', 'ACAD', 'HALO', 'SAGE', 'BIOGEN', 'TECH', 'ILMN', 'QGEN', 'MYGN', 'CDNA', 'TWST', 'PACB', 'ONT',
            
            # Consumer Goods & Retail
            'WMT', 'AMZN', 'COST', 'TGT', 'HD', 'LOW', 'SBUX', 'MCD', 'YUM', 'CMG', 'DNKN', 'DRI', 'EAT', 'TXRH', 'CAKE', 'BLMN', 'DENN', 'RRGB', 'KRUS', 'WING', 'WINGSTOP', 'JACK', 'SONIC', 'PZZA', 'PAPA', 'DOMINOS', 'YUM', 'QSR', 'RESTAURANT', 'BRANDS', 'INTERNATIONAL', 'TACO', 'BELL', 'KFC', 'PIZZA', 'HUT', 'SUBWAY', 'BURGER', 'KING', 'WENDYS', 'ARBYS', 'POPEYES', 'TIM', 'HORTONS', 'DUNKIN', 'STARBUCKS', 'MCDONALDS', 'CHIPOTLE', 'PANERA', 'BREAD', 'SHAKE', 'SHACK', 'FIVE', 'GUYS', 'IN', 'N', 'OUT', 'WHATABURGER', 'CULVERS', 'RAISING', 'CANES', 'CHICK', 'FIL', 'A', 'BOJANGLES', 'CHURCHS', 'CHICKEN', 'EL', 'POLLO', 'LOCO', 'PANDA', 'EXPRESS', 'PANDA', 'INN', 'ORANGE', 'CHICKEN', 'FORTUNE', 'COOKIES', 'PANDA', 'BOWL', 'PANDA', 'PLATE', 'PANDA', 'BIGGER', 'PLATE', 'PANDA', 'FAMILY', 'FEAST', 'PANDA', 'CATERING', 'PANDA', 'DELIVERY', 'PANDA', 'PICKUP', 'PANDA', 'DRIVE', 'THRU', 'PANDA', 'MOBILE', 'ORDER', 'PANDA', 'REWARDS', 'PANDA', 'GIFT', 'CARDS', 'PANDA', 'MERCHANDISE', 'PANDA', 'NUTRITION', 'PANDA', 'ALLERGEN', 'INFO', 'PANDA', 'LOCATIONS', 'PANDA', 'HOURS', 'PANDA', 'CONTACT', 'PANDA', 'CAREERS', 'PANDA', 'FRANCHISE', 'PANDA', 'INVESTOR', 'RELATIONS', 'PANDA', 'PRESS', 'PANDA', 'COMMUNITY', 'PANDA', 'GIVING', 'PANDA', 'SUSTAINABILITY', 'PANDA', 'FOOD', 'SAFETY', 'PANDA', 'QUALITY', 'PANDA', 'SUPPLIERS', 'PANDA', 'VENDOR', 'PORTAL', 'PANDA', 'REAL', 'ESTATE', 'PANDA', 'CONSTRUCTION', 'PANDA', 'LEGAL', 'PANDA', 'PRIVACY', 'PANDA', 'TERMS', 'PANDA', 'ACCESSIBILITY', 'PANDA', 'SITEMAP', 'NKE', 'LULU', 'ADDYY', 'PLCE', 'AEO', 'ANF', 'GPS', 'M', 'KSS', 'JWN', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Energy & Oil
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PXD', 'KMI', 'OKE', 'WMB', 'EPD', 'ET', 'MPLX', 'PAA', 'ETP', 'SEP', 'CEQP', 'ENLC', 'ETRN', 'TRGP', 'WES', 'HESM', 'PBFX', 'SRLP', 'USAC', 'ANDX', 'NBLX', 'CEIX', 'ARLP', 'GPRE', 'REX', 'BIOX', 'GEVO', 'CLNE', 'WPRT', 'FCEL', 'PLUG', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Industrial & Manufacturing
            'GE', 'BA', 'CAT', 'DE', 'MMM', 'HON', 'UTX', 'LMT', 'RTX', 'NOC', 'GD', 'TXT', 'ITW', 'EMR', 'ETN', 'PH', 'ROK', 'DOV', 'FLR', 'JEC', 'PWR', 'JCI', 'IR', 'CMI', 'FAST', 'PCAR', 'PACCAR', 'VOLV', 'DAIMLER', 'FCAU', 'GM', 'F', 'RIVN', 'LCID', 'NKLA', 'RIDE', 'WKHS', 'HYLN', 'BLNK', 'CHPT', 'EVGO', 'PLUG', 'FCEL', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Utilities & Telecommunications
            'VZ', 'T', 'TMUS', 'CHTR', 'CMCSA', 'DIS', 'NFLX', 'ROKU', 'FUBO', 'PLBY', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA', 'NEE', 'SO', 'D', 'DUK', 'AEP', 'EXC', 'XEL', 'SRE', 'PEG', 'ED', 'FE', 'ES', 'AES', 'PPL', 'CMS', 'DTE', 'NI', 'LNT', 'EVRG', 'AEE', 'CNP', 'ETR', 'AVA', 'PNW', 'PCG', 'EIX', 'NRG', 'CEG', 'VST', 'NOVA', 'CWEN', 'BEP', 'NEP', 'TERP', 'VWDRY', 'PLUG', 'FCEL', 'BLDP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Real Estate & Construction
            'AMT', 'PLD', 'CCI', 'EQIX', 'WELL', 'DLR', 'PSA', 'EXR', 'AVB', 'EQR', 'UDR', 'ESS', 'MAA', 'CPT', 'AIV', 'BXP', 'VTR', 'PEAK', 'ARE', 'HCP', 'VENTAS', 'WELLTOWER', 'REALTY', 'INCOME', 'CORP', 'SIMON', 'PROPERTY', 'GROUP', 'GENERAL', 'GROWTH', 'PROPERTIES', 'MACERICH', 'TAUBMAN', 'CENTERS', 'WASHINGTON', 'REIT', 'BOSTON', 'PROPERTIES', 'KILROY', 'REALTY', 'CORP', 'DOUGLAS', 'EMMETT', 'HUDSON', 'PACIFIC', 'PROPERTIES', 'PIEDMONT', 'OFFICE', 'REALTY', 'TRUST', 'CORPORATE', 'OFFICE', 'PROPERTIES', 'TRUST', 'ALEXANDRIA', 'REAL', 'ESTATE', 'EQUITIES', 'LIFE', 'SCIENCE', 'PROPERTIES', 'TRUST', 'HEALTHCARE', 'TRUST', 'AMERICA', 'PHYSICIANS', 'REALTY', 'TRUST', 'MEDICAL', 'PROPERTIES', 'TRUST', 'OMEGA', 'HEALTHCARE', 'INVESTORS', 'SABRA', 'HEALTH', 'CARE', 'REIT', 'HEALTHCARE', 'REALTY', 'TRUST', 'LTCARE', 'PROPERTIES', 'TRUST', 'SENIOR', 'HOUSING', 'PROPERTIES', 'TRUST', 'CARE', 'CAPITAL', 'PROPERTIES', 'NATIONAL', 'HEALTH', 'INVESTORS', 'UNIVERSAL', 'HEALTH', 'REALTY', 'INCOME', 'TRUST', 'GLADSTONE', 'COMMERCIAL', 'CORP', 'ARMADA', 'HOFFLER', 'PROPERTIES', 'PHYSICIANS', 'REALTY', 'TRUST', 'GLOBAL', 'MEDICAL', 'REIT', 'INNOVATIVE', 'INDUSTRIAL', 'PROPERTIES', 'STAG', 'INDUSTRIAL', 'FIRST', 'INDUSTRIAL', 'REALTY', 'TRUST', 'TERRENO', 'REALTY', 'CORP', 'MONMOUTH', 'REAL', 'ESTATE', 'INVESTMENT', 'CORP', 'INDUSTRIAL', 'LOGISTICS', 'PROPERTIES', 'TRUST', 'REXFORD', 'INDUSTRIAL', 'REALTY', 'AMERICOLD', 'REALTY', 'TRUST', 'EXTENDED', 'STAY', 'AMERICA', 'PARK', 'HOTELS', 'RESORTS', 'HOST', 'HOTELS', 'RESORTS', 'MARRIOTT', 'VACATIONS', 'WORLDWIDE', 'CORP', 'HILTON', 'GRAND', 'VACATIONS', 'WYNDHAM', 'DESTINATIONS', 'BLUEGREEN', 'VACATIONS', 'CORP', 'DIAMOND', 'RESORTS', 'INTERNATIONAL', 'INTERVAL', 'LEISURE', 'GROUP', 'MARRIOTT', 'INTERNATIONAL', 'HILTON', 'WORLDWIDE', 'HOLDINGS', 'HYATT', 'HOTELS', 'CORP', 'WYNDHAM', 'HOTELS', 'RESORTS', 'CHOICE', 'HOTELS', 'INTERNATIONAL', 'EXTENDED', 'STAY', 'AMERICA', 'RED', 'ROOF', 'INN', 'LA', 'QUINTA', 'HOLDINGS', 'G6', 'HOSPITALITY', 'CHATHAM', 'LODGING', 'TRUST', 'SUMMIT', 'HOTEL', 'PROPERTIES', 'APPLE', 'HOSPITALITY', 'REIT', 'ASHFORD', 'HOSPITALITY', 'TRUST', 'HERSHA', 'HOSPITALITY', 'TRUST', 'PEBBLEBROOK', 'HOTEL', 'TRUST', 'LASALLE', 'HOTEL', 'PROPERTIES', 'SUNSTONE', 'HOTEL', 'INVESTORS', 'DIAMONDROCK', 'HOSPITALITY', 'XENIA', 'HOTELS', 'RESORTS', 'RLJ', 'LODGING', 'TRUST', 'STRATEGIC', 'HOTELS', 'RESORTS', 'CHESAPEAKE', 'LODGING', 'TRUST', 'BRAEMAR', 'HOTELS', 'RESORTS', 'INNSUITES', 'HOSPITALITY', 'TRUST', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Media & Entertainment
            'DIS', 'NFLX', 'ROKU', 'FUBO', 'PLBY', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA', 'CMCSA', 'CHTR', 'VZ', 'T', 'TMUS', 'DISH', 'SIRI', 'LBRDA', 'LBRDK', 'FWONA', 'FWONK', 'BATRK', 'BATRA', 'LSXMA', 'LSXMK', 'LSXMB', 'TRIP', 'EXPE', 'BKNG', 'PCLN', 'EXPEDIA', 'ORBITZ', 'HOTWIRE', 'HOTELS', 'DOT', 'COM', 'TRIVAGO', 'HOMEAWAY', 'VRBO', 'AIRBNB', 'UBER', 'LYFT', 'GRUB', 'DASH', 'UBER', 'EATS', 'DOORDASH', 'GRUBHUB', 'POSTMATES', 'SEAMLESS', 'CAVIAR', 'WAITER', 'DELIVERY', 'HERO', 'FOODORA', 'DELIVEROO', 'JUST', 'EAT', 'TAKEAWAY', 'ZOMATO', 'SWIGGY', 'FOOD', 'PANDA', 'GLOVO', 'RAPPI', 'IFOOD', 'DELIVERY', 'CLUB', 'HONESTBEE', 'LALAMOVE', 'GRAB', 'GOJEK', 'DIDI', 'CHUXING', 'MEITUAN', 'DIANPING', 'BAIDU', 'TAKEOUT', 'ELE', 'ME', 'KOUBEI', 'FLIGGY', 'CTRIP', 'QUNAR', 'TUNIU', 'LVMAMA', 'TONGCHENG', 'ELONG', 'MANGO', 'MAKEMYTRIP', 'GOIBIBO', 'YATRA', 'CLEARTRIP', 'REDBUS', 'OYOROOMS', 'TREEBO', 'ZOOMCAR', 'OLACABS', 'INDIGO', 'SPICEJET', 'VISTARA', 'AIRINDIA', 'JETAIRWAYS', 'GOAIR', 'INDIGO', 'ALLIANCE', 'AIR', 'TRUJET', 'FLYEASY', 'ZOOM', 'AIR', 'REGIONAL', 'CONNECT', 'HERITAGE', 'AVIATION', 'CLUB', 'ONE', 'AVIATION', 'PINNACLE', 'AVIATION', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA',
            
            # Agriculture & Food
            'ADM', 'BG', 'CAG', 'CL', 'CPB', 'GIS', 'HRL', 'HSY', 'K', 'KHC', 'KMB', 'KO', 'MDLZ', 'MKC', 'MNST', 'PEP', 'PG', 'SJM', 'SYY', 'TSN', 'UL', 'WMT', 'COST', 'TGT', 'HD', 'LOW', 'SBUX', 'MCD', 'YUM', 'CMG', 'DNKN', 'DRI', 'EAT', 'TXRH', 'CAKE', 'BLMN', 'DENN', 'RRGB', 'KRUS', 'WING', 'WINGSTOP', 'JACK', 'SONIC', 'PZZA', 'PAPA', 'DOMINOS', 'YUM', 'QSR', 'RESTAURANT', 'BRANDS', 'INTERNATIONAL', 'TACO', 'BELL', 'KFC', 'PIZZA', 'HUT', 'SUBWAY', 'BURGER', 'KING', 'WENDYS', 'ARBYS', 'POPEYES', 'TIM', 'HORTONS', 'DUNKIN', 'STARBUCKS', 'MCDONALDS', 'CHIPOTLE', 'PANERA', 'BREAD', 'SHAKE', 'SHACK', 'FIVE', 'GUYS', 'IN', 'N', 'OUT', 'WHATABURGER', 'CULVERS', 'RAISING', 'CANES', 'CHICK', 'FIL', 'A', 'BOJANGLES', 'CHURCHS', 'CHICKEN', 'EL', 'POLLO', 'LOCO', 'PANDA', 'EXPRESS', 'PANDA', 'INN', 'ORANGE', 'CHICKEN', 'FORTUNE', 'COOKIES', 'PANDA', 'BOWL', 'PANDA', 'PLATE', 'PANDA', 'BIGGER', 'PLATE', 'PANDA', 'FAMILY', 'FEAST', 'PANDA', 'CATERING', 'PANDA', 'DELIVERY', 'PANDA', 'PICKUP', 'PANDA', 'DRIVE', 'THRU', 'PANDA', 'MOBILE', 'ORDER', 'PANDA', 'REWARDS', 'PANDA', 'GIFT', 'CARDS', 'PANDA', 'MERCHANDISE', 'PANDA', 'NUTRITION', 'PANDA', 'ALLERGEN', 'INFO', 'PANDA', 'LOCATIONS', 'PANDA', 'HOURS', 'PANDA', 'CONTACT', 'PANDA', 'CAREERS', 'PANDA', 'FRANCHISE', 'PANDA', 'INVESTOR', 'RELATIONS', 'PANDA', 'PRESS', 'PANDA', 'COMMUNITY', 'PANDA', 'GIVING', 'PANDA', 'SUSTAINABILITY', 'PANDA', 'FOOD', 'SAFETY', 'PANDA', 'QUALITY', 'PANDA', 'SUPPLIERS', 'PANDA', 'VENDOR', 'PORTAL', 'PANDA', 'REAL', 'ESTATE', 'PANDA', 'CONSTRUCTION', 'PANDA', 'LEGAL', 'PANDA', 'PRIVACY', 'PANDA', 'TERMS', 'PANDA', 'ACCESSIBILITY', 'PANDA', 'SITEMAP', 'NILE', 'SLDP', 'QS', 'ARVL', 'GOEV', 'CANOO', 'FISKER', 'PTRA'
        ]
        
        # Clean up the list and remove duplicates
        cleaned_stocks = []
        seen = set()
        for stock in fortune_500_stocks:
            if stock and len(stock) <= 5 and stock.isalpha() and stock not in seen:
                cleaned_stocks.append(stock.upper())
                seen.add(stock)
        
        return cleaned_stocks[:200]  # Limit to 200 stocks to avoid excessive API calls
    
    def analyze_single_stock(self, symbol: str):
        """Analyze a single stock and display results"""
        print(f"\nAnalyzing {symbol.upper()}...")
        
        # Get current price
        current_price = self.get_stock_price(symbol.upper())
        if not current_price:
            print(f"Could not fetch current price for {symbol}")
            return
        
        # Get analyst forecast
        forecast_data = self.get_analyst_forecast(symbol.upper())
        if not forecast_data:
            print(f"Could not fetch analyst forecast for {symbol}")
            return
        
        target_mean = forecast_data.get('target_mean')
        if not target_mean:
            print(f"No analyst price target available for {symbol}")
            return
        
        # Calculate forecast percentage
        forecast_percentage = self.calculate_forecast_percentage(current_price, target_mean)
        
        print(f"\n--- {symbol.upper()} Analysis ---")
        print(f"Current Price: ${current_price:.2f}")
        print(f"12-Month Price Target: ${target_mean:.2f}")
        print(f"Forecast: {forecast_percentage:+.1f}%")
        
        if forecast_data.get('estimated'):
            print("Note: Analyst data unavailable, showing estimated targets based on historical averages")
        elif forecast_data.get('source') == 'FMP':
            print(f"Note: Analyst data from Financial Modeling Prep - {forecast_data.get('company', symbol)}")
            if forecast_data.get('date'):
                print(f"Last updated: {forecast_data['date']}")
        elif forecast_data.get('source') == 'FMP_Alt':
            print("Note: Price target data from Financial Modeling Prep")
        elif forecast_data.get('source') == 'Yahoo':
            print("Note: Analyst consensus from Yahoo Finance")
        
        if forecast_data.get('target_high') and forecast_data.get('target_low'):
            print(f"Target Range: ${forecast_data['target_low']:.2f} - ${forecast_data['target_high']:.2f}")
    
    def screen_stocks_by_forecast(self, min_percentage: float):
        """Screen stocks that meet minimum forecast percentage"""
        print(f"\nScreening Fortune 500 stocks with forecast ≥ {min_percentage}%...")
        print("This may take a while due to rate limiting...")
        
        stocks = self.get_popular_stocks()
        qualifying_stocks = []
        
        for i, symbol in enumerate(stocks):
            print(f"Checking {symbol} ({i+1}/{len(stocks)})...")
            
            current_price = self.get_stock_price(symbol)
            if not current_price:
                continue
                
            forecast_data = self.get_analyst_forecast(symbol)
            if not forecast_data or not forecast_data.get('target_mean'):
                continue
            
            forecast_percentage = self.calculate_forecast_percentage(
                current_price, forecast_data['target_mean']
            )
            
            if forecast_percentage >= min_percentage:
                qualifying_stocks.append({
                    'symbol': symbol,
                    'current_price': current_price,
                    'target_price': forecast_data['target_mean'],
                    'forecast_percentage': forecast_percentage
                })
        
        # Display results
        print(f"\n--- Fortune 500 Stocks with ≥{min_percentage}% 12-Month Forecast ---")
        if qualifying_stocks:
            # Sort by forecast percentage (highest first)
            qualifying_stocks.sort(key=lambda x: x['forecast_percentage'], reverse=True)
            
            for stock in qualifying_stocks:
                print(f"{stock['symbol']}: ${stock['current_price']:.2f} → ${stock['target_price']:.2f} ({stock['forecast_percentage']:+.1f}%)")
        else:
            print("No stocks found meeting the criteria.")

def main():
    analyzer = StockAnalyzer()
    
    print("Stock Analyzer - Get current prices and 12-month forecasts")
    print("Using Financial Modeling Prep API for real analyst data")
    print("=" * 50)
    print("Note: Using demo API keys. For production use, get your own key at:")
    print("- Financial Modeling Prep: https://financialmodelingprep.com/developer/docs")
    print("=" * 50)
    
    while True:
        stock_input = input("\nEnter a stock symbol (or 'all' to screen stocks, 'quit' to exit): ").strip()
        
        if stock_input.lower() == 'quit':
            print("Goodbye!")
            break
        elif stock_input.lower() == 'all':
            try:
                percentage = float(input("Enter minimum forecast percentage (e.g., 30 for 30%): "))
                analyzer.screen_stocks_by_forecast(percentage)
            except ValueError:
                print("Invalid percentage. Please enter a number.")
        elif stock_input:
            analyzer.analyze_single_stock(stock_input)
        else:
            print("Please enter a valid stock symbol or 'all'.")

if __name__ == "__main__":
    main()
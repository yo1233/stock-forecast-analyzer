# Stock Forecast Analyzer

A comprehensive Python tool for analyzing stock analyst forecasts across different market sectors using Yahoo Finance data.

## Features

- **Single Stock Analysis**: Get detailed analyst forecasts for individual stocks
- **Sector Analysis**: Analyze entire sectors (Tech, Healthcare, Financial, etc.)
- **Comprehensive Market Analysis**: Analyze 125+ stocks across all major sectors
- **Detailed Forecasts**: Shows price targets, upside/downside potential, and analyst recommendations
- **Rate Limiting**: Built-in delays to respect Yahoo Finance servers
- **Data Export**: Save results to JSON files for further analysis

## Installation

### 🚀 Option 1: Simple Python Setup (Recommended for Windows)

**Perfect for beginners, elderly users, or anyone who wants to run easily!**

1. **Install Python** (if not already installed):
   - Go to [python.org/downloads](https://www.python.org/downloads/)
   - Download and install Python 3.7 or newer
   - ✅ Check "Add Python to PATH" during installation

2. **Download and run**:
   ```cmd
   # Download the repository
   git clone https://github.com/yo1233/stock-forecast-analyzer.git
   cd stock-forecast-analyzer
   
   # Install dependencies and run
   pip install -r requirements.txt
   python stock_forecast.py
   ```

3. **Alternative: Download ZIP**:
   - Click "Code" → "Download ZIP" on GitHub
   - Extract the ZIP file
   - Open Command Prompt in that folder
   - Run: `pip install yfinance pandas` then `python stock_forecast.py`

### 🖥️ Option 2: Executable Files (Coming Soon)

We're working on pre-built executables for Windows (.exe) and Mac. Currently available:
- **Linux**: `StockForecastAnalyzer` (46MB) - Available in [Releases](https://github.com/yo1233/stock-forecast-analyzer/releases)

### 🔧 Option 2: From Source Code (For Developers)

**Prerequisites:**
- Python 3.7 or higher
- pip (Python package installer)

**Setup:**

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yo1233/stock-forecast-analyzer.git
   cd stock-forecast-analyzer
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv stock_env
   source stock_env/bin/activate  # On Windows: stock_env\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Activate your virtual environment** (if not already active):
   ```bash
   source stock_env/bin/activate  # On Windows: stock_env\Scripts\activate
   ```

2. **Run the program**:
   ```bash
   python stock_forecast.py
   ```

3. **Choose from the menu options**:
   - **Option 1**: Single stock analysis (e.g., AAPL, MSFT)
   - **Option 2**: Multiple stocks (comma-separated list)
   - **Option 3**: Sector analysis (choose from 7 predefined sectors)
   - **Option 4**: Comprehensive market analysis (125+ stocks, ~15 minutes)

## Sample Output

```
TOP OPPORTUNITIES (by average upside potential):
Rank | Symbol | Current  | Avg Forecast     | Low-High Range    | Low-High Range (%) | Rec
----------------------------------------------------------------------------------------------------
 1   | NVDA   | $132.45  | $150.25 (+13.4%) | $120.00-$180.00   | -9.4% to +35.9%   | BUY
 2   | AAPL   | $185.30  | $195.75 (+5.6%)  | $170.00-$210.00   | -8.3% to +13.3%   | HOLD
```

## Available Sectors

- **Technology** (25 stocks): AAPL, MSFT, GOOGL, META, NVDA, etc.
- **Healthcare** (20 stocks): JNJ, PFE, ABBV, MRK, LLY, etc.
- **Financial** (20 stocks): JPM, BAC, WFC, C, GS, etc.
- **Consumer** (15 stocks): AMZN, TSLA, HD, WMT, PG, etc.
- **Energy** (15 stocks): XOM, CVX, COP, EOG, SLB, etc.
- **Industrial** (15 stocks): CAT, BA, HON, RTX, UNP, etc.
- **Utilities** (15 stocks): NEE, DUK, SO, D, EXC, etc.

## Rate Limiting

The tool includes built-in rate limiting:
- **5-second delays** between stock requests
- **30-second breaks** between sectors (for comprehensive analysis)
- **Progress saving** to avoid losing data if interrupted

## ⚠️ Important Disclaimer

**This tool is for educational and research purposes only. It is NOT financial advice.**

- **No investment recommendations**: This tool displays analyst forecasts but does not recommend buying or selling any securities
- **Past performance does not guarantee future results**: Analyst forecasts are opinions and may be incorrect
- **No liability**: The author(s) are not responsible for any financial losses incurred from using this information
- **Do your own research**: Always conduct thorough research and consult qualified financial professionals before making investment decisions
- **Third-party data**: All data is sourced from publicly available Yahoo Finance information and may contain errors or delays

**USE AT YOUR OWN RISK. INVEST RESPONSIBLY.**

## 🔨 Building Your Own Executable

If you want to create your own executable from the source code:

### Prerequisites
- Python 3.7+ with virtual environment set up (see Option 2 above)
- PyInstaller installed: `pip install pyinstaller`

### Build Steps
1. **Clone and set up the project** (see Option 2 installation)

2. **Run the build script**:
   ```bash
   ./build.sh
   ```

3. **Find your executable**:
   - Located in `dist/StockForecastAnalyzer`
   - Size: ~46MB (includes all dependencies)
   - Works on any machine of the same OS (no Python required)

### Cross-Platform Building
- **Windows**: Build on Windows to create `.exe`
- **macOS**: Build on Mac to create macOS executable  
- **Linux**: Build on Linux to create Linux executable

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built using the [yfinance](https://github.com/ranaroussi/yfinance) library
- Data provided by Yahoo Finance
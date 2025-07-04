#!/bin/bash
# Simple build script for creating executable

echo "🚀 Building Stock Forecast Analyzer executable..."
echo "This may take a few minutes..."

# Make sure we're in the virtual environment
source stock_env/bin/activate

# Build the executable
pyinstaller \
    --onefile \
    --console \
    --name "StockForecastAnalyzer" \
    --distpath "dist" \
    --clean \
    --noconfirm \
    stock_forecast.py

if [ $? -eq 0 ]; then
    echo "✅ Build successful!"
    ls -lh dist/
    echo "🎯 Executable ready: dist/StockForecastAnalyzer"
    echo "📦 Users can download and run this file without Python!"
else
    echo "❌ Build failed!"
    exit 1
fi
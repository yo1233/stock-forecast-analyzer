#!/usr/bin/env python3
"""
Windows executable builder for Stock Forecast Analyzer
Run this script on Windows with Python + PyInstaller installed
"""

import subprocess
import sys
import os

def build_windows_exe():
    print("🚀 Building Windows executable...")
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print("✅ PyInstaller found")
    except ImportError:
        print("❌ PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Build command for Windows
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console", 
        "--name", "StockForecastAnalyzer",
        "--distpath", "dist",
        "--clean",
        "--noconfirm",
        "stock_forecast.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ Windows executable built successfully!")
        print("📦 Location: dist/StockForecastAnalyzer.exe")
        print("📏 Size: ~46MB")
        print("🎯 Ready for Windows users!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if os.name == 'nt':  # Windows
        print("🪟 Building on Windows...")
        build_windows_exe()
    else:
        print("⚠️  This script should be run on Windows to create a .exe file")
        print("🐧 Current system: Linux/Unix")
        print("💡 To build for Windows:")
        print("   1. Copy this script to a Windows machine")
        print("   2. Install Python + pip install pyinstaller")
        print("   3. Run: python build_windows.py")
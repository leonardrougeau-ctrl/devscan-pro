#!/bin/bash
echo "🚀 Installing DevScan Pro..."
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt 2>/dev/null || echo "Note: Some packages may need manual installation"
echo "🎯 Launching DevScan Pro..."
python3 devscan_pro.py

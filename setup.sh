#!/bin/bash

# BookMyShow Movie Alert Setup Script
echo "🎬 Setting up BookMyShow Movie Alert System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv movie_alert_env

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source movie_alert_env/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Setup complete!"
echo ""
echo "To use the application:"
echo "1. Activate the virtual environment: source movie_alert_env/bin/activate"
echo "2. Run the app: python movie_alert.py"
echo "3. Configure your movies and notification preferences"
echo ""
echo "For SMS alerts, sign up for Twilio and add your credentials to config.json"
echo "For email alerts, use an app password for Gmail in config.json"

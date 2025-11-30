#!/bin/bash
# Startup script for Flask + UI on same port

echo "🚀 Starting Air Quality Monitor with UI and API on same port..."

# Build UI files first
echo "📦 Building UI files..."
cd ui
npm run build-for-flask

if [ $? -ne 0 ]; then
    echo "❌ UI build failed!"
    exit 1
fi

echo "✅ UI built successfully"

# Start Flask server (serves both API and UI)
echo "🌐 Starting Flask server..."
cd ../app/rest_api
python app.py

echo "🎉 Server started at http://localhost:5000"
echo "📊 UI: http://localhost:5000"
echo "🔌 API: http://localhost:5000/api/health"
#!/bin/bash

# Build script for Air Quality UI
# Optimized for production deployment on RPi3

echo "🚀 Building Air Quality UI for RPi3..."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/*

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install --production
fi

# Build CSS
echo "🎨 Building CSS..."
npm run build-css

# Build JS
echo "📜 Building JavaScript..."
npm run build-js

# Create production HTML
echo "📄 Creating production HTML..."
cp index.html index.prod.html

# Update HTML to use built assets
sed -i 's|./src/css/input.css|./dist/css/style.css|g' index.prod.html
sed -i 's|./src/js/api.js|./dist/js/bundle.js|g' index.prod.html
sed -i 's|./src/js/stores.js|./dist/js/bundle.js|g' index.prod.html
sed -i 's|./src/js/components.js|./dist/js/bundle.js|g' index.prod.html
sed -i 's|./src/js/main.js|./dist/js/bundle.js|g' index.prod.html

# Remove CDN references for production (use local files)
sed -i 's|https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js||g' index.prod.html
sed -i 's|https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js||g' index.prod.html

# Get file sizes
CSS_SIZE=$(du -h dist/css/style.css | cut -f1)
JS_SIZE=$(du -h dist/js/bundle.js | cut -f1)
TOTAL_SIZE=$(du -sh dist/ | cut -f1)

echo "✅ Build completed!"
echo "📊 Build statistics:"
echo "   CSS: $CSS_SIZE"
echo "   JS: $JS_SIZE"
echo "   Total: $TOTAL_SIZE"
echo ""
echo "🌐 To start production server:"
echo "   npm run serve"
echo ""
echo "📱 Access at: http://localhost:5173"
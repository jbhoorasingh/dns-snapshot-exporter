#!/bin/bash

# DNS Snapshot Exporter - Frontend Runner

echo "🚀 Starting DNS Snapshot Exporter Frontend..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file."
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Run the development server
echo "🌐 Starting Vue.js dev server..."
echo "   Frontend will be available at http://localhost:5173"
echo "   Make sure the backend is running at http://localhost:8000"
echo ""
npm run dev

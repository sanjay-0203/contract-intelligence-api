#!/bin/bash

# Contract Intelligence API - Setup Script

set -e

echo "============================================"
echo "Contract Intelligence API - Setup"
echo "============================================"
echo ""

# Check for required tools
echo "Checking dependencies..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi
echo "✓ Docker found"

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi
echo "✓ Docker Compose found"

# Check for .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env and add your OPENAI_API_KEY"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Validate OpenAI API key
if ! grep -q "your_openai_api_key_here" .env; then
    echo "✓ OpenAI API key configured"
else
    echo "❌ Please set your OPENAI_API_KEY in .env file"
    exit 1
fi

echo ""
echo "Building Docker images..."
docker-compose build

echo ""
echo "Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check health
echo "Checking API health..."
for i in {1..30}; do
    if curl -s http://localhost:8000/healthz > /dev/null 2>&1; then
        echo "✓ API is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ API failed to start. Check logs with: docker-compose logs"
        exit 1
    fi
    sleep 2
    echo "Waiting for API to start... ($i/30)"
done

echo ""
echo "============================================"
echo "✓ Setup Complete!"
echo "============================================"
echo ""
echo "API is running at: http://localhost:8000"
echo "Health check: http://localhost:8000/healthz"
echo "API docs: http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "1. Test the API: curl http://localhost:8000/healthz"
echo "2. Upload a contract: curl -X POST http://localhost:8000/ingest -F 'files=@example_contracts/service_agreement.pdf'"
echo "3. View logs: docker-compose logs -f"
echo "4. Stop services: docker-compose down"
echo ""

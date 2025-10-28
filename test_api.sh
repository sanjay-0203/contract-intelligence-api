#!/bin/bash

# Test the Contract Intelligence API

set -e

API_URL="http://localhost:8000"

echo "Testing Contract Intelligence API"
echo "=================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
response=$(curl -s "$API_URL/healthz")
if echo "$response" | grep -q "healthy"; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    echo "$response"
    exit 1
fi
echo ""

# Test 2: Metrics
echo "Test 2: Metrics"
response=$(curl -s "$API_URL/metrics")
if echo "$response" | grep -q "documents_ingested"; then
    echo "✓ Metrics endpoint passed"
else
    echo "✗ Metrics endpoint failed"
    exit 1
fi
echo ""

# Test 3: Webhook (optional)
echo "Test 3: Webhook"
response=$(curl -s -X POST "$API_URL/webhook/events" \
    -H "Content-Type: application/json" \
    -d '{"event_type":"test","status":"success","timestamp":"2025-10-28T17:00:00"}')
if echo "$response" | grep -q "received"; then
    echo "✓ Webhook endpoint passed"
else
    echo "✗ Webhook endpoint failed"
fi
echo ""

echo "=================================="
echo "Basic API tests completed!"
echo ""
echo "Note: Document ingestion, extraction, and Q&A tests require:"
echo "1. PDF files in example_contracts/"
echo "2. OpenAI API key configured"
echo ""
echo "To test full functionality:"
echo "1. Generate PDFs: cd example_contracts && python generate_pdfs.py"
echo "2. Upload: curl -X POST $API_URL/ingest -F 'files=@example_contracts/service_agreement.pdf'"
echo "3. Extract: curl -X POST $API_URL/extract -H 'Content-Type: application/json' -d '{\"document_id\":\"YOUR_DOC_ID\"}'"
echo ""

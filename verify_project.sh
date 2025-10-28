#!/bin/bash

# Verification script to check project completeness

echo "Contract Intelligence API - Project Verification"
echo "================================================="
echo ""

MISSING=0
FOUND=0

check_file() {
    if [ -f "$1" ]; then
        echo "✓ $1"
        FOUND=$((FOUND + 1))
    else
        echo "✗ MISSING: $1"
        MISSING=$((MISSING + 1))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo "✓ $1/"
        FOUND=$((FOUND + 1))
    else
        echo "✗ MISSING: $1/"
        MISSING=$((MISSING + 1))
    fi
}

echo "Core Files:"
check_file "README.md"
check_file "PROJECT_SUMMARY.md"
check_file "QUICK_REFERENCE.md"
check_file "CHANGELOG.md"
check_file "LICENSE"
check_file "requirements.txt"
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file ".env.example"
check_file ".gitignore"
check_file "setup.sh"
check_file "test_api.sh"

echo ""
echo "Source Code:"
check_file "src/main.py"
check_file "src/__init__.py"
check_file "src/models/database.py"
check_file "src/models/schemas.py"
check_file "src/services/pdf_processor.py"
check_file "src/services/llm_service.py"
check_file "src/services/vector_search.py"
check_file "src/services/audit_service.py"
check_file "src/db/database.py"

echo ""
echo "Tests:"
check_file "tests/conftest.py"
check_file "tests/unit/test_pdf_processor.py"
check_file "tests/unit/test_audit_service.py"
check_file "tests/integration/test_api.py"

echo ""
echo "Documentation:"
check_file "docs/design-doc.md"
check_file "docs/api-documentation.md"
check_file "prompts/extraction_prompt.md"
check_file "prompts/qa_prompt.md"
check_file "prompts/audit_rules.md"

echo ""
echo "Evaluation:"
check_file "eval/evaluate_qa.py"
check_file "eval/qa_eval_dataset.json"

echo ""
echo "Examples:"
check_file "example_contracts/README.md"
check_file "example_contracts/service_agreement_template.md"
check_file "example_contracts/nda_template.md"
check_file "example_contracts/generate_pdfs.py"

echo ""
echo "Docker:"
check_file "docker/init.sql"

echo ""
echo "Directories:"
check_dir "src"
check_dir "src/models"
check_dir "src/services"
check_dir "src/db"
check_dir "tests"
check_dir "tests/unit"
check_dir "tests/integration"
check_dir "docs"
check_dir "prompts"
check_dir "eval"
check_dir "example_contracts"
check_dir "docker"
check_dir "migrations"

echo ""
echo "================================================="
echo "Summary:"
echo "  Found: $FOUND"
echo "  Missing: $MISSING"
echo ""

if [ $MISSING -eq 0 ]; then
    echo "✓ All required files present!"
    echo ""
    echo "Next steps:"
    echo "1. Add your OPENAI_API_KEY to .env"
    echo "2. Run: ./setup.sh"
    echo "3. Test: ./test_api.sh"
    exit 0
else
    echo "✗ Some files are missing. Please check the list above."
    exit 1
fi

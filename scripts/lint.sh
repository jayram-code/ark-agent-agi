#!/bin/bash
# Lint and format check script for local development

set -e

echo "=================================================="
echo "Running ARK Agent AGI Code Quality Checks"
echo "=================================================="

echo ""
echo "1️⃣  Checking code formatting with Black..."
black --check src/ tests/ || {
    echo "❌ Black formatting issues found. Run 'black src/ tests/' to fix"
    exit 1
}
echo "✅ Black check passed"

echo ""
echo "2️⃣  Checking import sorting with isort..."
isort --check-only src/ tests/ || {
    echo "❌ Import sorting issues found. Run 'isort src/ tests/' to fix" 
    exit 1
}
echo "✅ isort check passed"

echo ""
echo "3️⃣  Linting with flake8..."
flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics
flake8 src/ tests/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
echo "✅ flake8 check passed"

echo ""
echo "4️⃣  Type checking with mypy..."
mypy src/ --ignore-missing-imports || {
    echo "⚠️  mypy found type issues (non-blocking)"
}

echo ""
echo "=================================================="
echo "✅ All quality checks passed!"
echo "=================================================="

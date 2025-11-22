# ARK Agent AGI - Production Hardening

This directory contains production-ready infrastructure and tooling.

## Features Implemented

### 1. Environment Management
- **`.env.example`**: Template for all environment variables
- **`src/config/environment.py`**: Type-safe configuration with validation
- **Usage**: Copy `.env.example` to `.env` and fill in your values

### 2. CI/CD Pipeline
- **`.github/workflows/ci.yml`**: Automated testing, linting, and type checking
- **`pyproject.toml`**: Configuration for Black, isort, pytest, mypy
- **`scripts/lint.sh`**: Local linting script for pre-commit checks

### 3. Production Utilities
- **`src/utils/circuit_breaker.py`**: Circuit breaker pattern for fault tolerance
- **`src/utils/cloud_logger.py`**: Centralized logging with cloud sink support

### 4. Evaluation Framework
- **`evaluation/enhanced_harness.py`**: Direct prediction capture for accurate metrics
- **`evaluation/baselines.py`**: Rule-based baselines for comparison

### 5. Expanded Testing
- **`tests/test_agent_routing.py`**: Orchestrator routing tests
- **`tests/test_builtin_tools.py`**: 40+ unit tests for all tools

## Quick Start

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Set Up Environment
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Run Tests
```bash
pytest tests/ -v --cov=src
```

### Run Linting
```bash
bash scripts/lint.sh
```

### Format Code
```bash
black src/ tests/
isort src/ tests/
```

## Production Deployment

### Required Environment Variables
- `GOOGLE_API_KEY`: Required for Gemini AI

### Optional Environment Variables
- API keys for built-in tools (see `.env.example`)
- Infrastructure settings (logging, circuit breakers)

### CI/CD
GitHub Actions automatically runs tests and linting on every PR.

### Monitoring
- Structured logs in `logs/` directory
- Cloud logging supported (Stackdriver, CloudWatch, Splunk)
- Metrics in NDJSON format at `logs/metrics.jsonl`

## Architecture Improvements

### Import Consistency
All imports now use absolute `src.` paths for reliable top-level execution.

### Fault Tolerance
Circuit breakers on network calls prevent cascading failures.

### Observability
Centralized logging with JSON formatting for easy cloud integration.

## Next Steps

1. Deploy to cloud platform (GCP, AWS, Azure)
2. Set up cloud logging sink
3. Configure monitoring and alerts
4. Set up CI/CD secrets for API keys
5. Run baseline comparisons on production data

This infrastructure makes ARK Agent AGI ready for enterprise production deployment.

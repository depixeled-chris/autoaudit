# Auto Dealership Compliance Checker

Multi-tier compliance checking system for automotive dealership websites using AI-powered text analysis, visual verification, and intelligent template caching.

## Quick Start

### Start API Server
```bash
cd server
python -m uvicorn api.main:app --reload
```

Visit **http://localhost:8000/docs** for interactive API documentation.

## Project Structure

```
autoaudit/
├── server/
│   ├── core/                   # Compliance checking logic
│   │   ├── database.py         # SQLite ORM
│   │   ├── scraper.py          # Playwright scraping
│   │   ├── analyzer.py         # GPT-4.1-nano analysis
│   │   ├── visual_analyzer.py  # GPT-4V verification
│   │   └── main_hybrid.py      # CLI tool
│   │
│   └── api/                    # FastAPI REST API
│       ├── main.py
│       ├── models/             # Pydantic models
│       └── routes/             # API endpoints
│
├── client/                     # Frontend (TBD)
├── compliance.db               # SQLite database
├── openapi.yaml                # OpenAPI 3.0 spec
└── API_DOCUMENTATION.md        # Full API docs
```

## Features

- **27 REST API Endpoints** with OpenAPI 3.0 spec
- **Multi-tier analysis:** Text (GPT-4.1-nano) + Visual (GPT-4V)
- **Template caching:** 98% cost reduction
- **Multi-project support:** Manage multiple dealerships
- **Historical tracking:** Complete audit trail
- **4 States supported:** CA, TX, NY, OK

## API Examples

### Create Project
```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Dealership", "state_code": "OK"}'
```

### Run Compliance Check
```bash
curl -X POST "http://localhost:8000/api/checks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/vehicle.htm",
    "state_code": "OK"
  }'
```

### Get Project Summary
```bash
curl "http://localhost:8000/api/projects/1/summary"
```

## Documentation

- **API Documentation:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference
- **Database Guide:** [DATABASE_GUIDE.md](DATABASE_GUIDE.md) - Schema and usage
- **OpenAPI Spec:** [openapi.yaml](openapi.yaml) - Machine-readable spec
- **Interactive Docs:** http://localhost:8000/docs - Swagger UI

## Installation

```bash
cd server
pip install -r requirements.txt
playwright install chromium
```

Create `.env` file:
```
OPENAI_API_KEY=your_api_key_here
```

## Cost Analysis

- **Text-only:** $0.0003 per check
- **Text + Visual (first time):** $0.0153 per check
- **Text + Cached:** $0.0003 per check (98% savings)

**At scale:** 1,000 sites = $3.33 first run, $0.30 subsequent runs

## Tech Stack

- **FastAPI** - REST API framework
- **SQLite** - Database
- **Playwright** - Web scraping
- **OpenAI** - GPT-4.1-nano & GPT-4V
- **Pydantic** - Data validation

## Status

✅ **Production Ready** - v1.0.0

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete details.

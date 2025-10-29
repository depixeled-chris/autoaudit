# AutoAudit - Dealership Compliance Monitoring

**AI-powered compliance monitoring system for automotive dealership websites.**

Monitor dealer websites for state advertising regulation compliance using AI analysis of screenshots and page content.

## Quick Start

```bash
# Start all services
docker-compose up

# Access the application
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

**First time setup**: Create admin user
```bash
docker-compose exec server python manage.py user:create admin@example.com --name "Admin User"

# Check migrations (using Alembic)
docker-compose exec server alembic current
```

## What It Does

1. **Upload Legislation**: Add state advertising regulations (PDF → AI parsing)
2. **Generate Rules**: Extract atomic compliance requirements from legislation
3. **Create Projects**: Set up monitoring for dealership websites
4. **Run Checks**: AI analyzes screenshots + content for violations
5. **Track Compliance**: Historical checks, violation tracking, reporting

## Technology Stack

- **Backend**: Python FastAPI + SQLite
- **Frontend**: React 18 + TypeScript + Vite
- **State Management**: RTK Query (Redux Toolkit)
- **LLM**: OpenAI GPT-4o-mini
- **Deployment**: Docker Compose

## Project Structure

```
autoaudit/
├── server/              # FastAPI backend
│   ├── api/             # API routes (main.py, states.py, rules.py, llm.py, etc.)
│   ├── core/            # Database, LLM client, llm_operations
│   ├── services/        # Business logic
│   ├── alembic/         # Database migrations (Alembic)
│   ├── data/            # SQLite database
│   └── generate_openapi.py  # OpenAPI spec generator
├── client/              # React frontend
│   ├── src/
│   │   ├── pages/       # Route components (ConfigPage with 6 tabs)
│   │   ├── features/    # Feature modules
│   │   └── store/api/   # RTK Query
├── docs/                # Documentation
├── openapi.json         # OpenAPI 3.1 spec (auto-generated)
├── openapi.yaml         # OpenAPI 3.1 spec (auto-generated)
└── CLAUDE.md            # Documentation index (START HERE)
```

## Documentation

**📚 [CLAUDE.md](CLAUDE.md) - Start here for comprehensive documentation**

This is the master index linking to:
- Database schema
- API endpoints
- Frontend architecture
- Migration system
- Development guide
- User workflows

## Key Features

- **Legislation Management**: Upload PDFs, AI-powered parsing into atomic rules
- **Project Monitoring**: Track multiple dealership sites
- **Compliance Checks**: Screenshot + text analysis with violation detection
- **Preamble System**: Versioned prompt templates (universal → state → page type → project)
- **Rule Versioning**: Track legislation changes, rule evolution, collision detection
- **LLM Usage Tracking**: Comprehensive cost monitoring, per-operation model configuration
- **18 Page Types**: VDP, Homepage, Financing, Lease, Service, etc.

## Architecture

### Data Hierarchy
```
States (OK, TX, etc.)
  └── Legislation Sources (statutory PDFs)
       └── Legislation Digests (AI interpretations, versioned)
            └── Rules (atomic compliance requirements)
                 └── Projects (dealership sites)
                      └── URLs (specific pages)
                           └── Compliance Checks (violations detected)
```

### Data Flow
```
States → Legislation Sources → Legislation Digests → Rules
                                                       ↓
                                          Projects → URLs → Compliance Checks
```

### AI Pipeline
1. Upload PDF legislation
2. AI extracts plain-language requirements (digests)
3. AI generates atomic compliance rules
4. Rules applied to projects by state
5. Screenshot + text analysis detects violations
6. Results stored with full audit trail

## Development

### Common Commands

```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f server

# Check migrations (Alembic)
docker-compose exec server alembic current

# Run pending migrations
docker-compose exec server alembic upgrade head

# Regenerate OpenAPI spec (after API changes)
docker-compose exec server python generate_openapi.py

# Shell access
docker-compose exec server sh
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete reference:
- All Docker operations
- Database operations
- Debugging guide
- Hot reload setup
- Troubleshooting

## API Documentation

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **OpenAPI Spec**: `openapi.json` / `openapi.yaml` (regenerate after API changes)
- **Complete Reference**: [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)
- **86 Endpoints**: Projects, URLs, Checks, States, Legislation, Rules, Preambles, LLM Management

## Database

- **SQLite**: `server/data/compliance.db`
- **28 Tables**: Users, Projects, URLs, Checks, States, Legislation, Rules, Preambles, LLM Logs, Model Config
- **Schema Docs**: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **Migrations**: Alembic (`docker-compose exec server alembic upgrade head`)

## Environment Variables

Create `.env` file in root:
```bash
JWT_SECRET_KEY=your-secret-key-change-this
OPENAI_API_KEY=sk-your-openai-key
```

## License

Proprietary - All rights reserved

## Status

**In Development** - Core features complete, LLM tracking implemented, collision detection in progress.

Recent updates:
- ✅ Migration system unified (Alembic only)
- ✅ LLM usage tracking and cost monitoring
- ✅ Per-operation model configuration
- ✅ OpenAPI 3.1 specification
- ✅ Complete database schema (28 tables)

See [CLAUDE.md](CLAUDE.md) for current priorities and detailed documentation.

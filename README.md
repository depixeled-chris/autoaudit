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
├── server/           # FastAPI backend
│   ├── api/          # API routes
│   ├── core/         # Database, migrations, LLM client
│   ├── services/     # Business logic
│   └── data/         # SQLite database
├── client/           # React frontend
│   ├── src/
│   │   ├── pages/    # Route components
│   │   ├── features/ # Feature modules
│   │   └── store/    # RTK Query
├── docs/             # Documentation
└── CLAUDE.md         # Documentation index (START HERE)
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
- **Cost Tracking**: Per-call LLM usage and cost monitoring
- **18 Page Types**: VDP, Homepage, Financing, Lease, Service, etc.

## Architecture

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

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for:
- Common commands
- Debugging guide
- Database operations
- Hot reload setup
- Troubleshooting

## API Documentation

- **Interactive Docs**: http://localhost:8000/docs (Swagger UI)
- **Complete Reference**: [docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)
- **~80 Endpoints**: Projects, URLs, Checks, States, Legislation, Rules, Preambles

## Database

- **SQLite**: `server/data/compliance.db`
- **27 Tables**: Users, Projects, URLs, Checks, States, Legislation, Rules, Preambles
- **Schema Docs**: [docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)
- **Migrations**: Auto-run on startup via `core/migrations.py`

## Environment Variables

Create `.env` file in root:
```bash
JWT_SECRET_KEY=your-secret-key-change-this
OPENAI_API_KEY=sk-your-openai-key
```

## License

Proprietary - All rights reserved

## Status

**In Development** - Core features complete, collision detection and advanced features in progress.

See [CLAUDE.md](CLAUDE.md) for current priorities and known issues.

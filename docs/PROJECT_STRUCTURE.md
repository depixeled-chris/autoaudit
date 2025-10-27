# Project Structure

Full directory layout and what goes where.

## Repository Root

```
autoaudit/
├── server/                     # Python FastAPI backend
├── client/                     # React TypeScript frontend
├── docs/                       # All documentation (you are here)
├── docker-compose.yml          # Docker orchestration
├── CLAUDE.md                   # Master documentation index
└── proposed_schema_changes.md  # Design notes for versioning system
```

## Backend (`/server`)

```
server/
├── api/                        # FastAPI route handlers
│   ├── main.py                 # App entry point, CORS config, router registration
│   ├── dependencies.py         # Shared dependencies (auth, DB)
│   ├── states.py               # States & legislation endpoints
│   ├── rules.py                # Rules CRUD endpoints
│   ├── preambles.py            # Preamble management endpoints
│   ├── demo.py                 # Demo/admin utilities (protected by PRODUCTION_MODE)
│   └── routes/                 # Additional route modules
│       ├── auth.py             # Login, register, refresh, logout
│       ├── projects.py         # Project CRUD + intelligent setup
│       ├── urls.py             # URL management
│       ├── checks.py           # Compliance check operations
│       ├── page_types.py       # Page type CRUD
│       ├── templates.py        # Legacy template system
│       └── reports.py          # Report generation
├── core/                       # Core infrastructure
│   ├── database.py             # ComplianceDatabase class, schema creation
│   ├── migrations.py           # ⭐ ACTIVE migration system (auto-runs on init)
│   ├── llm_client.py           # OpenAI wrapper with auto-logging
│   ├── config.py               # Settings (DATABASE_PATH, PRODUCTION_MODE, etc.)
│   └── dump_schema.py          # Utility: dump DB schema to JSON
├── services/                   # Business logic layer
│   ├── state_service.py        # State/legislation operations
│   ├── rule_service.py         # Rule generation, collision detection
│   ├── preamble_service.py     # Preamble composition
│   ├── preamble_management_service.py  # Preamble versioning
│   └── document_parser_service.py      # PDF text extraction
├── schemas/                    # Pydantic request/response models
│   ├── state.py                # State, LegislationSource, LegislationDigest
│   ├── rule.py                 # Rule models
│   └── preamble.py             # Preamble models
├── migrations/                 # ⚠️ ORPHANED - do NOT use
│   └── *.py                    # Separate migration files (not mounted in Docker)
├── data/
│   └── compliance.db           # SQLite database (mounted at /app/data/compliance.db)
├── screenshots/                # Stored screenshots
├── manage.py                   # CLI for DB operations
├── Dockerfile.dev              # Dev container config
└── requirements.txt            # Python dependencies
```

## Frontend (`/client`)

```
client/
├── src/
│   ├── main.tsx                # App entry point
│   ├── App.tsx                 # Root component, routing, providers
│   ├── components/
│   │   ├── layout/
│   │   │   └── Layout.tsx      # Main layout wrapper (header, nav, content)
│   │   └── ui/                 # Reusable UI components
│   │       ├── Badge/
│   │       ├── Button/
│   │       ├── Card/
│   │       ├── ConfirmModal/
│   │       ├── Input/
│   │       ├── Modal/
│   │       ├── ThemeToggle/
│   │       ├── Toast/
│   │       └── Toggle/
│   ├── contexts/               # React context providers
│   │   ├── ModalContext.tsx    # Global modal management
│   │   └── ThemeContext.tsx    # Theme (light/dark) state
│   ├── features/               # Feature-based modules
│   │   ├── auth/
│   │   │   └── components/
│   │   │       ├── AuthModal.tsx   # Login/register modal
│   │   │       └── AuthGate.tsx    # Protected route wrapper
│   │   ├── checks/
│   │   │   └── components/
│   │   │       └── CheckDetailModal.tsx
│   │   ├── config/
│   │   │   └── components/
│   │   │       ├── PageTypeSettingsModal.tsx
│   │   │       └── PageTypesTable.tsx
│   │   ├── projects/
│   │   │   ├── pages/
│   │   │   │   ├── ProjectsPage.tsx        # Project list page
│   │   │   │   └── ProjectDetailPage.tsx   # Single project + URLs
│   │   │   └── components/
│   │   │       └── CreateProjectModal.tsx
│   │   └── urls/
│   │       └── components/
│   │           ├── AddURLModal.tsx
│   │           ├── EditURLModal.tsx
│   │           └── URLList.tsx
│   ├── pages/
│   │   ├── ConfigPage.tsx      # Legacy config page (being migrated)
│   │   └── Config/             # New config page structure
│   │       ├── Config.tsx      # Main config page with tabs
│   │       ├── tabs/
│   │       │   ├── StatesTab.tsx       # Manage states & legislation
│   │       │   ├── RulesTab.tsx        # View/approve rules
│   │       │   ├── PreamblesTab.tsx    # Preamble templates & versions
│   │       │   └── OtherTab.tsx        # Demo utilities
│   │       └── components/
│   │           ├── AddStateModal.tsx
│   │           ├── StateConfigModal.tsx
│   │           ├── AddLegislationModal.tsx
│   │           ├── LegislationDetailsModal.tsx
│   │           ├── RuleDetailModal.tsx
│   │           ├── CreatePreambleModal.tsx
│   │           └── CreateVersionModal.tsx
│   ├── services/
│   │   └── api.ts              # API client configuration (axios/fetch)
│   ├── store/
│   │   └── api/                # RTK Query
│   │       ├── apiSlice.ts     # Base API config, auth interceptor
│   │       └── statesApi.ts    # States/legislation endpoints
│   └── index.css               # Global styles, CSS variables
├── public/                     # Static assets
├── index.html                  # HTML entry point
├── vite.config.ts              # Vite configuration
├── tsconfig.json               # TypeScript config
├── package.json                # Node dependencies
└── Dockerfile.dev              # Dev container config
```

## Documentation (`/docs`)

```
docs/
├── DATABASE_SCHEMA.md          # Complete DB schema, current state
├── MIGRATION_SYSTEM.md         # Two migration systems explained
├── API_ENDPOINTS.md            # All API routes documented
├── FRONTEND_STRUCTURE.md       # React architecture, patterns
├── PROJECT_STRUCTURE.md        # This file
├── WORKFLOWS.md                # Key user workflows
└── DEVELOPMENT.md              # Common commands, debugging
```

## File Organization Rules

### Backend
- **Routes (`api/`)**: HTTP handling only, delegate to services
- **Services (`services/`)**: Business logic, can use DB and LLM client
- **Schemas (`schemas/`)**: Pydantic models for validation
- **Core (`core/`)**: Infrastructure (DB, migrations, LLM, config)

### Frontend
- **Components (`components/ui/`)**: Presentational, reusable across features
- **Features (`features/`)**: Feature modules with pages + components
- **Pages (`pages/`)**: Top-level route components
- **Store (`store/api/`)**: RTK Query endpoints, one file per API domain

### When to Create New Files

**Backend**:
- New route module: When you have 5+ related endpoints
- New service: When business logic gets complex (>200 lines in route handler)
- New schema: When you have reusable Pydantic models

**Frontend**:
- New component: When JSX is reused 2+ times
- New feature module: When adding a new major feature (e.g., `features/reporting/`)
- New page: When adding a new route

## Naming Conventions

- **Python files**: `snake_case.py`
- **TypeScript files**: `PascalCase.tsx` (components), `camelCase.ts` (utilities)
- **CSS Modules**: `Component.module.scss`
- **Directories**: `kebab-case/` or `PascalCase/` (components)

## Import Patterns

### Backend
```python
# Relative imports within same module
from .schemas import StateResponse

# Absolute imports from core
from core.database import ComplianceDatabase
from core.llm_client import LLMClient

# Third-party
from fastapi import APIRouter, Depends
```

### Frontend
```typescript
// Absolute imports (via tsconfig paths)
import { Button } from '@/components/ui/Button/Button';
import { useModal } from '@/contexts/ModalContext';

// Relative for local files
import styles from './Component.module.scss';
import { HelperType } from './types';
```

## Asset Locations

- **Screenshots**: `server/screenshots/` (served via `/api/reports/screenshots/:filename`)
- **Uploaded PDFs**: Processed and text stored in DB (not kept as files)
- **Static assets**: `client/public/` (images, fonts, etc.)
- **Database backups**: Not in repo (use `server/data/*.db.backup`)

## What NOT to Commit

- `server/data/compliance.db` (database file)
- `server/screenshots/*.png` (screenshots)
- `client/node_modules/`
- `__pycache__/`, `*.pyc`
- `.env` files with secrets
- `venv/`, `.venv/`

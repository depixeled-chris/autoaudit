# AutoAudit Project Documentation

**Last Updated**: 2025-10-27
**Purpose**: Automotive dealership compliance monitoring system

## 🎯 Quick Navigation

### For Users & Developers
**[README.md](README.md)** - Project overview, quick start, features, and setup instructions

### For AI Agents (Context Management)
**This file (CLAUDE.md)** - Documentation navigation hub with links to detailed technical docs

---

## 📚 Documentation Tree

**Treat these docs as external memory - navigate to specific docs as needed instead of loading everything into context.**

### Core Technical Docs
1. **[DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - All 27 tables, current state, missing components
2. **[MIGRATION_SYSTEM.md](docs/MIGRATION_SYSTEM.md)** - ⚠️ TWO migration systems exist (critical to understand)
3. **[API_ENDPOINTS.md](docs/API_ENDPOINTS.md)** - All ~80 REST endpoints with examples
4. **[FRONTEND_STRUCTURE.md](docs/FRONTEND_STRUCTURE.md)** - React app, RTK Query, component patterns
5. **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Directory layout, file organization rules
6. **[WORKFLOWS.md](docs/WORKFLOWS.md)** - 10 end-to-end user workflows
7. **[DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Commands, debugging, troubleshooting
8. **[DESIGN_NOTES.md](docs/DESIGN_NOTES.md)** - Design decisions for versioning system

### Reference
- **Tech Stack**: FastAPI + React + TypeScript + SQLite + OpenAI GPT-4o-mini
- **Deployment**: Docker Compose (ports: server=8000, client=5173)
- **Database**: `server/data/compliance.db` → `/app/data/compliance.db` in Docker

---

## 🏗️ Major Documentation Principles

1. **Keep docs updated** - When you change code, update the relevant doc
2. **No duplication** - Each piece of info lives in ONE place
3. **Tree structure** - CLAUDE.md is the trunk, docs/* are branches
4. **External memory** - Don't load everything into context, navigate as needed
5. **Link, don't repeat** - Reference other docs instead of copying content

---

## 🚨 Critical Issues (As of 2025-10-27)

### 1. TWO Migration Systems
See [MIGRATION_SYSTEM.md](docs/MIGRATION_SYSTEM.md) for full details.

- **Active**: `core/migrations.py` (inline functions, auto-runs)
- **Orphaned**: `server/migrations/*.py` (separate files, NOT mounted in Docker)
- **Mystery**: Migration 13 was applied from orphaned system somehow

### 2. Database Incomplete
See [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) for full details.

- ❌ `rules` table missing 5 lineage columns
- ❌ `rule_collisions` table doesn't exist
- ❌ `llm_logs` table doesn't exist
- ✅ `legislation_digests` HAS version & active columns

### 3. Docker Volume Mounts (Server)
```
✅ ./server/api:/app/api
✅ ./server/core:/app/core
✅ ./server/services:/app/services
✅ ./server/schemas:/app/schemas
✅ ./server/data:/app/data
❌ ./server/migrations:/app/migrations  # NOT MOUNTED - files are orphaned
```

---

## 🗺️ Data Hierarchy

```
States (OK, TX, etc.)
  └── Legislation Sources (statutory PDFs)
       └── Legislation Digests (AI interpretations, versioned)
            └── Rules (atomic compliance requirements)
                 └── Projects (dealership sites)
                      └── URLs (specific pages)
                           └── Compliance Checks (violations detected)
```

---

## 🎯 Getting Started

### First Time Reading
1. Read [README.md](README.md) - Project overview and quick start
2. Read this file (CLAUDE.md) - Understand documentation structure
3. Read [DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md) - Understand data model
4. Read [MIGRATION_SYSTEM.md](docs/MIGRATION_SYSTEM.md) - Understand migration mess
5. Pick specific docs based on your task

### Working on Features
- **Database change?** → [MIGRATION_SYSTEM.md](docs/MIGRATION_SYSTEM.md)
- **API endpoint?** → [API_ENDPOINTS.md](docs/API_ENDPOINTS.md)
- **Frontend component?** → [FRONTEND_STRUCTURE.md](docs/FRONTEND_STRUCTURE.md)
- **User workflow?** → [WORKFLOWS.md](docs/WORKFLOWS.md)
- **Need commands?** → [DEVELOPMENT.md](docs/DEVELOPMENT.md)

### When Context Resets
1. Start with this file (CLAUDE.md)
2. Check "Critical Issues" section for current state
3. Navigate to specific docs as needed
4. **Don't try to hold everything in memory**

---

## 📂 Quick Reference

### Project Structure (Brief)
```
autoaudit/
├── server/              # FastAPI backend
│   ├── api/             # Routes (main.py, states.py, rules.py, etc.)
│   ├── core/            # Database, migrations, LLM client
│   ├── services/        # Business logic
│   └── data/            # SQLite database
├── client/
│   ├── src/
│   │   ├── pages/Config/  # Config page with tabs
│   │   ├── features/      # Feature modules
│   │   └── store/api/     # RTK Query
├── docs/                # 📚 All documentation (you are here)
├── README.md            # User-facing overview
└── CLAUDE.md            # This file - Agent navigation hub
```

### Common Commands
```bash
# Start services
docker-compose up

# Check migrations
docker-compose exec server python manage.py migration:status

# View logs
docker-compose logs -f server

# Database operations
docker-compose exec server sh -c "python -c \"...\""
```

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for complete command reference.

---

## 🎯 Task Management (External Memory)

**Task lists are segmented for efficient context usage:**
- **[TODO_NEW.md](docs/TODO_NEW.md)** - New & pending tasks (load to see what needs doing)
- **[TODO_IN_PROGRESS.md](docs/TODO_IN_PROGRESS.md)** - Currently active tasks (load to see current work)
- **[TODO_COMPLETED.md](docs/TODO_COMPLETED.md)** - Finished tasks (load to see what's been done)
- **[TODO_BACKLOG.md](docs/TODO_BACKLOG.md)** - Future ideas & deprioritized items (load when planning)

**Maintain these like documentation**:
- Check TODO_NEW.md when looking for work
- Move task to TODO_IN_PROGRESS.md when starting
- Move task to TODO_COMPLETED.md when done
- Move unprioritized items to TODO_BACKLOG.md
- Update "Last Updated" dates
- Keep context minimal by only loading the relevant TODO file

---

## 📝 When Updating Documentation

1. **Update the relevant doc** - Don't duplicate info in multiple places
2. **Update this file** - If you add a new doc, link it here
3. **Keep README current** - User-facing changes should update README
4. **Date your changes** - Update "Last Updated" at top of files
5. **Link, don't copy** - Reference other docs instead of repeating content

---

**Remember**: This is a navigation hub, not a knowledge dump. Navigate to specific docs as needed. Treat documentation as external memory to minimize context usage.

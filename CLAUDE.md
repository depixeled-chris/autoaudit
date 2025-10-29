# AutoAudit Project Documentation

**Last Updated**: 2025-10-28

---

## 🧠 Principles for AI Agents

**CRITICAL**: This documentation system is your external long-term memory. Neglecting it is to forget it. Your context window is small and you have a very limited memory otherwise. You're basically afflicted similar to Lenny from Memento. If you don't write it down, it's forgotten in short order.

### Core Principles
1. **Documentation IS long-term memory** - Context resets, documentation doesn't. Navigate to docs as needed.
2. **README.md is the root** - Always start there for overview, then navigate to specific docs. Keep it concise so that you don't have to store a large volume of information in your context window. Critical info in README.md. Deeper dives in the drilldown documents.
3. **Don't load everything into context** - Treat docs as external memory, read what you need when you need it.
4. **Update docs BEFORE every commit** - Outdated docs are worse than no docs.
5. **No duplication** - Each piece of info lives in ONE place, link to it instead of copying.
6. **TODO docs are your work log** - CLAUDE.md is guiding set of critical principles, not a task tracker. PLEASE ASK if you should remember something in CLAUDE.md before doing so.
7. **BE CAREFUL when updating documents** - Don't completely rewrite the documents. Archive and ammend as needed. Development is an iterative process, not inventing a completely new version of reality when it suits you. We build on the past, not overwrite it.Let's do

### Dev Environment Principles
1. **Don't run Python outside of a Docker container without approval.** I prefer that you run all operations within Docker where you should have all the dependencies you need.

### When Context Resets
1. Read this file (CLAUDE.md) first - get oriented
2. Read README.md - understand project overview
3. Navigate to specific docs based on your task
4. Check TODO files to see current/pending/completed work

### Documentation Structure
```
README.md (Root - user-facing overview, tech stack, quick start)
  ├── CLAUDE.md (This file - AI agent principles & navigation)
  └── docs/* (Detailed technical documentation)
        ├── Technical: DATABASE_SCHEMA, API_ENDPOINTS, FRONTEND_STRUCTURE, etc.
        └── Work Logs: TODO_NEW, TODO_IN_PROGRESS, TODO_COMPLETED, TODO_BACKLOG
```

---

## 📚 Documentation Index

**Start with [README.md](README.md)** - User-facing overview, tech stack, architecture, quick start

### Technical Documentation
- **[docs/DATABASE_SCHEMA.md](docs/DATABASE_SCHEMA.md)** - 31 tables, Alembic migrations
- **[docs/API_ENDPOINTS.md](docs/API_ENDPOINTS.md)** - 86 REST endpoints with examples
- **[docs/FRONTEND_STRUCTURE.md](docs/FRONTEND_STRUCTURE.md)** - React components, RTK Query, 6 config tabs
- **[docs/MIGRATION_SYSTEM.md](docs/MIGRATION_SYSTEM.md)** - Alembic workflow, creating migrations
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Docker commands, debugging, troubleshooting
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Directory layout, file organization
- **[docs/WORKFLOWS.md](docs/WORKFLOWS.md)** - 10 end-to-end user workflows
- **[docs/DESIGN_NOTES.md](docs/DESIGN_NOTES.md)** - Architecture decisions, versioning system

### Work Logs (TODO System)
- **[docs/TODO_NEW.md](docs/TODO_NEW.md)** - Pending tasks
- **[docs/TODO_IN_PROGRESS.md](docs/TODO_IN_PROGRESS.md)** - Active work
- **[docs/TODO_COMPLETED.md](docs/TODO_COMPLETED.md)** - Completed work with detailed logs
- **[docs/TODO_BACKLOG.md](docs/TODO_BACKLOG.md)** - Future/deprioritized items

---

## 🚨 TODO Maintenance (CRITICAL)

**The TODO docs are your work log. CLAUDE.md is NOT your work log.**

### Workflow
1. **Starting**: Move task from TODO_NEW.md → TODO_IN_PROGRESS.md. Create the task in TODO_IN_PROGRESS.md if it doesn't exist.
2. **While working**: Update TODO_IN_PROGRESS.md with current status
3. **Completing**: Move to TODO_COMPLETED.md with detailed entry:
   - Problem identified
   - Actions taken (step-by-step)
   - Files created/modified/deleted
   - Verification steps performed
   - Results achieved

### What Goes Where
- **TODO_COMPLETED.md**: Detailed action logs, file changes, verification results
- **TODO_BLOCKERS.md**: Critical blocking issues preventing progress (create if needed)

---

## 📝 Pre-Commit Checklist

**Before EVERY commit, update documentation:**

1. **Code changed?** → Update relevant docs:
   - README.md (if tech stack/features/architecture affected)
   - docs/DATABASE_SCHEMA.md (table/column changes)
   - docs/API_ENDPOINTS.md (endpoint changes)
   - docs/FRONTEND_STRUCTURE.md (component/state changes)
   - docs/MIGRATION_SYSTEM.md (new migrations)
   - docs/DEVELOPMENT.md (new commands)

2. **API changed?** → Regenerate OpenAPI:
   ```bash
   docker-compose exec server python generate_openapi.py
   ```

3. **Work completed?** → Update TODO_COMPLETED.md with detailed log

4. **Update "Last Updated" dates** in modified docs

**Golden Rule**: Documentation updates are NOT optional. Outdated docs are worse than no docs.

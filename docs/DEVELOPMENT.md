# Development Guide

Common commands, debugging, and troubleshooting.

## Quick Commands

### Docker Operations
```bash
# Start all services
docker-compose up

# Start in background
docker-compose up -d

# Restart single service
docker-compose restart server
docker-compose restart client

# Rebuild after dependency changes
docker-compose up --build

# Stop all services
docker-compose down

# View logs
docker-compose logs -f server
docker-compose logs -f client

# Shell access
docker-compose exec server sh
docker-compose exec client sh
```

### Database Operations
```bash
# Check migration status (Alembic)
docker-compose exec server alembic current

# Show migration history
docker-compose exec server alembic history

# Run pending migrations
docker-compose exec server alembic upgrade head

# Database info (counts)
docker-compose exec server python manage.py db:info

# Create admin user
docker-compose exec server python manage.py user:create admin@example.com --name "Admin"

# List all tables
docker-compose exec server sh -c "python -c \"import sqlite3; conn = sqlite3.connect('/app/data/compliance.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\" ORDER BY name'); print('\\n'.join([r[0] for r in cursor.fetchall()]))\""
```

### OpenAPI Specification
```bash
# ⚠️ IMPORTANT: Regenerate after ANY API endpoint changes
docker-compose exec server python generate_openapi.py

# This generates:
# - openapi.json (at project root)
# - openapi.yaml (at project root)
#
# The script outputs a summary showing:
# - Total endpoints count
# - Total models/schemas count
# - List of all endpoints by method and path

# Dump table schema
docker-compose exec server sh -c "python -c \"import sqlite3; conn = sqlite3.connect('/app/data/compliance.db'); cursor = conn.cursor(); cursor.execute('PRAGMA table_info(rules)'); [print(row) for row in cursor.fetchall()]\""

# Count rows in table
docker-compose exec server sh -c "python -c \"import sqlite3; conn = sqlite3.connect('/app/data/compliance.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM rules'); print(f'Rules: {cursor.fetchone()[0]}')\""
```

### Frontend Development
```bash
# Install dependencies (from client/)
npm install

# Start dev server (if not using Docker)
npm run dev

# Type check
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
```

### Backend Development
```bash
# Install dependencies (from server/)
pip install -r requirements.txt

# Run server directly (outside Docker)
cd server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Python shell with DB access
docker-compose exec server python -c "from core.database import ComplianceDatabase; db = ComplianceDatabase('/app/data/compliance.db'); import code; code.interact(local=locals())"
```

## Access URLs

- **Frontend**: http://localhost:5173 (Vite dev server)
- **Backend API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **NGINX Proxy**: http://localhost (production-like routing)

## Debugging

### Backend Issues

**Check server logs:**
```bash
docker-compose logs -f server
```

**Common issues:**
- **Import errors**: Check Python path, ensure module is in mounted volume
- **Migration errors**: See MIGRATION_SYSTEM.md
- **Database locked**: SQLite WAL mode should prevent this, but restart server if it happens
- **CORS errors**: Check `main.py` CORS middleware allows frontend origin

**Debug with Python:**
```python
# Add to code
import pdb; pdb.set_trace()

# Or use logging
import logging
logger = logging.getLogger(__name__)
logger.info(f"Debug: {variable}")
```

### Frontend Issues

**Check client logs:**
```bash
docker-compose logs -f client
```

**Common issues:**
- **API calls failing**: Check network tab, verify backend is running
- **State not updating**: Check RTK Query cache, may need to invalidate tags
- **Modal not closing**: Ensure `onClose` is called in submit handler
- **TypeScript errors**: Run `npm run type-check` to see all errors

**Debug with Browser:**
- Open DevTools → Network tab for API calls
- Redux DevTools for RTK Query state
- React DevTools for component tree

### Database Issues

**Inspect database directly:**
```bash
# Copy DB to host
docker cp autoaudit-server:/app/data/compliance.db ./compliance.db.backup

# Open with SQLite browser
sqlite3 compliance.db.backup
.tables
.schema rules
SELECT * FROM rules LIMIT 5;
```

**Fix corrupted database:**
```bash
# Stop services
docker-compose down

# Backup DB
cp server/data/compliance.db server/data/compliance.db.backup

# Delete and recreate
rm server/data/compliance.db
docker-compose up
# Migrations will recreate schema
```

## Testing

### Manual API Testing

**Using curl:**
```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Get states (with auth)
curl http://localhost:8000/api/states \
  -H "Authorization: Bearer <token>"
```

**Using Swagger UI:**
1. Go to http://localhost:8000/docs
2. Click "Authorize" button
3. Login to get token
4. Use interactive API docs

### Frontend Testing

Currently no automated tests. Manual testing workflow:
1. Create project
2. Add URLs
3. Run check
4. View violations
5. Test modal flows

## Hot Reload

### Backend
- Changes to `api/`, `core/`, `services/`, `schemas/` reload automatically
- Changes to `requirements.txt` require rebuild: `docker-compose up --build server`

### Frontend
- Changes to `src/` reload automatically (Vite HMR)
- Changes to `package.json` require rebuild: `docker-compose up --build client`

## Environment Variables

### Backend (.env or docker-compose.yml)
```bash
JWT_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
DATABASE_PATH=/app/data/compliance.db
PRODUCTION_MODE=false
PYTHONUNBUFFERED=1
```

### Frontend (.env or docker-compose.yml)
```bash
VITE_API_URL=http://localhost:8000
```

## Performance Tips

### Backend
- SQLite WAL mode enabled by default (better concurrency)
- Connection pooling: Each request gets its own DB instance
- LLM caching: Repeated calls with same input may be cached by OpenAI

### Frontend
- RTK Query caches API responses
- React.memo used sparingly on expensive components
- Code splitting: Not yet implemented (future optimization)

## Common Tasks

### Add a new migration
1. Add function to `server/core/migrations.py`
2. Register in `MIGRATIONS` list
3. Restart server: `docker-compose restart server`
4. Verify: `docker-compose exec server python manage.py migration:status`

See MIGRATION_SYSTEM.md for details.

### Add a new API endpoint
1. Add route in `server/api/{module}.py`
2. Add schema in `server/schemas/{module}.py`
3. Add service logic in `server/services/{module}_service.py`
4. Update `docs/API_ENDPOINTS.md`

### Add a new frontend component
1. Create in `client/src/components/ui/ComponentName/`
2. Create `ComponentName.tsx` and `ComponentName.module.scss`
3. Export from `client/src/components/ui/index.ts` (if creating barrel exports)

### Add RTK Query endpoint
1. Add to `client/src/store/api/{domain}Api.ts`
2. Define query/mutation with proper tags for cache invalidation
3. Use in component: `const { data } = useGetThingsQuery()`

## Troubleshooting Checklist

### Backend not starting
- [ ] Check logs: `docker-compose logs server`
- [ ] Verify Python syntax: No import errors
- [ ] Check database file exists: `server/data/compliance.db`
- [ ] Verify migrations ran: `docker-compose exec server python manage.py migration:status`

### Frontend not starting
- [ ] Check logs: `docker-compose logs client`
- [ ] Verify `node_modules` installed
- [ ] Check TypeScript errors: `npm run type-check`
- [ ] Verify backend is running: http://localhost:8000/api/health

### API calls failing
- [ ] Check CORS: Origin allowed in `api/main.py`?
- [ ] Check auth: Token present and valid?
- [ ] Check network tab: What's the actual error?
- [ ] Check backend logs for server-side error

### Database issues
- [ ] Check file permissions on `server/data/compliance.db`
- [ ] Check disk space
- [ ] Try: `docker-compose restart server`
- [ ] Last resort: Backup and recreate DB

## Code Quality

### Backend
- Use type hints: `def foo(bar: str) -> int:`
- Docstrings for public functions
- FastAPI automatic validation via Pydantic
- No manual SQL injection risk (parameterized queries)

### Frontend
- TypeScript strict mode enabled
- Props interfaces defined for all components
- CSS Modules for scoped styles
- ESLint/Prettier config (if added)

## Useful Aliases

Add to your shell config:
```bash
# Docker aliases
alias dc='docker-compose'
alias dcl='docker-compose logs -f'
alias dce='docker-compose exec'

# AutoAudit specific
alias aa-server='docker-compose exec server sh'
alias aa-client='docker-compose exec client sh'
alias aa-db='docker-compose exec server python manage.py'
alias aa-migrate='docker-compose exec server python manage.py migrate'
```

## Getting Help

1. Check this file for common commands
2. Check MIGRATION_SYSTEM.md for migration issues
3. Check API_ENDPOINTS.md for API questions
4. Check server logs: `docker-compose logs -f server`
5. Check database schema: See DATABASE_SCHEMA.md

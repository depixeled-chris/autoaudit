# Deployment Guide

This guide covers deploying AutoAudit to production with proper security configurations.

## Environment Configuration

AutoAudit uses environment variables to configure behavior for different deployment environments (development vs production).

### Environment Variables

#### Server (`server/.env`)

```bash
# Environment Mode
# Options: development | production
# Affects cookie security, CORS origins, and other security settings
ENVIRONMENT=production

# JWT Configuration
# IMPORTANT: Generate a strong random secret for production
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
JWT_SECRET_KEY=your-secure-random-secret-key

# CORS Origins (Production only)
# Comma-separated list of allowed frontend origins
# IMPORTANT: Must be exact match including protocol and port
# Example: https://yourdomain.com,https://app.yourdomain.com
CORS_ORIGINS=https://yourdomain.com

# OpenAI API Key
OPENAI_API_KEY=your-openai-api-key

# Database Path (optional, defaults to compliance.db)
DATABASE_PATH=/app/data/compliance.db
```

### What ENVIRONMENT Does

When `ENVIRONMENT=production`:

**Security Enhancements:**
- ✅ **Cookies**: `secure=true` (HTTPS only), `samesite=strict` (maximum CSRF protection)
- ✅ **CORS**: Uses explicit origins from `CORS_ORIGINS` (must be comma-separated)
- ✅ **Access Tokens**: 15-minute expiration
- ✅ **Refresh Tokens**: 30-day expiration, httpOnly cookies

When `ENVIRONMENT=development`:

**Developer Convenience:**
- ✅ **Cookies**: `secure=false` (works with HTTP), `samesite=lax` (allows page refresh)
- ✅ **CORS**: Automatically allows localhost origins
- ✅ **Logging**: More verbose output

## Production Deployment Checklist

### 1. Environment Setup

```bash
# Copy example env file
cp server/.env.example server/.env

# Edit server/.env
nano server/.env
```

Set these critical values:
- ✅ `ENVIRONMENT=production`
- ✅ `JWT_SECRET_KEY=<generate-random-secret>`
- ✅ `CORS_ORIGINS=https://yourdomain.com`
- ✅ `OPENAI_API_KEY=<your-key>`

### 2. Generate JWT Secret

```bash
# Generate a secure random secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output to `JWT_SECRET_KEY` in your `.env` file.

### 3. Configure CORS Origins

**IMPORTANT**: CORS origins must be exact matches including protocol.

**Correct Examples:**
```bash
CORS_ORIGINS=https://example.com
CORS_ORIGINS=https://example.com,https://app.example.com
```

**Incorrect Examples:**
```bash
CORS_ORIGINS=example.com  # ❌ Missing protocol
CORS_ORIGINS=https://example.com/  # ❌ Trailing slash
CORS_ORIGINS=*.example.com  # ❌ Wildcards not supported with credentials
```

### 4. SSL/TLS Certificate

For production, you MUST use HTTPS. The refresh token cookies require `secure=true` which only works over HTTPS.

**Options:**
- **Let's Encrypt**: Free SSL certificates (recommended)
- **Cloudflare**: Free SSL/CDN
- **AWS Certificate Manager**: If using AWS
- **Commercial Certificate**: From providers like DigiCert

### 5. Deploy with Docker Compose

```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# You should see:
# "Starting in PRODUCTION mode"
# "CORS origins: ['https://yourdomain.com']"
```

## Security Features

### JWT Refresh Token System

**Architecture:**
- **Access Token**: 15 minutes, stored in memory (React state)
- **Refresh Token**: 30 days, stored in httpOnly cookie
- **Token Rotation**: New refresh token on every refresh (detects theft)
- **Database-Backed**: Tokens can be instantly revoked
- **Device Tracking**: Tracks user-agent and IP for audit trail

**Cookie Security:**
```python
# Development
secure=False  # Works with HTTP (localhost)
samesite="lax"  # Allows same-site navigation

# Production
secure=True  # HTTPS required
samesite="strict"  # Maximum CSRF protection
```

### CORS Security

**Development:**
```python
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:5173",
    "http://127.0.0.1",
    "http://127.0.0.1:5173",
]
```

**Production:**
```python
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")
# Example: ["https://example.com", "https://app.example.com"]
```

## Monitoring Production

### Health Check

```bash
# Check API health
curl https://api.yourdomain.com/api/health

# Should return:
{
  "status": "healthy",
  "database": "connected"
}
```

### Check Environment Mode

```bash
# View startup logs
docker-compose -f docker-compose.prod.yml logs server | grep -i "starting"

# Should show:
# "Starting in PRODUCTION mode"
# "CORS origins: ['https://yourdomain.com']"
```

### View Refresh Tokens

```sql
-- Connect to database
sqlite3 server/data/compliance.db

-- View active refresh tokens
SELECT
    id,
    user_id,
    device_info,
    ip_address,
    created_at,
    expires_at,
    revoked_at
FROM refresh_tokens
WHERE revoked_at IS NULL
ORDER BY created_at DESC;
```

## Troubleshooting

### "CORS error: Access-Control-Allow-Origin"

**Cause**: Frontend origin not in `CORS_ORIGINS`

**Fix**:
```bash
# Update .env
CORS_ORIGINS=https://yourfrontend.com

# Restart server
docker-compose -f docker-compose.prod.yml restart server
```

### "Refresh token failed: 401 Unauthorized"

**Cause**: Cookie not being sent (likely `secure=true` without HTTPS)

**Fix**:
1. Ensure you're using HTTPS in production
2. If testing locally, use `ENVIRONMENT=development`

### "Token expired" immediately after login

**Cause**: Clock skew between server and client

**Fix**:
```bash
# Sync system clock
sudo ntpdate -s time.nist.gov
```

## Scaling Considerations

### Database

Current setup uses SQLite. For production at scale, consider:

- **PostgreSQL**: Better concurrency, full ACID compliance
- **Connection Pooling**: Reduce database connections
- **Read Replicas**: Separate read/write traffic

### Refresh Token Cleanup

Set up a cron job to clean expired tokens:

```bash
# Add to crontab (daily at 2 AM)
0 2 * * * docker exec autoaudit-server python -c "from core.database import ComplianceDatabase; db = ComplianceDatabase('/app/data/compliance.db'); db.cleanup_expired_tokens()"
```

### Session Management

Tokens are stored in database. To revoke all sessions for a user:

```python
# Logout user from all devices
db.revoke_all_user_tokens(user_id=123)
```

## Rollback Procedure

If issues arise in production:

```bash
# Stop containers
docker-compose -f docker-compose.prod.yml down

# Restore previous environment
git checkout main  # or previous stable tag

# Rebuild and start
docker-compose -f docker-compose.prod.yml up -d --build
```

## Support

For deployment issues:
- Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- Review this guide's troubleshooting section
- Check [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for endpoint details

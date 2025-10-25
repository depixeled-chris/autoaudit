# Docker Deployment Guide

This guide covers how to run AutoAudit using Docker and Docker Compose.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (included with Docker Desktop)

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and update with your values:

```bash
cp .env.example .env
```

Edit `.env` and set:
```env
JWT_SECRET_KEY=<generate-with-command-below>
OPENAI_API_KEY=<your-openai-api-key>
VITE_API_URL=http://localhost:8000
```

Generate a secure JWT secret:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Build and Run

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### 3. Access the Application

- **Frontend**: http://localhost (port 80)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Services

### Server (FastAPI Backend)
- Port: 8000
- Database: SQLite (persisted in `./server/data/`)
- Features: REST API, JWT auth, compliance checking

### Client (React Frontend)
- Port: 80
- Framework: React + Vite + Redux Toolkit
- Features: SPA with modal auth, dark/light theme

## Development Mode

To enable hot-reload during development, uncomment the volume mount in `docker-compose.yml`:

```yaml
# server service
volumes:
  - ./server:/app  # Uncomment this line
```

Then rebuild:
```bash
docker-compose up -d --build
```

## Production Deployment

### Build for Production

```bash
# Set production API URL
export VITE_API_URL=https://api.yourdomain.com

# Build images
docker-compose build

# Tag for registry
docker tag autoaudit-server:latest your-registry/autoaudit-server:latest
docker tag autoaudit-client:latest your-registry/autoaudit-client:latest

# Push to registry
docker push your-registry/autoaudit-server:latest
docker push your-registry/autoaudit-client:latest
```

### Environment Variables for Production

Update `.env` for production:
```env
JWT_SECRET_KEY=<strong-random-secret>
OPENAI_API_KEY=<your-key>
VITE_API_URL=https://api.yourdomain.com
```

### Security Considerations

1. **Change default secrets** - Never use example values in production
2. **Use HTTPS** - Put services behind reverse proxy (nginx/traefik) with SSL
3. **Database backup** - Regularly backup `./server/data/compliance.db`
4. **Update base images** - Keep Docker images updated
5. **Limit exposure** - Don't expose ports unless necessary

## Commands Reference

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs
docker-compose logs -f [service-name]

# Execute command in container
docker-compose exec server bash
docker-compose exec client sh

# Remove all containers and volumes
docker-compose down -v

# Check service health
docker-compose ps
```

## Troubleshooting

### Port Already in Use
```bash
# Change ports in docker-compose.yml
ports:
  - "8080:80"      # client
  - "8001:8000"    # server
```

### Database Issues
```bash
# Remove and recreate database
docker-compose down -v
rm -rf server/data/compliance.db
docker-compose up -d
```

### Build Failures
```bash
# Clean build with no cache
docker-compose build --no-cache

# Remove old images
docker system prune -a
```

### Network Issues
```bash
# Recreate networks
docker-compose down
docker network prune
docker-compose up -d
```

## File Structure

```
autoaudit/
├── docker-compose.yml       # Orchestration config
├── .env                     # Environment variables
├── server/
│   ├── Dockerfile          # Server container config
│   ├── .dockerignore       # Exclude from build
│   ├── requirements.txt    # Python dependencies
│   └── data/              # SQLite database (volume)
└── client/
    ├── Dockerfile          # Client container config
    ├── .dockerignore       # Exclude from build
    ├── nginx.conf          # Nginx config
    └── package.json        # Node dependencies
```

## Health Checks

Both services include health checks:

```bash
# Check service health
docker-compose ps

# Manually test endpoints
curl http://localhost:8000/api/health
curl http://localhost/
```

## Scaling

To run multiple server instances:

```bash
docker-compose up -d --scale server=3
```

Add a load balancer (nginx/traefik) to distribute traffic.

## Monitoring

View real-time logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f server
docker-compose logs -f client
```

Monitor resource usage:
```bash
docker stats
```

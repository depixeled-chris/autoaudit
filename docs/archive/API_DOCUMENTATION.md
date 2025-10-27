# Auto Dealership Compliance API Documentation

## Overview

REST API for checking automotive dealership website compliance with state advertising regulations. Built with FastAPI and includes OpenAPI 3.0 specification.

## Base URL

```
http://localhost:8000
```

## OpenAPI Specification

- **Swagger UI (Interactive):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json
- **OpenAPI YAML:** `openapi.yaml` (generated file)

## API Summary

- **Total Endpoints:** 27
- **Pydantic Models:** 15
- **Authentication:** None (add as needed)
- **Rate Limiting:** None (add as needed)

---

## Quick Start

### 1. Start the API Server

```bash
cd server
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Health Check

```bash
curl http://localhost:8000/api/health
```

**Response:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## API Endpoints

### Projects API

#### Create Project

```http
POST /api/projects
```

**Request Body:**
```json
{
  "name": "AllStar CDJR Muskogee",
  "state_code": "OK",
  "description": "Oklahoma dealership compliance monitoring"
}
```

**Response (201):**
```json
{
  "id": 1,
  "name": "AllStar CDJR Muskogee",
  "state_code": "OK",
  "description": "Oklahoma dealership compliance monitoring",
  "created_at": "2025-10-24T18:30:00",
  "updated_at": "2025-10-24T18:30:00"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AllStar CDJR Muskogee",
    "state_code": "OK",
    "description": "Oklahoma dealership compliance monitoring"
  }'
```

#### List Projects

```http
GET /api/projects
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "AllStar CDJR Muskogee",
    "state_code": "OK",
    "description": "Oklahoma dealership compliance monitoring",
    "created_at": "2025-10-24T18:30:00",
    "updated_at": "2025-10-24T18:30:00"
  }
]
```

#### Get Project

```http
GET /api/projects/{project_id}
```

**Response (200):** Same as create response

#### Get Project Summary

```http
GET /api/projects/{project_id}/summary
```

**Response (200):**
```json
{
  "project_id": 1,
  "project_name": "AllStar CDJR Muskogee",
  "total_urls": 25,
  "total_checks": 150,
  "avg_score": 82.5,
  "compliant_count": 120,
  "total_violations": 45
}
```

---

### URLs API

#### Add URL

```http
POST /api/urls
```

**Request Body:**
```json
{
  "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
  "project_id": 1,
  "url_type": "vdp",
  "template_id": "dealer.com_vdp",
  "platform": "dealer.com",
  "check_frequency_hours": 24
}
```

**Response (201):**
```json
{
  "id": 1,
  "project_id": 1,
  "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
  "url_type": "vdp",
  "template_id": "dealer.com_vdp",
  "platform": "dealer.com",
  "active": true,
  "check_frequency_hours": 24,
  "last_checked": null,
  "created_at": "2025-10-24T18:30:00"
}
```

#### List URLs

```http
GET /api/urls?project_id={project_id}&active_only=true
```

**Query Parameters:**
- `project_id` (optional): Filter by project
- `active_only` (default: true): Only return active URLs

**Response (200):** Array of URL objects

#### Update URL

```http
PATCH /api/urls/{url_id}
```

**Request Body:**
```json
{
  "active": false,
  "check_frequency_hours": 48
}
```

**Response (200):** Updated URL object

#### Delete URL (Deactivate)

```http
DELETE /api/urls/{url_id}
```

**Response (204):** No content (marks as inactive)

---

### Compliance Checks API

#### Run Compliance Check

```http
POST /api/checks
```

**⚠️ Note:** This endpoint may take 30-60 seconds depending on visual verification needs.

**Request Body:**
```json
{
  "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
  "state_code": "OK",
  "skip_visual": false,
  "save_formats": ["markdown", "json"]
}
```

**Response (201):**
```json
{
  "id": 1,
  "url_id": 1,
  "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
  "state_code": "OK",
  "template_id": "dealer.com_vdp",
  "overall_score": 70,
  "compliance_status": "NEEDS_REVIEW",
  "summary": "Found 4 violations, 1 visually verified as compliant",
  "llm_input_path": "llm_inputs/input_20251024_183000.md",
  "report_path": "reports/report_20251024_183000.md",
  "checked_at": "2025-10-24T18:30:00",
  "violations": [...],
  "visual_verifications": [...]
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/api/checks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
    "state_code": "OK",
    "skip_visual": false,
    "save_formats": ["markdown"]
  }'
```

#### List Checks

```http
GET /api/checks?url_id={url_id}&state_code={state_code}&limit=100
```

**Query Parameters:**
- `url_id` (optional): Filter by URL
- `state_code` (optional): Filter by state
- `limit` (default: 100, max: 1000): Result limit

**Response (200):** Array of check objects

#### Get Check Details

```http
GET /api/checks/{check_id}?include_details=true
```

**Query Parameters:**
- `include_details` (default: true): Include violations and visual verifications

**Response (200):** Full check object with violations and visual verifications

#### Get Check Violations

```http
GET /api/checks/{check_id}/violations
```

**Response (200):**
```json
[
  {
    "id": 1,
    "check_id": 1,
    "category": "pricing",
    "severity": "high",
    "rule_violated": "Price must include all fees",
    "rule_key": "full_price_disclosure",
    "confidence": 0.85,
    "needs_visual_verification": true,
    "explanation": "Price shown without fee disclosure",
    "evidence": "Price: $35,411 (no disclaimer visible)",
    "created_at": "2025-10-24T18:30:00"
  }
]
```

#### Get Visual Verifications

```http
GET /api/checks/{check_id}/visual-verifications
```

**Response (200):**
```json
[
  {
    "id": 1,
    "check_id": 1,
    "rule_key": "vehicle_id_adjacent",
    "rule_text": "Vehicle ID must be adjacent to price",
    "is_compliant": true,
    "confidence": 0.95,
    "verification_method": "visual",
    "visual_evidence": "Vehicle heading displayed directly above price",
    "proximity_description": "20px separation, same visual module",
    "screenshot_path": "screenshots/visual_123.png",
    "cached": false,
    "created_at": "2025-10-24T18:30:00"
  }
]
```

#### Get Latest Check for URL

```http
GET /api/checks/url/{url}
```

**Example:**
```bash
curl "http://localhost:8000/api/checks/url/https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm"
```

**Response (200):** Most recent check object for that URL

---

### Templates API

#### List Templates

```http
GET /api/templates
```

**Response (200):**
```json
[
  {
    "id": 1,
    "template_id": "dealer.com_vdp",
    "platform": "dealer.com",
    "template_type": "compliance",
    "config": {},
    "created_at": "2025-10-24T18:00:00",
    "updated_at": "2025-10-24T18:30:00",
    "rules": [...]
  }
]
```

#### Get Template

```http
GET /api/templates/{template_id}
```

**Response (200):** Template object with all cached rules

#### Get Template Rules

```http
GET /api/templates/{template_id}/rules
```

**Response (200):**
```json
[
  {
    "id": 1,
    "template_id": "dealer.com_vdp",
    "rule_key": "vehicle_id_adjacent",
    "status": "compliant",
    "confidence": 0.95,
    "verification_method": "visual",
    "notes": "Vehicle ID prominently displayed above price",
    "verified_date": "2025-10-24T18:12:27"
  }
]
```

#### Update Template Rule

```http
PUT /api/templates/{template_id}/rules/{rule_key}
```

**Request Body:**
```json
{
  "status": "compliant",
  "confidence": 0.95,
  "verification_method": "visual",
  "notes": "Vehicle ID always displayed in heading above price"
}
```

**Response (200):** Updated rule object

#### Delete Template Rule

```http
DELETE /api/templates/{template_id}/rules/{rule_key}
```

**Response (204):** No content

---

### Reports API

#### Download Markdown Report

```http
GET /api/reports/{check_id}/markdown
```

**Response (200):** Markdown file download

**cURL Example:**
```bash
curl "http://localhost:8000/api/reports/1/markdown" -o report.md
```

#### Download LLM Input

```http
GET /api/reports/{check_id}/llm-input
```

**Response (200):** Markdown file with LLM input

**cURL Example:**
```bash
curl "http://localhost:8000/api/reports/1/llm-input" -o llm_input.md
```

#### Download Screenshot

```http
GET /api/reports/screenshots/{screenshot_filename}
```

**Response (200):** PNG image file

**cURL Example:**
```bash
curl "http://localhost:8000/api/reports/screenshots/visual_123.png" -o screenshot.png
```

---

## Data Models

### ProjectCreate
```typescript
{
  name: string;           // 1-200 chars
  state_code: string;     // 2 chars (e.g., "OK", "TX")
  description?: string;   // 0-1000 chars
}
```

### URLCreate
```typescript
{
  url: string;
  project_id?: number;
  url_type?: string;                // default: "vdp"
  template_id?: string;
  platform?: string;
  check_frequency_hours?: number;   // default: 24, range: 1-168
}
```

### CheckRequest
```typescript
{
  url: string;
  state_code: string;               // 2 chars
  skip_visual?: boolean;            // default: false
  save_formats?: string[];          // default: ["markdown"]
}
```

### TemplateRuleUpdate
```typescript
{
  status: string;                   // "compliant" | "non_compliant"
  confidence: number;               // 0.0 - 1.0
  verification_method: string;      // "text" | "visual" | "human"
  notes?: string;
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Invalid request data",
  "status_code": 400
}
```

### 404 Not Found
```json
{
  "error": "Project not found",
  "status_code": 404
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Error message details",
  "status_code": 500
}
```

---

## Workflow Examples

### Complete Workflow: Create Project → Add URL → Run Check

```bash
# 1. Create project
PROJECT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Dealership",
    "state_code": "OK"
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.id')
echo "Created project ID: $PROJECT_ID"

# 2. Add URL
URL_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/urls" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm\",
    \"project_id\": $PROJECT_ID,
    \"platform\": \"dealer.com\"
  }")

URL_ID=$(echo $URL_RESPONSE | jq -r '.id')
echo "Added URL ID: $URL_ID"

# 3. Run compliance check
CHECK_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/checks" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.allstarcdjrmuskogee.com/used/Chevrolet/2022-Chevrolet-Silverado-1500.htm",
    "state_code": "OK",
    "skip_visual": false
  }')

CHECK_ID=$(echo $CHECK_RESPONSE | jq -r '.id')
SCORE=$(echo $CHECK_RESPONSE | jq -r '.overall_score')
echo "Check ID: $CHECK_ID, Score: $SCORE/100"

# 4. Get project summary
curl -s "http://localhost:8000/api/projects/$PROJECT_ID/summary" | jq
```

### Monitoring Workflow: Check URLs Needing Updates

```bash
# Get all active URLs
URLS=$(curl -s "http://localhost:8000/api/urls?active_only=true")

# For each URL, check if it needs updating
echo "$URLS" | jq -c '.[]' | while read url_obj; do
  URL=$(echo $url_obj | jq -r '.url')
  LAST_CHECKED=$(echo $url_obj | jq -r '.last_checked')

  # Run check if needed
  if [ "$LAST_CHECKED" == "null" ] || [ "$(date -d "$LAST_CHECKED" +%s)" -lt "$(date -d '24 hours ago' +%s)" ]; then
    echo "Checking $URL..."
    curl -X POST "http://localhost:8000/api/checks" \
      -H "Content-Type: application/json" \
      -d "{\"url\": \"$URL\", \"state_code\": \"OK\"}"
  fi
done
```

---

## Performance Notes

- **Text Analysis:** ~10 seconds, ~$0.0003 per check
- **Visual Verification:** ~15 seconds, ~$0.015 per verification
- **Template Caching:** 98% cost reduction on repeat checks
- **Database:** SQLite, suitable for 10,000+ URLs

---

## Development

### Run in Development Mode

```bash
cd server
python -m uvicorn api.main:app --reload --log-level debug
```

### Run Tests

```bash
cd server
pytest tests/ -v
```

### Generate OpenAPI Spec

```bash
python generate_openapi.py
```

---

## Next Steps

1. Add authentication (JWT, API keys)
2. Add rate limiting
3. Add batch check endpoints
4. Add WebSocket for real-time progress
5. Add export endpoints (CSV, PDF)
6. Build frontend client

---

## Support

- **API Documentation:** http://localhost:8000/docs
- **OpenAPI Spec:** `openapi.yaml`
- **Database Schema:** `DATABASE_GUIDE.md`
- **Project README:** `README.md`

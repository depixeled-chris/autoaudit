# API Endpoints Documentation

**Base URL**: `http://localhost:8000/api` (dev) | `http://localhost/api` (nginx)

## Authentication Endpoints (`/api/auth`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/register` | Create new user account | No |
| POST | `/login` | Login and get JWT tokens | No |
| POST | `/refresh` | Refresh access token | Yes (refresh token) |
| POST | `/logout` | Logout and revoke tokens | Yes |
| GET | `/me` | Get current user info | Yes |

## Project Management (`/api/projects`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Create new project | Yes |
| GET | `/` | List all projects (active only) | Yes |
| GET | `/{project_id}` | Get project details | Yes |
| GET | `/{project_id}/summary` | Get project summary stats | Yes |
| DELETE | `/{project_id}` | Soft delete project | Yes |
| POST | `/{project_id}/screenshot` | Upload project screenshot | Yes |
| POST | `/intelligent-setup` | AI-powered project setup | Yes |

## URL Management (`/api/urls`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Add URL to project | Yes |
| GET | `/` | List all URLs | Yes |
| GET | `/{url_id}` | Get URL details | Yes |
| PATCH | `/{url_id}` | Update URL settings | Yes |
| DELETE | `/{url_id}` | Delete URL | Yes |
| POST | `/{url_id}/rescan` | Trigger manual rescan | Yes |

## Compliance Checks (`/api/checks`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Create new compliance check | Yes |
| GET | `/` | List all checks | Yes |
| GET | `/{check_id}` | Get check details | Yes |
| GET | `/{check_id}/violations` | Get violations for check | Yes |
| GET | `/{check_id}/visual-verifications` | Get visual verifications | Yes |
| GET | `/url/{url}` | Get latest check for URL | Yes |

## Page Types (`/api/page-types`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | List all page types | Yes |
| GET | `/{page_type_id}` | Get page type details | Yes |
| POST | `/` | Create page type | Yes |
| PATCH | `/{page_type_id}` | Update page type | Yes |
| DELETE | `/{page_type_id}` | Delete page type | Yes |

## States & Legislation (`/api/states`)

### States
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Create state | Yes |
| GET | `/` | List all states | Yes |
| GET | `/{state_id}` | Get state by ID | Yes |
| GET | `/code/{state_code}` | Get state by code (e.g., 'OK') | Yes |
| PATCH | `/{state_id}` | Update state | Yes |

### Legislation Sources
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/legislation/upload` | Upload PDF and parse legislation | Yes |
| POST | `/legislation` | Create legislation source manually | Yes |
| GET | `/legislation` | List all legislation sources | Yes |
| GET | `/legislation/{source_id}` | Get legislation source | Yes |
| PATCH | `/legislation/{source_id}` | Update legislation source | Yes |
| DELETE | `/legislation/{source_id}` | Delete legislation source + cascades | Yes |

### Legislation Digests
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/legislation/{source_id}/digests` | Create digest (AI parse) | Yes |
| GET | `/legislation/{source_id}/digests` | List digests for source | Yes |
| GET | `/digests/{digest_id}` | Get digest details | Yes |
| PATCH | `/digests/{digest_id}` | Update digest | Yes |

## LLM Management (`/api/llm`)

### LLM Logs
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/logs` | List LLM logs with filtering | Yes |
| GET | `/logs/{log_id}` | Get specific LLM log details | Yes |
| GET | `/stats` | Get aggregate LLM usage statistics | Yes |

**Query Parameters for GET `/logs`**:
- `limit` - Results per page (default: 100, max: 1000)
- `offset` - Skip N results (default: 0)
- `operation_type` - Filter by operation (PARSE_LEGISLATION, GENERATE_RULES, etc.)
- `model` - Filter by model (gpt-4o-mini, gpt-4o, etc.)
- `status` - Filter by status (success, error, timeout)

**Example Response for `/stats`**:
```json
{
  "total_calls": 1234,
  "total_tokens": 567890,
  "total_cost_usd": 12.34,
  "avg_duration_ms": 1500,
  "by_operation": [
    {
      "operation_type": "GENERATE_RULES",
      "calls": 456,
      "tokens": 234567,
      "cost_usd": 5.67
    }
  ],
  "by_model": [...],
  "by_status": [...]
}
```

### Model Configuration
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/models` | List model configurations per operation | Yes |
| PATCH | `/models/{operation_type}` | Update model for operation type | Yes |
| GET | `/models/available` | List available OpenAI models | Yes |
| GET | `/operations` | List all operation types with metadata | Yes |

**Example PATCH `/models/GENERATE_RULES`**:
```json
{
  "model": "gpt-4o"
}
```

## Rules (`/api/rules`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Create new rule | Yes |
| GET | `/` | List all rules (filterable) | Yes |
| GET | `/{rule_id}` | Get rule details | Yes |
| PATCH | `/{rule_id}` | Update rule | Yes |
| DELETE | `/{rule_id}` | Delete rule | Yes |
| DELETE | `/states/{state_code}/rules` | Delete all rules for state | Yes |
| POST | `/legislation/{source_id}/digest` | Generate rules from source | Yes |

**Query Parameters for GET `/`**:
- `state_code` - Filter by state
- `active` - Filter by active status
- `approved` - Filter by approval status

## Preambles (`/api/preambles`)

### Templates
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/templates` | Create preamble template | Yes |
| GET | `/templates` | List all templates | Yes |
| GET | `/templates/{template_id}` | Get template details | Yes |

### Preambles
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/` | Create preamble | Yes |
| GET | `/` | List preambles (filterable) | Yes |
| GET | `/{preamble_id}` | Get preamble details | Yes |

### Preamble Versions
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/{preamble_id}/versions` | Create new version | Yes |
| GET | `/{preamble_id}/versions` | List versions | Yes |
| GET | `/versions/{version_id}` | Get version details | Yes |
| PATCH | `/versions/{version_id}/activate` | Activate version | Yes |

### Testing & Composition
| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/test-runs` | Create test run | Yes |
| GET | `/test-runs` | List test runs | Yes |
| GET | `/test-runs/{test_id}` | Get test run details | Yes |
| GET | `/versions/{version_id}/performance` | Get performance metrics | Yes |
| POST | `/compose` | Compose preamble from layers | Yes |

## Templates (`/api/templates`) [Legacy]

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/` | List all templates | Yes |
| GET | `/{template_id}` | Get template details | Yes |
| GET | `/{template_id}/rules` | List rules for template | Yes |
| GET | `/{template_id}/rules/{rule_key}` | Get specific rule | Yes |
| PUT | `/{template_id}/rules/{rule_key}` | Create/update rule | Yes |
| DELETE | `/{template_id}/rules/{rule_key}` | Delete rule | Yes |

## Reports (`/api/reports`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/{check_id}/markdown` | Get check report as markdown | Yes |
| GET | `/{check_id}/llm-input` | Get LLM input for check | Yes |
| GET | `/screenshots/{filename}` | Get screenshot file | Yes |

## Demo/Admin (`/api/demo`) ⚠️ DANGEROUS

**Production Safety**: All endpoints check `settings.PRODUCTION_MODE`. Returns 403 if in production.

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| DELETE | `/rules` | Delete ALL rules | Yes |
| DELETE | `/preambles` | Delete ALL preambles | Yes |
| DELETE | `/projects` | Delete ALL projects | Yes |
| DELETE | `/users` | Delete ALL users (keeps admin) | Yes |
| DELETE | `/legislation` | Delete ALL legislation data | Yes |
| DELETE | `/everything` | Nuclear reset (keeps admin user) | Yes |

## Key Data Flows

### Upload & Parse Legislation
```
POST /api/states/legislation/upload
  ├─> Upload PDF file
  ├─> Extract text (PyPDF2/pdfplumber)
  ├─> LLM parses into digests
  └─> Returns: { legislation_source_id, digests: [...] }
```

### Generate Rules from Legislation
```
POST /api/rules/legislation/{source_id}/digest
  ├─> Get legislation source
  ├─> Get active digest
  ├─> LLM extracts atomic rules
  ├─> Detect collisions with existing rules
  └─> Returns: { rules: [...], collisions: [...] }
```

### Create Project with Intelligent Setup
```
POST /api/projects/intelligent-setup
  ├─> User provides base URL
  ├─> AI detects page types automatically
  ├─> Creates project
  ├─> Adds discovered URLs
  └─> Returns: { project_id, urls: [...] }
```

## Response Formats

### Success Response
```json
{
  "id": 1,
  "name": "Example",
  "created_at": "2025-10-27T00:00:00",
  ...
}
```

### List Response
```json
{
  "items": [...],
  "total": 10,
  "page": 1,
  "page_size": 50
}
```

### Error Response
```json
{
  "detail": "Error message",
  "type": "validation_error",
  "code": "INVALID_INPUT"
}
```

## Authentication

All protected endpoints require JWT token in header:
```
Authorization: Bearer <access_token>
```

Token refresh flow:
1. Login → Get access + refresh tokens
2. Use access token for requests
3. When access expires → POST /auth/refresh with refresh token
4. Get new access token

## CORS

Configured in `main.py`:
- Origins: `http://localhost:5173`, `http://localhost`
- Credentials: Allowed
- Methods: All
- Headers: All

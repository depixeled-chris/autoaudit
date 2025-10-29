# Database Schema Documentation

**Database**: SQLite at `server/data/compliance.db` (Docker: `/app/data/compliance.db`)

## Migration Status (Updated 2025-10-28)

### Applied Migrations
**Alembic System** (current):
- **20251027_001**: Complete baseline - Consolidates all legacy migrations (1-17)
- **20251027_002**: Update operation types to ALL_CAPS constants

**Legacy Systems** (historical):
- Migration 1-8: Various column additions (inline system, deleted)
- Migration 13-15: Rules system (external files, deprecated)

**See**: [MIGRATION_SYSTEM.md](MIGRATION_SYSTEM.md) for full migration history and how to use Alembic.

## Table Categories

### 1. User Management
- **users** - User authentication and accounts
- **refresh_tokens** - JWT refresh token tracking

### 2. Core Compliance System
- **projects** - Dealership compliance monitoring projects
- **urls** - URLs being monitored for compliance
- **compliance_checks** - Historical compliance check results
- **violations** - Detected compliance violations
- **llm_calls** - LLM API call tracking (LEGACY - use llm_logs instead)
- **llm_logs** - ✅ Comprehensive LLM cost and performance tracking
- **llm_model_config** - ✅ Per-operation model configuration (which model to use for each operation type)

### 3. Page Type System
- **page_types** - Page type definitions (VDP, Homepage, Financing, etc.)
  - 18 predefined page types with preambles and confirmation requirements
  - Created by migration 13

### 4. Legislation & Rules System
- **states** - US states with active regulations
  - Currently: Oklahoma (OK)
- **legislation_sources** - Original statutory text (PDFs/documents)
  - Unmodified source of truth
  - Unique constraint: (state_code, statute_number)
- **legislation_digests** - AI interpretations of legislation
  - ✅ **HAS versioning**: `version` (INTEGER), `active` (BOOLEAN)
  - One active digest per source (enforced via unique index)
  - Types: 'universal' or 'page_specific'
- **rules** - Atomic compliance requirements
  - ✅ **HAS all lineage columns** (added by migration 015):
    - `legislation_digest_id` - Links to digest that created this rule
    - `is_manually_modified` - Tracks manual edits
    - `original_rule_text` - AI-generated text before edits
    - `status` - Rule lifecycle state (active/pending_review/superseded/merged)
    - `supersedes_rule_id` - Points to rule this one replaces
  - Links to both state_code and legislation_source_id
  - Cascade delete when source is deleted
- **rule_collisions** - ✅ Collision detection (created by migration 015)
  - Tracks semantic duplicates, conflicts, overlaps when re-digesting
  - Types: duplicate, semantic, conflict, overlap, supersedes
  - Resolution workflow: keep_both, keep_existing, keep_new, merge, pending

### 5. Preamble System
- **preamble_templates** - Template structures for composing preambles
- **preambles** - Master preamble records (universal, state, page_type, project scopes)
- **preamble_versions** - Version history with status (draft/active/retired)
- **preamble_version_performance** - Performance metrics per version
- **preamble_test_runs** - Individual test run results
- **preamble_compositions** - Composed preamble cache with hash-based lookup
- **preamble_composition_deps** - Dependency tracking for cache invalidation
- **default_page_type_preambles** - System-level defaults
- **project_page_type_preambles** - Project-specific overrides

### 6. Template System (Legacy)
- **templates** - Compliance checking templates
- **template_rules** - Rules associated with templates
- **extraction_templates** - Content extraction configurations

## Schema Status (Updated 2025-10-28)

### ✅ Schema is Complete
All planned tables and columns from DESIGN_NOTES.md have been applied:

1. ✅ `states` - All required columns
2. ✅ `legislation_sources` - All required columns
3. ✅ `legislation_digests` - WITH version and active columns
4. ✅ `rules` - WITH all 5 lineage columns
5. ✅ `rule_collisions` - Created for collision detection
6. ✅ `llm_logs` - Created for comprehensive LLM tracking
7. ✅ `llm_model_config` - Created for per-operation model selection
8. ✅ `page_types` - All required columns including preamble fields

### No Missing Components
The schema is now ready for:
- ✅ Versioning system implementation
- ✅ Collision detection workflow
- ✅ LLM cost dashboard (implemented in LLMTab)
- ✅ Dynamic model configuration per operation type

## Key Indexes (Updated 2025-10-27)

### Performance Indexes
- `idx_legislation_sources_state` on `legislation_sources(state_code)`
- `idx_rules_state_code` on `rules(state_code)`
- `idx_rules_legislation_source` on `rules(legislation_source_id)`
- `idx_rules_active` on `rules(active)`
- `idx_rules_approved` on `rules(approved)`
- ✅ `idx_rules_by_digest` on `rules(legislation_digest_id)` (added by migration 015)
- ✅ `idx_rules_status` on `rules(status)` (added by migration 015)
- ✅ `idx_collisions_by_rule` on `rule_collisions(rule_id)` (added by migration 015)
- ✅ `idx_collisions_by_existing` on `rule_collisions(collides_with_rule_id)` (added by migration 015)
- ✅ `idx_collisions_pending` on `rule_collisions(resolution)` WHERE pending (added by migration 015)
- ✅ 7 indexes on `llm_logs` for common queries (endpoint, operation, model, cost, etc.)

### Unique Constraints
- `legislation_sources`: UNIQUE(state_code, statute_number)
- ✅ `legislation_digests`: UNIQUE(legislation_source_id, active) WHERE active=1 (enforced)

## Data Lineage Flow

```
states (OK, TX, etc.)
  └── legislation_sources (statute text)
       └── legislation_digests (AI interpretation, versioned)
            └── rules (atomic requirements)
                 └── Applied to compliance_checks
```

### Versioning Rules
1. Each legislation_source can have multiple digests (versions)
2. Only ONE digest can be active=1 per source at a time
3. Rules point to BOTH source_id AND digest_id for full lineage
4. When digest is re-run, collision detection compares new rules vs existing
5. Manual edits to rules set `is_manually_modified=1` and detach from digest

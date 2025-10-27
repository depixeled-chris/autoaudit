# SQLite Database Guide

## Overview

The compliance checking system now uses SQLite for centralized data storage instead of scattered JSON files. This provides:

- **Multi-project support** - Manage multiple dealerships/clients
- **Historical tracking** - Full audit trail of compliance checks
- **Template caching** - Reusable compliance decisions
- **Scalability** - Easy to query, report, and analyze
- **Data integrity** - Foreign keys and relationships

## Database Schema

### Core Tables

#### 1. **projects**
Represents clients or dealership groups.

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    state_code TEXT NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

**Example:**
```python
db.create_project(
    name="AllStar CDJR Muskogee",
    state_code="OK",
    description="Oklahoma dealership compliance monitoring"
)
```

#### 2. **templates**
Compliance template metadata (dealer.com, DealerOn, etc.)

```sql
CREATE TABLE templates (
    id INTEGER PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    template_type TEXT DEFAULT 'compliance',
    config JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

#### 3. **template_rules**
Cached compliance decisions for specific rules within templates.

```sql
CREATE TABLE template_rules (
    id INTEGER PRIMARY KEY,
    template_id TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    status TEXT NOT NULL,           -- "compliant", "non_compliant"
    confidence REAL NOT NULL,       -- 0.0 - 1.0
    verification_method TEXT,       -- "text", "visual", "human"
    notes TEXT,
    verified_date TIMESTAMP,
    UNIQUE(template_id, rule_key)
)
```

**Example:**
```python
db.save_template_rule(
    template_id="dealer.com_vdp",
    rule_key="vehicle_id_adjacent",
    status="compliant",
    confidence=0.95,
    verification_method="visual",
    notes="Vehicle ID prominently displayed above price"
)
```

#### 4. **urls**
URLs to monitor for compliance.

```sql
CREATE TABLE urls (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    url TEXT UNIQUE NOT NULL,
    url_type TEXT DEFAULT 'vdp',
    template_id TEXT,
    platform TEXT,
    active BOOLEAN DEFAULT 1,
    check_frequency_hours INTEGER DEFAULT 24,
    last_checked TIMESTAMP,
    created_at TIMESTAMP
)
```

**Example:**
```python
db.add_url(
    url="https://example.com/vehicle.htm",
    project_id=1,
    template_id="dealer.com_vdp",
    platform="dealer.com",
    check_frequency_hours=24
)
```

#### 5. **compliance_checks**
Historical compliance check results.

```sql
CREATE TABLE compliance_checks (
    id INTEGER PRIMARY KEY,
    url_id INTEGER NOT NULL,
    url TEXT NOT NULL,
    state_code TEXT NOT NULL,
    template_id TEXT,
    overall_score INTEGER,
    compliance_status TEXT,         -- "COMPLIANT", "NEEDS_REVIEW", "NON_COMPLIANT"
    summary TEXT,
    llm_input_path TEXT,
    report_path TEXT,
    checked_at TIMESTAMP
)
```

**Example:**
```python
check_id = db.save_compliance_check(
    url="https://example.com/vehicle.htm",
    state_code="OK",
    template_id="dealer.com_vdp",
    overall_score=70,
    compliance_status="NEEDS_REVIEW",
    summary="Found 4 violations, 1 visually verified as compliant",
    llm_input_path="llm_inputs/input_20251024_120000.md",
    report_path="reports/report_20251024_120000.md"
)
```

#### 6. **violations**
Individual violations found during checks.

```sql
CREATE TABLE violations (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL,
    category TEXT NOT NULL,         -- "disclosure", "pricing", "financing"
    severity TEXT NOT NULL,         -- "critical", "high", "medium", "low"
    rule_violated TEXT NOT NULL,
    rule_key TEXT,
    confidence REAL,
    needs_visual_verification BOOLEAN,
    explanation TEXT,
    evidence TEXT,
    created_at TIMESTAMP
)
```

#### 7. **visual_verifications**
Visual verification results (GPT-4V screenshots).

```sql
CREATE TABLE visual_verifications (
    id INTEGER PRIMARY KEY,
    check_id INTEGER NOT NULL,
    violation_id INTEGER,
    rule_key TEXT NOT NULL,
    rule_text TEXT,
    is_compliant BOOLEAN NOT NULL,
    confidence REAL NOT NULL,
    verification_method TEXT,
    visual_evidence TEXT,
    proximity_description TEXT,
    screenshot_path TEXT,
    cached BOOLEAN DEFAULT 0,
    created_at TIMESTAMP
)
```

#### 8. **extraction_templates**
DOM extraction templates for clean scraping.

```sql
CREATE TABLE extraction_templates (
    id INTEGER PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    platform TEXT NOT NULL,
    selectors JSON NOT NULL,
    cleanup_rules JSON,
    extraction_order JSON,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

## Usage Examples

### 1. Create a New Project

```python
from database import ComplianceDatabase

db = ComplianceDatabase("compliance.db")

project_id = db.create_project(
    name="Example Dealership",
    state_code="TX",
    description="Texas dealership group"
)
```

### 2. Add URLs to Monitor

```python
# Single URL
db.add_url(
    url="https://example.com/vehicle1.htm",
    project_id=project_id,
    template_id="dealer.com_vdp",
    platform="dealer.com",
    check_frequency_hours=24
)

# List URLs for a project
urls = db.list_urls(project_id=project_id, active_only=True)
for url_data in urls:
    print(f"{url_data['url']} - Last checked: {url_data['last_checked']}")
```

### 3. Save Compliance Check Results

```python
# After running analysis
check_id = db.save_compliance_check(
    url="https://example.com/vehicle1.htm",
    state_code="TX",
    template_id="dealer.com_vdp",
    overall_score=85,
    compliance_status="COMPLIANT",
    summary="All requirements met",
    report_path="reports/report_123.md"
)

# Save violations
for violation in violations_list:
    db.save_violation(
        check_id=check_id,
        category="pricing",
        severity="high",
        rule_violated="Price must include all fees",
        rule_key="full_price_disclosure",
        confidence=0.9,
        needs_visual_verification=False,
        explanation="Price shown as 'Starting at...' without full disclosure"
    )
```

### 4. Query Historical Data

```python
# Get latest check for a URL
latest = db.get_latest_check("https://example.com/vehicle1.htm")
print(f"Score: {latest['overall_score']}/100")

# Get all checks for a project
checks = db.list_checks(url_id=url_id, limit=10)

# Get violations for a specific check
violations = db.get_violations(check_id)
```

### 5. Template Caching

```python
# Save a rule decision
db.save_template_rule(
    template_id="dealer.com_vdp",
    rule_key="vehicle_id_adjacent",
    status="compliant",
    confidence=0.95,
    verification_method="visual",
    notes="Always displayed in heading above price"
)

# Check cached rule
rule = db.get_template_rule("dealer.com_vdp", "vehicle_id_adjacent")
if rule and rule['confidence'] >= 0.85:
    # Skip expensive visual verification
    print("Using cached decision")
```

### 6. Project Reporting

```python
# Get project summary statistics
summary = db.get_project_summary(project_id)
print(f"""
Project Summary:
- Total URLs: {summary['total_urls']}
- Total Checks: {summary['total_checks']}
- Average Score: {summary['avg_score']}
- Compliant Count: {summary['compliant_count']}
- Total Violations: {summary['total_violations']}
""")
```

## Migration from JSON

If you have existing JSON template files, run the migration script:

```bash
python migrate_to_db.py
```

This will:
1. Create the database schema
2. Import templates from `templates/*.json`
3. Import extraction templates from `extraction_templates/*.json`
4. Create a sample project

## Database Files

- **compliance.db** - Main production database
- **test_compliance.db** - Test database (created by database.py example)
- **backup_YYYYMMDD.db** - Backup copies (create manually)

## Backup Strategy

```python
import shutil
from datetime import datetime

# Backup database
backup_name = f"backup_{datetime.now().strftime('%Y%m%d')}.db"
shutil.copy("compliance.db", backup_name)
```

## Integration with Main System

The main hybrid checker now uses the database automatically:

```python
# In main_hybrid.py
checker = HybridComplianceChecker(
    state_code="OK",
    output_dir="reports"
)

# Internally uses:
# - self.template_manager (uses database)
# - self.extraction_manager (uses database)
```

Templates are automatically:
1. Detected from URL/platform
2. Loaded from database
3. Updated with new verification results
4. Cached for future use

## Benefits Over JSON Files

### Before (JSON Files)
```
templates/
  ├── dealer.com_vdp.json (scattered)
  ├── dealeron_vdp.json
  └── cdk_vdp.json

extraction_templates/
  ├── dealer.com_vdp.json (duplicated)
  ├── dealeron_vdp.json
  └── cdk_vdp.json

No project organization
No historical tracking
Manual file management
Difficult to query
```

### After (SQLite)
```
compliance.db (single file)
  ├── 8 tables with relationships
  ├── Multi-project support
  ├── Full audit trail
  ├── Easy querying
  └── Automatic backups possible
```

## Advanced Queries

### Find All Non-Compliant URLs

```python
cursor = db.conn.cursor()
cursor.execute("""
    SELECT u.url, c.overall_score, c.compliance_status, c.checked_at
    FROM compliance_checks c
    JOIN urls u ON c.url_id = u.id
    WHERE c.compliance_status != 'COMPLIANT'
    ORDER BY c.overall_score ASC
    LIMIT 10
""")
results = cursor.fetchall()
```

### Find Templates Needing More Verification

```python
cursor.execute("""
    SELECT t.template_id, COUNT(tr.id) as rule_count
    FROM templates t
    LEFT JOIN template_rules tr ON t.template_id = tr.template_id
    GROUP BY t.template_id
    HAVING rule_count < 5
""")
```

### Track Compliance Trends

```python
cursor.execute("""
    SELECT
        DATE(checked_at) as date,
        AVG(overall_score) as avg_score,
        COUNT(*) as check_count
    FROM compliance_checks
    WHERE url_id = ?
    GROUP BY DATE(checked_at)
    ORDER BY date DESC
    LIMIT 30
""", (url_id,))
```

## Next Steps

1. **Dashboard** - Build web interface for viewing results
2. **Scheduled Checks** - Automatically re-check URLs based on `check_frequency_hours`
3. **Alerts** - Email notifications for compliance drops
4. **API** - REST API for integration with other systems
5. **Bulk Import** - CSV import for adding many URLs at once

## Support

For questions or issues with the database system, check:
- `database.py` - Core database class
- `template_manager.py` - Template caching integration
- `extraction_templates.py` - Extraction template integration
- `migrate_to_db.py` - Migration script

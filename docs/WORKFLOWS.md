# Key User Workflows

End-to-end workflows from user perspective.

## 1. Upload & Digest Legislation (with Automatic Rule Generation)

**User Goal**: Add new legislation to the system for a state and automatically generate compliance rules.

### Steps
1. User navigates to Config page → States tab
2. Selects state (e.g., Oklahoma)
3. Clicks "Add Legislation" button
4. Opens `AddLegislationModal`
5. Fills form:
   - Uploads PDF/Markdown/Text file
   - State is pre-selected
6. Clicks "Upload & Digest"

### Backend Flow
```
POST /api/states/legislation/upload
  ↓
document_parser_service.py:
  - Extracts text from PDF (PyPDF2)
  - Sends text to OpenAI GPT-4o-mini
  - LLM extracts statute_number, title, effective_date, etc.
  - LLM creates digest (plain language interpretation)
  ↓
Creates:
  - legislation_sources record (original text + metadata)
  - legislation_digests record (single combined digest, version 1)
  ↓
Auto-generates rules:
  - Calls parse_legislation_to_rules()
  - LLM extracts atomic, testable rules
  - Creates rules records linked to digest
  ↓
Returns: {
  legislation_source,
  digest,
  rules_created: N,
  requires_review: true
}
```

### UI Response
- Modal shows success screen
- Displays: "Your document has been digested and the legislation source has been created."
- Shows rules created count
- User next steps:
  1. Close modal
  2. Go to Rules tab to review and approve rules

### Database Changes
- `legislation_sources` table: +1 row
- `legislation_digests` table: +1 row (single combined digest)
- `rules` table: +N rows (automatically generated, unapproved)

---

## 2. Re-Digest Legislation (Manual Rule Regeneration)

**User Goal**: Regenerate rules from existing legislation (e.g., after editing digest).

**Note**: This workflow is now optional since upload automatically generates rules.

### Steps
1. User clicks on legislation source in StateConfigModal
2. Opens `LegislationDetailsModal`
3. Clicks "Re-digest" button
4. Confirms action

### Backend Flow
```
POST /api/rules/legislation/{source_id}/digest
  ↓
rule_service.py:
  - Gets active digest for source
  - Sends legislation text to OpenAI
  - LLM extracts atomic, testable rules
  - Detects collisions with existing rules (semantic similarity)
  ↓
Creates:
  - rules records (one per atomic requirement)
  - rule_collisions records (if collisions detected)
  ↓
Returns: { rules: [...], collisions: [...] }
```

### Collision Detection (Future Feature)
If new rules overlap with existing:
- Collision types: duplicate, semantic, conflict, overlap, supersedes
- AI provides explanation of collision
- Resolution options: keep_both, keep_existing, keep_new, merge

### UI Response
- Rules appear in Config → Rules tab with `approved=false`
- If collisions detected: Shows collision resolution UI (future feature)
- User must manually approve rules before they can be used

### Database Changes
- `rules` table: +N rows
- `rule_collisions` table: +M rows (if collisions - not yet implemented)

---

## 3. Approve Rules

**User Goal**: Review and approve AI-generated rules for production use.

### Steps
1. User navigates to Config → Rules tab
2. Filters by state and `approved=false`
3. Reviews each rule:
   - Reads rule text
   - Checks applicable page types
   - Clicks "Approve" or "Edit"
4. Rule status changes to `approved=true`

### Backend Flow
```
PATCH /api/rules/{rule_id}
  ↓
Updates: rules.approved = true
```

### Why This Matters
- Only approved rules are available when creating projects
- Ensures human review of AI-generated compliance requirements
- Prevents automatic application of potentially incorrect rules

---

## 4. Create Project

**User Goal**: Set up compliance monitoring for a dealership.

### Steps
1. User navigates to Projects page
2. Clicks "New Project" button
3. Opens `CreateProjectModal`
4. Fills form:
   - Project name (e.g., "Bob's Auto Sales")
   - State (e.g., Oklahoma)
   - Base URL (e.g., "https://bobsauto.com")
   - Description (optional)

### Validation
Frontend checks:
```typescript
const { data: rulesData } = useGetRulesQuery({
  state_code: selectedState,
  approved: true
});

if (!rulesData?.items?.length) {
  setError("No approved rules for this state");
  return;
}
```

### Backend Flow
```
POST /api/projects
  ↓
Creates:
  - projects record with state_code
  ↓
Project inherits all approved rules for that state
```

### UI Response
- Redirects to ProjectDetailPage
- Shows empty URLs list with "Add URL" button

### Database Changes
- `projects` table: +1 row

---

## 5. Add URLs to Project

**User Goal**: Add specific pages to monitor for compliance.

### Steps
1. User is on ProjectDetailPage
2. Clicks "Add URL" button
3. Opens `AddURLModal`
4. Fills form:
   - URL (e.g., "https://bobsauto.com/inventory/new")
   - Page type (e.g., "New Inventory")
   - Check frequency (hours)
5. Clicks "Add URL"

### Backend Flow
```
POST /api/urls
  ↓
Creates:
  - urls record linked to project
  ↓
Schedules periodic compliance checks (based on frequency)
```

### UI Response
- URL appears in URLList
- Shows last checked timestamp (null initially)
- "Check Now" button available

### Database Changes
- `urls` table: +1 row

---

## 6. Run Compliance Check

**User Goal**: Check a URL for compliance violations.

### Steps
1. User clicks "Check Now" on a URL
2. Backend runs compliance check

### Backend Flow
```
POST /api/checks
  ↓
compliance_service.py:
  - Takes screenshot of URL
  - Extracts text from page
  - Composes preamble from:
    • Universal preamble
    • State preamble (from approved rules)
    • Page type preamble
    • Project-specific preamble (if any)
  - Sends to OpenAI with screenshot + text
  - LLM identifies violations
  ↓
Creates:
  - compliance_checks record
  - violations records (one per violation found)
  - visual_verifications records (if visual confirmation needed)
  ↓
Returns: { check_id, overall_score, violations: [...] }
```

### Preamble Composition
Hierarchical composition:
```
1. Universal (applies to all)
   ↓
2. State-specific (Oklahoma rules)
   ↓
3. Page type (New Inventory guidance)
   ↓
4. Project override (if dealership has special requirements)
```

### UI Response
- Check status updates to "Complete"
- Overall score displayed (0-100)
- Violations list shown with severity
- Can click to view full report

### Database Changes
- `compliance_checks` table: +1 row
- `violations` table: +N rows
- `llm_calls` table: +M rows (token tracking)

---

## 7. View Check Results

**User Goal**: Review compliance violations for a check.

### Steps
1. User clicks on check in history
2. Opens `CheckDetailModal`
3. Views:
   - Overall score
   - List of violations with:
     • Severity (critical/important/minor)
     • Rule violated
     • Evidence/location
     • Screenshot (if applicable)
4. Can download full report (markdown)

### Data Flow
```
GET /api/checks/{check_id}
GET /api/checks/{check_id}/violations
GET /api/reports/{check_id}/markdown
```

---

## 8. Intelligent Project Setup (Advanced)

**User Goal**: Automatically discover page types and create project.

### Steps
1. User clicks "Intelligent Setup" button
2. Opens modal with base URL input
3. Enters dealership URL
4. AI crawls site and detects page types
5. Shows discovered URLs with detected types
6. User confirms or adjusts
7. Project + URLs created in one step

### Backend Flow
```
POST /api/projects/intelligent-setup
  ↓
intelligent_setup_service.py:
  - Crawls homepage
  - Detects page types using LLM (screenshots + structure)
  - Finds common pages (VDP, Inventory, Financing, etc.)
  ↓
Creates:
  - project record
  - urls records (bulk creation)
  ↓
Returns: { project_id, urls: [...] }
```

### AI Detection
Uses OpenAI Vision to identify:
- Homepage
- Vehicle Detail Pages (VDP)
- Inventory listings
- Financing calculators
- Special offers
- Service pages

---

## 9. Manage Preambles (Advanced)

**User Goal**: Customize compliance prompts for LLM.

### Workflow
1. Navigate to Config → Preambles tab
2. Select scope (universal, state, page type, project)
3. Create preamble with template
4. Version management:
   - Create new version
   - Mark as active
   - Track performance metrics
5. Test preamble against URLs
6. Compare versions by performance

### Versioning
- Each preamble can have multiple versions
- Only one version active at a time
- Performance tracked (scores, cost, duration)
- A/B testing support via test runs

---

## 10. Demo Data Management (Admin)

**User Goal**: Reset system for demo or development.

### Steps
1. Navigate to Config → Other tab
2. Click nuclear reset buttons (production-protected)
3. Options:
   - Delete all rules
   - Delete all preambles
   - Delete all projects
   - Delete all users (except admin)
   - Delete all legislation
   - Delete EVERYTHING (nuclear option)

### Safety
```python
if settings.PRODUCTION_MODE:
    raise HTTPException(403, "Demo endpoints disabled in production")
```

All demo endpoints check production mode before executing.

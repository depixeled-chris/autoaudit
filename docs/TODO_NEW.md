# New & Pending Tasks

**Last Updated**: 2025-10-27

## 🔥 High Priority

### Implement Collision Detection
- Create collision detection service in `services/rule_service.py`
- Semantic similarity comparison using OpenAI embeddings
- Collision types: duplicate, semantic, conflict, overlap, supersedes
- Store collisions in `rule_collisions` table

**Why**: Prevents duplicate/conflicting rules when re-digesting.
**See**: [DESIGN_NOTES.md](DESIGN_NOTES.md)

### Build Collision Resolution UI
- Create `CollisionResolutionModal` component
- Side-by-side comparison view (existing vs new rule)
- AI explanation of collision
- Resolution actions: keep_both, keep_existing, keep_new, merge
- Batch resolution UI for multiple collisions

**Why**: Human review required for all collisions.
**See**: [FRONTEND_STRUCTURE.md](FRONTEND_STRUCTURE.md)

### Investigate Migration 13 Mystery
- Forensic analysis: how was migration 13 applied?
- Check for hidden migration runner scripts
- Document findings in MIGRATION_SYSTEM.md
- Decide: keep current state or rebuild?

**Why**: Need to understand how orphaned migrations got executed.
**See**: [MIGRATION_SYSTEM.md](MIGRATION_SYSTEM.md)

---

## 📋 Medium Priority

### LLM Cost Dashboard
- Create `LLMUsagePage` component
- Charts: costs by operation, model, time period
- Top expensive operations
- Cost per project/URL
- Token usage trends

**Depends on**: `llm_logs` table

### Enhanced Re-digest Workflow
- Show version history when re-digesting
- Preview new rules before creating
- Collision detection before committing
- Rollback to previous digest version

### Rule Approval Workflow
- Bulk approve rules
- Filtering by collision status
- Rule editing preserves original AI text
- Approval history/audit trail

---

## 🔧 Low Priority (Technical Debt)

### Migration System Cleanup
- Archive orphaned files in `server/migrations/`
- Add README to orphaned files explaining deprecation
- Consolidate to single migration system
- Add migration rollback support

### Frontend Modernization
- Complete ConfigPage.tsx → pages/Config/Config.tsx migration
- Implement code splitting for routes
- Add proper error boundaries
- Implement loading skeletons

### Testing
- Add backend unit tests (pytest)
- Add frontend component tests (Vitest + React Testing Library)
- E2E tests for critical workflows (Playwright)
- API contract tests

### Performance
- Implement pagination for large lists (rules, checks)
- Add database indexes for slow queries
- React.memo optimization for expensive components
- Image optimization for screenshots

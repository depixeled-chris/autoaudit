# Rule Deletion Logic

**Last Updated**: 2025-10-27

## Overview

Rules can be deleted in different contexts, and the deletion behavior differs based on **what is being deleted** and **the state of the rule**.

## Rule Protection

**Protected Rules** are rules that have been:
- **Approved** (`approved = 1`), OR
- **Manually Modified** (`is_manually_modified = 1`)

Protected rules represent human investment and should be preserved when possible.

## Deletion Scenarios

### 1. Deleting Legislation Source

**What happens**: Delete the entire legislation source (PDF/document)

**Rule behavior**: **ALL rules are deleted**, regardless of protection status.

**Rationale**: If the source legislation is removed, all derived rules become invalid.

**Method**: `delete_rules_by_legislation_source(source_id)`

```python
# Deletes ALL rules - no protection
DELETE FROM rules WHERE legislation_source_id = ?
```

**Example**: User uploads Oklahoma statute 12-1145.pdf, generates 50 rules, approves 10 of them. Later, user realizes they uploaded the wrong statute and deletes the source. **All 50 rules are deleted**, including the 10 approved ones.

---

### 2. Re-digesting Legislation (Iterative Refinement)

**What happens**: User clicks "Re-digest" to iteratively refine the rule set - looking for new rules or re-interpreting existing ones.

**Rule behavior**: **Protected rules are preserved**, unprotected rules are deleted and regenerated.

**Rationale**: Digest is an **iterative process**. Each re-digest should:
- Look for new rules the AI might have missed
- Re-interpret ambiguous rules with improved prompts
- **Avoid duplicating rules that are already well-defined** in approved/manually created rules
- Preserve all human investment (approvals, edits)

**Method**: `delete_rules_by_digest(digest_id)`

```python
# Delete only unapproved, unmodified rules
# Protected rules keep their digest_id for full lineage trail
DELETE FROM rules
WHERE legislation_digest_id = ?
AND approved = 0
AND is_manually_modified = 0
```

**Protection Mechanism**: Rules are protected by the `approved` and `is_manually_modified` flags. The digest lineage (`legislation_digest_id`) is NEVER removed - this preserves the full trail of where the rule came from.

**Example**: User digests Oklahoma statute (digest_id=100), gets 50 rules. User approves 10 rules and manually edits 5 others. User clicks "Re-digest" (creates digest_id=101). Result:
- **35 unprotected rules**: Deleted and regenerated with `legislation_digest_id = 101`
- **10 approved rules**: Preserved with original `legislation_digest_id = 100` and `approved = 1`
- **5 manually edited rules**: Preserved with original `legislation_digest_id = 100` and `is_manually_modified = 1`

All rules maintain full lineage trail - you can always see which digest version created each rule.

---

### 3. Individual Rule Deletion

**What happens**: User clicks "Delete" on a specific rule in the UI.

**Rule behavior**: Rule is deleted regardless of protection status.

**Rationale**: Explicit user action to remove a specific rule.

**Method**: `delete_rule(rule_id)`

```python
# Direct deletion - no protection
DELETE FROM rules WHERE id = ?
```

---

## Full Lineage Trail

**Every rule maintains complete lineage**:

- `legislation_source_id`: **Always set** - ties to source legislation (statute/regulation)
- `legislation_digest_id`: **Always set** - shows which digest version created this rule
- `approved`: Flag indicating user has reviewed and approved
- `is_manually_modified`: Flag indicating user has edited the rule text
- `status`: Lifecycle state (active, pending_review, superseded, merged)

When a digest is replaced via re-digest:
- New rules get the new `legislation_digest_id`
- Protected rules (approved/modified) keep their original `legislation_digest_id`
- **Full trail is preserved** - you can query: "Show me all rules from digest version 100"
- Protected rules continue functioning in compliance checks with their original digest lineage intact

## Collision Detection

**Purpose**: Avoid creating duplicate rules that are already well-defined in approved/manual rules.

When re-digesting creates new rules that collide with protected (orphaned) rules:

1. New rules are created with their own `legislation_digest_id`
2. **Collision detection compares new rules with ALL active rules** (including orphaned ones)
3. Collisions are flagged in `rule_collisions` table with types:
   - `duplicate` - Exact or near-exact match
   - `semantic` - Same meaning, different wording
   - `conflict` - Contradictory requirements
   - `overlap` - Partial overlap in scope
   - `supersedes` - New rule replaces old rule
4. User resolves collisions manually via UI:
   - `keep_both` - Both rules are valid
   - `keep_existing` - Delete new rule, keep approved one
   - `keep_new` - Replace old rule (mark as superseded)
   - `merge` - Combine into single rule

**This ensures the iterative digest process doesn't duplicate work** - the AI won't recreate rules that users have already perfected through approval or manual editing.

## Code Locations

- **delete_rules_by_legislation_source()**: `server/services/rule_service.py:222`
  - Deletes ALL rules when source is deleted
- **delete_rules_by_digest()**: `server/services/rule_service.py:255`
  - Protects approved/modified rules during re-digest
- **get_protected_rules_count()**: `server/services/rule_service.py:322`
  - Counts how many rules will be protected

## UI Implications

### Before Re-digest

Show warning:
```
⚠️ Re-digesting will replace unapproved rules.
Protected: 15 approved/edited rules will be preserved.
Deletable: 35 unapproved rules will be regenerated.
```

### Before Source Deletion

Show warning:
```
⚠️ Deleting this legislation source will delete ALL 50 rules,
including 15 approved/edited rules. This cannot be undone.
```

## Database Schema Support

The `rules` table has these columns to support this logic:

- `approved` (BOOLEAN) - Marks rules the user has reviewed and approved
- `is_manually_modified` (BOOLEAN) - Marks rules the user has edited
- `legislation_source_id` (INTEGER) - Parent source (cascade delete)
- `legislation_digest_id` (INTEGER) - Parent digest (orphaned when re-digested)
- `status` (TEXT) - Lifecycle state: active, pending_review, superseded, merged

## Best Practices

1. **Always check protected count** before re-digesting (UI should display this)
2. **Orphaned rules are OK** - they continue to work in compliance checks
3. **Collision detection handles duplicates** - re-digest won't create silent conflicts
4. **Source deletion is final** - warn users clearly in UI

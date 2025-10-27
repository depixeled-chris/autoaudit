# Proposed Schema Changes for Legislation → Rules Lineage

## Problem
Rules currently link to `legislation_source_id` but not `legislation_digest_id`, breaking the lineage chain and preventing proper versioning.

## Solution: Add Digest Versioning + Rules Lineage

### 1. Add to `legislation_digests` table:
```sql
ALTER TABLE legislation_digests ADD COLUMN version INTEGER DEFAULT 1;
ALTER TABLE legislation_digests ADD COLUMN active BOOLEAN DEFAULT 1;

-- Create unique constraint: only one active digest per source
CREATE UNIQUE INDEX idx_one_active_digest_per_source
ON legislation_digests(legislation_source_id, active)
WHERE active = 1;
```

### 2. Add to `rules` table:
```sql
ALTER TABLE rules ADD COLUMN legislation_digest_id INTEGER;
ALTER TABLE rules ADD COLUMN is_manually_modified BOOLEAN DEFAULT 0;
ALTER TABLE rules ADD COLUMN original_rule_text TEXT; -- Preserve AI-generated text

-- Add foreign key
ALTER TABLE rules ADD FOREIGN KEY (legislation_digest_id)
REFERENCES legislation_digests(id) ON DELETE SET NULL;
```

## Mental Model Flow

### Initial Upload & Parse
```
1. Upload PDF → legislation_source created
2. AI parse → legislation_digest created (version=1, active=true)
3. (No rules yet, user must click "Re-digest" aka "Generate Rules")
```

### Generate Rules (aka "Re-digest")
```
1. User clicks "Generate Rules" on digest
2. AI generates rules → rules created with:
   - legislation_source_id = source.id
   - legislation_digest_id = digest.id
   - is_manually_modified = false
   - original_rule_text = rule_text (same initially)
   - active = true
   - approved = false (requires review)
```

### Re-digest (Generate New Version)
```
1. User clicks "Re-digest" on legislation source
2. System:
   a. Mark current digest as active=false
   b. Deactivate all rules from old digest (active=false)
   c. Create new digest (version=old_version+1, active=true)
   d. Generate new rules from new digest
3. Result:
   - Old digest preserved (active=false)
   - Old rules preserved but inactive
   - New digest is source of truth
   - New rules are active
```

### Manual Rule Edits
```
1. User edits a rule in UI
2. System updates:
   - rule_text = new_text
   - is_manually_modified = true
   - original_rule_text = [unchanged, preserves AI version]
   - updated_at = now()
   - Keep legislation_digest_id (tracks origin)
```

## Benefits

1. **Clear Lineage**: Rule → Digest → Source (full chain)
2. **Version History**: Can see all digest versions and their rules
3. **Single Truth**: Only one active digest per source
4. **Edit Tracking**: Know which rules have been manually modified
5. **Rollback Capability**: Could reactivate old digest version if needed
6. **Audit Trail**: Preserve original AI-generated text even after edits

## UI Changes Needed

### State Config → Legislation Details Modal
- Show digest version number: "Digest v2 (Active)"
- Show if rules have been generated yet
- "Generate Rules" button (if no rules yet)
- "Re-digest" button → warns about creating new version

### Rules Tab
- Show which digest generated each rule
- Show if manually modified
- Option to view original AI text vs current
- Filter by active/inactive

## Migration Plan

1. Create migration script to:
   - Add new columns with defaults
   - Populate existing rules with digest_id (find by source_id + created_at proximity)
   - Set all existing digests to active=true (will violate constraint if multiple exist)
   - Manual resolution for any conflicts

2. Update services:
   - Rule generation service to use digest_id
   - Re-digest service to version properly
   - Rule update service to track modifications

3. Update UI:
   - Show digest versions
   - Show rule lineage
   - Better "Re-digest" warnings

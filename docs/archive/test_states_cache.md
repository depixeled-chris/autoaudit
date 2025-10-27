# Cache Invalidation Debug

## Current Setup

**getStateByCode**:
- Tags: `{ type: 'States', id: 'OK' }`

**updateState**:
- Invalidates: `{ type: 'States', id: 1 }`, `{ type: 'States', id: result?.code }`, `'States'`

## Problem
When updating state ID 1 (Oklahoma/OK), we invalidate:
1. `{ type: 'States', id: 1 }` ✓
2. `{ type: 'States', id: 'OK' }` ✓ (from result.code)
3. `'States'` ✓ (general tag)

This SHOULD work. Let me check if result is actually being returned...

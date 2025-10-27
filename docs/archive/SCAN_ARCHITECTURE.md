# Compliance Scan Architecture

## Overview

The compliance scanning system now supports two distinct processing modes based on URL type and scan trigger:

## Scan Types

### 1. Immediate Scans (Synchronous)
**Used for:**
- VDP (Vehicle Detail Pages)
- Homepage scans
- Manual forced rescans on non-inventory URLs

**Characteristics:**
- Runs synchronously (blocks until complete)
- Takes 30-60 seconds to complete
- Uses real-time OpenAI API calls
- Returns complete results immediately
- More expensive per scan (real-time API pricing)

**Implementation:**
```python
# In ScanService.force_rescan_immediate()
result = await checker.check_url(url, save_formats=['json', 'markdown'])
```

### 2. Batch Scans (Asynchronous)
**Used for:**
- Inventory page scans
- Scheduled periodic scans
- Bulk scanning operations

**Characteristics:**
- Schedules scan for later processing
- Returns immediately with batch ID
- Uses OpenAI Batch API (50% cost savings)
- Results available within 24 hours
- Cost-effective for large-scale scanning

**Implementation:**
```python
# In ScanService.schedule_batch_scan()
batch_id = await openai_batch_api.submit(urls)
# Returns immediately, processes asynchronously
```

## Decision Logic

The `/api/urls/{url_id}/rescan` endpoint automatically determines scan type:

```python
if url_type == 'inventory':
    # Use batch processing
    result = await scan_service.schedule_batch_scan([url_id])
else:
    # Use immediate processing
    result = await scan_service.force_rescan_immediate(url_id)
```

## URL Types

- **`homepage`**: Main dealership page → Immediate scan
- **`vdp`**: Vehicle detail page → Immediate scan
- **`inventory`**: Vehicle search/listing page → Batch scan
- **`custom`**: Custom pages → Immediate scan

## Database Integration

All scans (both types) save results to:
- `compliance_checks` table (main check record)
- `violations` table (rule violations found)
- `visual_verifications` table (visual confirmation results)

The `url_id` links scans to monitored URLs for tracking scan history.

## Future Enhancements

### Batch API Integration (TODO)
Currently, batch scans are marked as "scheduled" but not yet integrated with OpenAI Batch API.

**Next steps:**
1. Create batch submission service
2. Implement batch status polling
3. Add batch result retrieval
4. Create scheduled job for batch processing

### Scheduled Scanning
Use `ScanService.get_urls_needing_scan()` to find URLs that:
- Have never been checked
- Last check was more than `check_frequency_hours` ago

**Example cron job:**
```python
# Run every hour
urls_to_scan = scan_service.get_urls_needing_scan()

# Split by type
inventory_urls = [u for u in urls_to_scan if u['url_type'] == 'inventory']
other_urls = [u for u in urls_to_scan if u['url_type'] != 'inventory']

# Process appropriately
if inventory_urls:
    await scan_service.schedule_batch_scan([u['id'] for u in inventory_urls])

for url in other_urls:
    await scan_service.force_rescan_immediate(url['id'])
```

## API Endpoints

### Force Rescan
```
POST /api/urls/{url_id}/rescan?skip_visual=false
```

**Response (Immediate):**
```json
{
  "scan_type": "immediate",
  "status": "completed",
  "check_id": 123,
  "url_id": 45,
  "compliance_status": "COMPLIANT",
  "overall_score": 95,
  "violations_count": 2,
  "completed_at": "2025-01-26T10:30:00"
}
```

**Response (Batch):**
```json
{
  "scan_type": "batch",
  "status": "scheduled",
  "batch_id": "batch_20250126_103000",
  "url_count": 1,
  "scheduled_at": "2025-01-26T10:30:00",
  "message": "Inventory scan scheduled for batch processing"
}
```

## Service Layer

### ScanService Methods

#### `force_rescan_immediate(url_id, skip_visual=False)`
- Validates URL is not inventory type
- Runs compliance check synchronously
- Saves results to database
- Updates `last_checked` timestamp
- Returns complete check results

#### `schedule_batch_scan(url_ids, batch_name=None)`
- Validates all URLs are active
- Creates batch identifier
- Marks URLs for batch processing
- Returns batch details
- (TODO: Submit to OpenAI Batch API)

#### `get_urls_needing_scan(project_id=None, url_type=None)`
- Queries URLs due for scanning
- Filters by check frequency
- Returns list of URL records
- Use for scheduled scan jobs

## Frontend Integration

The force rescan button in URLList component:
- Shows spinning icon during scan
- Handles both immediate and batch responses
- Updates UI when scan completes
- Displays appropriate status messages

```typescript
const handleForceRescan = async (id: number) => {
  const result = await forceRescan(id).unwrap();

  if (result.scan_type === 'immediate') {
    // Show completion message with results
  } else {
    // Show batch scheduled message
  }
};
```

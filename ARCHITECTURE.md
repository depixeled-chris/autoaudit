# Multi-Tier Compliance Analysis Architecture

## Overview

The system uses a **cost-optimized, template-aware escalation strategy** for compliance checking:

```
Text Analysis → Visual Confirmation → Human Review
   (Fast)            (Moderate)          (Final)
  GPT-4.1-nano         GPT-4V            Manual
```

## Why This Architecture?

### Problem with Text-Only Analysis:
- Regulations care about **visual compliance** ("conspicuous", "adjacent")
- Markdown strips all CSS layout information
- Can't judge proximity or prominence from linearized text
- ~80% of scraped content is navigation noise

### Solution: Layered Verification
1. **Text analysis first** - Fast, cheap, catches obvious violations
2. **Visual confirmation when uncertain** - Screenshots for spatial/visual rules
3. **Template caching** - Reuse visual analysis across similar pages
4. **Human review for edge cases** - Final arbiter for critical decisions

---

## System Components

### 1. Text Analyzer (`analyzer.py`)
- **Model:** GPT-4.1-nano
- **Input:** Cleaned markdown
- **Output:** Violations with confidence scores
- **Triggers visual verification when:**
  - Confidence < 0.7 on HIGH/CRITICAL violations
  - Rule involves spatial judgment ("adjacent", "conspicuous")
  - Layout positioning is critical

**Example Response:**
```json
{
  "violations": [
    {
      "rule_violated": "Vehicle ID adjacent to price",
      "rule_key": "vehicle_id_adjacent",
      "confidence": 0.6,
      "severity": "high",
      "needs_visual_verification": true,
      "evidence": "Heading appears 2 lines above price in markdown..."
    }
  ]
}
```

### 2. Visual Analyzer (`visual_analyzer.py`)
- **Model:** GPT-4o (vision-enabled)
- **Input:** Full-page screenshot
- **Output:** Visual compliance verdict
- **Only called when:** Text analysis is uncertain

**Example Response:**
```json
{
  "is_compliant": true,
  "confidence": 0.95,
  "visual_evidence": "Vehicle heading '2022 Chevrolet Silverado' appears in large text directly above price card",
  "proximity_description": "Heading and price are in the same visual module, separated by ~20px",
  "verification_method": "visual"
}
```

### 3. Template Manager (`template_manager.py`)
- **Purpose:** Cache compliance decisions by template
- **Key Insight:** dealer.com template compliance is consistent across ALL dealer.com sites
- **Avoids:** Re-checking the same template rules repeatedly

**Template Config Example:**
```json
{
  "template_id": "dealer.com_vdp",
  "known_compliance": {
    "vehicle_id_adjacent": {
      "status": "compliant",
      "confidence": 0.95,
      "verified_date": "2025-10-24",
      "verification_method": "visual",
      "notes": "Dealer.com VDP always shows vehicle heading above price in same card"
    },
    "dealer_name_conspicuous": {
      "status": "non_compliant",
      "confidence": 0.90,
      "verified_date": "2025-10-24",
      "verification_method": "visual",
      "notes": "Name only in footer, not in main listing"
    }
  }
}
```

---

## Workflow

### Step 1: Text Analysis
```python
# Analyze with GPT-4.1-nano
text_result = await analyzer.analyze_compliance(markdown_content)

# Check violations
for violation in text_result['violations']:
    if violation['needs_visual_verification']:
        # Escalate to visual verification
        visual_result = await visual_analyzer.verify(screenshot, violation)
```

### Step 2: Template Check
```python
# Detect template
template_id = template_manager.detect_template(url, platform, html)

# Check if we've already verified this rule for this template
if template_manager.should_skip_visual_verification(template_id, rule_key):
    # Use cached decision
    cached_status = template_manager.get_rule_status(template_id, rule_key)
else:
    # Perform visual verification and cache result
    visual_result = await visual_analyzer.verify(...)
    template_manager.update_rule_status(template_id, rule_key, ...)
```

### Step 3: Visual Verification (if needed)
```python
# Capture screenshot
screenshot_path = await page.screenshot(full_page=True)

# Verify specific rule
result = await visual_analyzer.verify_visual_compliance(
    screenshot_path=screenshot_path,
    rule_to_verify="Vehicle identification adjacent to price",
    context={"url": url, "state": "Oklahoma"}
)
```

### Step 4: Human Review Queue (if needed)
- Critical violations with low confidence
- Contradictory text vs visual results
- Novel template patterns
- High-stakes compliance decisions

---

## Cost Optimization

### Per-URL Costs:

**Text Analysis Only:**
- ~6,500 tokens @ $0.05/1M input = **$0.0003**
- ~99% of analyses (when template is known)

**Text + Visual:**
- Text: $0.0003
- Visual: ~$0.01-0.02 per image
- **Total: ~$0.015**
- Only ~10% of first-time template checks

**Amortized Cost:**
- First dealer.com site: $0.015 (includes visual)
- Next 99 dealer.com sites: $0.0003 each (text only, use cache)
- **Average: $0.0004 per URL at scale**

### Comparison:
- **Current text-only:** Unreliable, but cheap ($0.0003)
- **Visual-only:** Accurate, but expensive ($0.02)
- **Our hybrid:** Accurate AND cheap ($0.0004 average)

---

## Template Detection

### Supported Platforms:
1. **dealer.com** - Most common US dealership platform
2. **DealerOn** - Popular alternative
3. **CDK Global** - Enterprise solution
4. **AutoTrader** - Listing site
5. **Cars.com** - Listing site
6. **Custom** - Domain-specific templates

### Detection Logic:
```python
def detect_template(url, platform, html):
    if "dealer.com" in html or platform == "dealer.com":
        return "dealer.com_vdp"
    elif "dealeron" in html.lower():
        return "dealeron_vdp"
    else:
        # Custom template per domain
        domain = urlparse(url).netloc
        return f"custom_{domain}"
```

---

## Future Enhancements

### Phase 1 (Current):
- ✅ Text analysis with confidence scores
- ✅ Visual verification system
- ✅ Template detection & caching

### Phase 2 (Next):
- [ ] Smart DOM extraction (reduce noise)
- [ ] Selective screenshots (price card only, not full page)
- [ ] Template-specific CSS selectors
- [ ] Batch visual verification

### Phase 3 (Advanced):
- [ ] ML-based template classification
- [ ] Automated template learning
- [ ] A/B testing compliance improvements
- [ ] Real-time compliance monitoring

---

## Key Principles

1. **Text First:** Always try text analysis first (fast & cheap)
2. **Visual When Uncertain:** Use vision for spatial/layout rules
3. **Cache Aggressively:** Templates are consistent, reuse decisions
4. **Human as Final Arbiter:** Machine suggests, human decides critical cases
5. **Cost-Conscious:** Optimize for accuracy AND affordability
6. **Template-Aware:** Leverage template consistency across sites

---

## Example: Complete Analysis Flow

```python
# 1. Scrape page
scraped_data = await scraper.scrape_page(url)
template_id = template_manager.detect_template(url, scraped_data['platform'], scraped_data['html'])

# 2. Text analysis
markdown = converter.html_to_markdown(scraped_data['html'])
text_result = await analyzer.analyze_compliance(markdown, state_rules)

# 3. Check which violations need visual confirmation
uncertain_violations = [
    v for v in text_result['violations']
    if v['needs_visual_verification'] and v['confidence'] < 0.7
]

# 4. Visual verification (with caching)
for violation in uncertain_violations:
    rule_key = violation['rule_key']

    # Check template cache
    if template_manager.should_skip_visual_verification(template_id, rule_key):
        cached = template_manager.get_rule_status(template_id, rule_key)
        violation['final_status'] = cached['status']
        violation['final_confidence'] = cached['confidence']
    else:
        # Perform visual verification
        visual_result = await visual_analyzer.capture_and_verify(
            page=page,
            rule=violation['rule_violated'],
            context={'url': url, 'state': state_rules.state}
        )

        # Update template cache
        template_manager.update_rule_status(
            template_id=template_id,
            rule=rule_key,
            status="compliant" if visual_result['is_compliant'] else "non_compliant",
            confidence=visual_result['confidence'],
            verification_method="visual",
            notes=visual_result['visual_evidence']
        )

        violation['final_status'] = visual_result['is_compliant']
        violation['final_confidence'] = visual_result['confidence']

# 5. Generate final report
report = reporter.generate_report(text_result, visual_results)
```

---

## Testing Strategy

### Unit Tests:
- Text analyzer with known compliant/non-compliant examples
- Visual analyzer with screenshot fixtures
- Template detection accuracy

### Integration Tests:
- Full flow: text → visual → cache
- Template caching behavior
- Cost tracking

### Real-World Validation:
- Test on 100 different dealership sites
- Compare text-only vs hybrid accuracy
- Measure cache hit rate
- Calculate actual cost savings

---

## Success Metrics

**Accuracy:**
- Text-only baseline: ~60-70% (current)
- Text + Visual target: ~90-95%
- With template caching: ~95%+ (reuse verified decisions)

**Cost:**
- Text-only: $0.0003/URL
- Target with hybrid: $0.0004/URL average (1.3x cost for 30% accuracy gain)

**Speed:**
- Text analysis: ~10s
- Visual verification: ~15s (only first time per template)
- Cached template: ~10s (text-only speed)

---

This architecture balances **accuracy, cost, and speed** by using the right tool for each task and aggressively caching template-level decisions.

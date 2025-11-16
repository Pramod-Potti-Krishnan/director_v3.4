# L02 Analytics Integration - Complete Diagnosis

**Date**: November 16, 2025
**Issue**: L02 analytics slides showing blank screen
**Root Cause**: Mismatch between Analytics Service output and Layout Builder expectations

---

## 🎯 The Problem

Analytics Service v3 is generating L02 slides, but they render as blank screens in Layout Builder.

---

## 📋 Layout Builder L02 Specification

According to `/agents/layout_builder_main/v7.5-main/LAYOUT_SPECIFICATIONS.md`:

### L02 Element Mapping

| Element | Content Field | Type | Dimensions |
|---------|---------------|------|------------|
| Title | `slide_title` | **Text** | Full width |
| Subtitle | `element_1` | **Text** | Full width |
| Diagram/Chart | `element_3` | **HTML/Diagram/Chart** | 1260×720px (left, 21 grids) |
| Explanation | `element_2` | **Text** | Right side (8 grids × 12 grids) |
| Footer | `presentation_name` | **Text** | Bottom |
| Logo | `company_logo` | Image/Emoji | Bottom right |

### Expected Content Structure
```json
{
  "layout": "L02",
  "content": {
    "slide_title": "Process Overview",
    "element_1": "Workflow explanation",
    "element_3": "<div>Diagram or Chart HTML</div>",  // ← HTML allowed
    "element_2": "Detailed explanation text for the diagram or chart",  // ← PLAIN TEXT expected
    "presentation_name": "Presentation Name",
    "company_logo": "🏢"
  }
}
```

**Critical**: `element_2` is typed as **"Text"** - Layout Builder will handle formatting.

---

## 🔍 What Analytics Service is Sending

### Current Analytics Service Response
```json
{
  "content": {
    "element_3": "<div class='l02-chart-container' style='width: 1260px; height: 720px;'>...<canvas>...</canvas></div>",
    "element_2": "<div class='l02-observations-panel' style='width: 540px; height: 720px; padding: 40px 32px; background: #f8f9fa;'><h3>Key Insights</h3><div>The line chart illustrates...</div></div>"
  }
}
```

### Problem with element_2
Analytics Service is sending **formatted HTML** with:
- `<div>` wrapper with explicit dimensions (540px × 720px)
- Background color (`#f8f9fa`)
- Padding and styling
- `<h3>` tags for headings
- Nested `<div>` tags

**But Layout Builder expects**: Plain text that it will format itself.

---

## ✅ What SHOULD Be Sent

### Correct Structure
```json
{
  "content": {
    "element_3": "<div class='l02-chart-container' style='width: 1260px; height: 720px;'>...<canvas>...</canvas></div>",

    "element_2": "The line chart illustrates quarterly revenue growth, with figures increasing from $100,000 in Q1 to $180,000 in Q4, resulting in an average revenue of $138,750. This upward trend indicates robust business performance over the year."
  }
}
```

**Changes needed**:
- ✅ `element_3`: Keep as-is (full HTML with Chart.js)
- ❌ `element_2`: Remove ALL HTML tags, send plain text only

---

## 🔧 Required Fixes

### Option 1: Analytics Service Change (Recommended)
**Location**: Analytics Service v3 L02 endpoint
**File**: Likely `generate_L02_response()` or similar

**Current Code** (assumed):
```python
element_2_html = f"""
<div class="l02-observations-panel" style="...">
    <h3>Key Insights</h3>
    <div>{observations_text}</div>
</div>
"""
```

**Fixed Code**:
```python
# For L02, element_2 should be plain text only
element_2_text = observations_text  # No HTML wrapper
```

### Option 2: Layout Builder Change (Alternative)
**Location**: Layout Builder v7.5 frontend
**File**: Likely `builder.html` or rendering logic

**Current Behavior**: Expects plain text in element_2, doesn't render HTML
**Needed Change**: Accept and render HTML in element_2 for L02 layouts

**Update L02 spec**:
```markdown
| Explanation | `element_2` | **HTML** (was: Text) | Right side (8 grids × 12 grids) |
```

---

## 📊 Current Test Results

### Test Presentation IDs
All showing blank screens:
1. `8ad5ed63-1368-47f0-a413-4280a2294058` (layout: L25, variant_id: L02)
2. `3ae42050-a788-432b-b4a9-18c17d2f4a87` (layout: L25)
3. `2237cf7f-7ed5-4179-ae1a-69c930154a40` (layout: L02) ← **Correct layout type**

### Data Verification
```bash
curl https://web-production-f0d13.up.railway.app/api/presentations/2237cf7f-7ed5-4179-ae1a-69c930154a40
```

**Saved Data**:
- ✅ `layout: "L02"` - Correct
- ✅ `element_3` - Chart HTML present (3659 chars)
- ❌ `element_2` - HTML present (should be plain text)
- ✅ `slide_title` - Present
- ✅ `element_1` - Present (subtitle)

---

## 🎨 Analytics Service L02 Integration Guide

### What Analytics Service Should Return

**For L02 Layout**:
```python
{
  "content": {
    "element_3": generate_chart_html(),  # Full HTML with Chart.js canvas
    "element_2": generate_observations_text()  # PLAIN TEXT ONLY - no HTML tags
  },
  "metadata": {
    "analytics_type": "revenue_over_time",
    "chart_type": "line",
    "layout": "L02"
  }
}
```

### Example element_2 (Plain Text)
```
The line chart illustrates quarterly revenue growth, with figures increasing from $100,000 in Q1 to $180,000 in Q4, resulting in an average revenue of $138,750. This upward trend indicates robust business performance over the year. The consistent growth suggests effective strategies and market demand. To capitalize on this momentum, consider reinforcing successful initiatives and exploring new market opportunities.
```

**No**: `<div>`, `<h3>`, `<p>`, styling, or any HTML

---

## 🧪 Testing After Fix

### Step 1: Deploy Analytics Service Fix
Remove HTML wrapper from element_2 for L02 responses.

### Step 2: Create Test Presentation
```bash
python3 test_analytics_L02_layout.py
```

### Step 3: Verify Response Format
```bash
curl https://analytics-v30-production.up.railway.app/api/v1/analytics/L02/revenue_over_time \
  -X POST -H "Content-Type: application/json" \
  -d '{
    "presentation_id": "test",
    "slide_id": "test",
    "slide_number": 1,
    "narrative": "Test",
    "data": [{"label": "Q1", "value": 100}],
    "context": {"slide_title": "Test"}
  }' | python3 -m json.tool
```

**Verify**:
- `element_3` starts with `<div>` or `<canvas>` ✅
- `element_2` is **plain text** (no `<` or `>` characters) ✅

### Step 4: Open in Layout Builder
URL: `https://web-production-f0d13.up.railway.app/static/builder.html?id={new_id}`

**Expected**:
- Chart rendered on left (1260px wide)
- Observations text formatted on right (Layout Builder styling)
- No blank screen

---

## 📝 Communication Between Services

### Analytics Service → Layout Builder Contract

**L02 Layout Response Format**:
```json
{
  "content": {
    "element_3": "STRING - HTML allowed (chart)",
    "element_2": "STRING - PLAIN TEXT ONLY (observations)"
  }
}
```

**element_2 Constraints**:
- ❌ No HTML tags
- ❌ No inline styles
- ❌ No `<div>`, `<h3>`, `<p>` wrappers
- ✅ Plain text with natural paragraphs (line breaks via `\n` if needed)
- ✅ ~500 characters max (as currently implemented)

---

## 🔄 Alternative: Director Transformation

If Analytics Service can't be changed immediately, Director could strip HTML from element_2:

**Location**: `src/utils/content_transformer.py`

```python
import re

def strip_html_for_l02(element_2_html: str) -> str:
    """Strip HTML tags from element_2 for L02 layouts."""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', element_2_html)
    # Clean up extra whitespace
    text = ' '.join(text.split())
    return text

# In transform_slide()
if layout_id == "L02" and "element_2" in content:
    content["element_2"] = strip_html_for_l02(content["element_2"])
```

**But this is a workaround** - better to fix at the source (Analytics Service).

---

## 🎯 Summary

### Root Cause
**Type mismatch**: Analytics Service sends HTML for element_2, Layout Builder expects plain text.

### Quick Fix (Analytics Service)
Change L02 response generation to return plain text for element_2:
```python
# Before
element_2 = f"<div class='l02-observations-panel'>...{text}...</div>"

# After
element_2 = text  # Plain text only
```

### Impact
- ✅ element_3 (chart) already correct
- ✅ All other fields (slide_title, element_1) already correct
- ❌ element_2 needs plain text instead of HTML

### Files to Check

**Analytics Service v3**:
- `/agents/analytics_microservice_v3/` - L02 response generation
- Look for: `element_2` construction in L02 endpoint
- Change: Remove HTML wrapper, return plain text

**Layout Builder v7.5**:
- `/agents/layout_builder_main/v7.5-main/` - L02 rendering
- Verify: element_2 is rendered as text (not innerHTML)
- Expected: Layout Builder adds its own formatting

---

## 📞 Action Items

### For Analytics Team
- [ ] Update L02 endpoint to return plain text for element_2
- [ ] Remove `<div>`, `<h3>`, and styling from element_2
- [ ] Keep element_3 as full HTML (no changes needed)
- [ ] Test with Layout Builder after deployment

### For Layout Builder Team
- [ ] Verify L02 template is implemented in builder.html
- [ ] Confirm element_2 is rendered as text (not HTML)
- [ ] Check if element_2 has proper text formatting/styling
- [ ] Test with new Analytics Service response format

### For Director Team
- [x] Integration tests complete
- [x] Diagnostic documentation created
- [ ] Add HTML stripping as temporary workaround (optional)
- [ ] Retest after Analytics/Layout Builder fixes deployed

---

**Document Created**: November 16, 2025
**Test Scripts**: `test_analytics_L02_layout.py`
**Test Presentation ID**: `2237cf7f-7ed5-4179-ae1a-69c930154a40`

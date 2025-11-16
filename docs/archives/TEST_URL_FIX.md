# Director Test File URL Fix

**Date**: November 16, 2025
**Issue**: Blank screen when opening L02 presentations
**Presentation ID**: dd6d8551-64b3-4c13-91ed-f339667e387a

---

## Problem Identified

The test file `test_analytics_L02_layout.py` opens the wrong URL, causing a 404 error and blank screen.

### Current Code (Line 110-123)

```python
# Step 5: Open both viewer endpoints
preview_url = f"{LAYOUT_BUILDER_URL}/static/builder.html?id={pres_id}"  # ❌ WRONG - 404 Error
viewer_url = f"{LAYOUT_BUILDER_URL}/p/{pres_id}"  # ✅ CORRECT

print(f"\n🔗 Builder URL:")
print(f"   {preview_url}")
print(f"\n🔗 Viewer URL:")
print(f"   {viewer_url}")

import subprocess
subprocess.run(["open", preview_url])  # ❌ Opens wrong URL causing blank screen
```

### Railway Logs Showing 404

```
INFO:     100.64.0.3:22700 - "GET /static/builder.html?id=dd6d8551-64b3-4c13-91ed-f339667e387a HTTP/1.1" 404 Not Found
```

---

## Root Cause

**Line 123**: `subprocess.run(["open", preview_url])`

This opens `/static/builder.html?id={pres_id}` which doesn't exist on Railway deployment. The Layout Builder doesn't have a `/static/builder.html` endpoint.

---

## Solution

Change line 123 to open the correct viewer URL:

```python
# Step 5: Open the viewer endpoint
viewer_url = f"{LAYOUT_BUILDER_URL}/p/{pres_id}"

print(f"\n{'=' * 70}")
print(f"🎉 PRESENTATION CREATED")
print(f"{'=' * 70}")
print(f"\n🔗 Viewer URL:")
print(f"   {viewer_url}")
print(f"\n📊 Using layout: 'L02' (with HTML support)")

import subprocess
subprocess.run(["open", viewer_url])  # ✅ Opens correct URL
```

---

## Verification Results

### Railway Deployment Status ✅

**Checked**: https://web-production-f0d13.up.railway.app/p/dd6d8551-64b3-4c13-91ed-f339667e387a

✅ Railway has v7.5.1 deployed with L02 HTML support
✅ L02.js includes HTML auto-detection function
✅ Presentation data correctly saved with HTML in element_2 and element_3
✅ Correct viewer URL `/p/{id}` renders successfully

### Presentation Data Verification

```json
{
  "layout": "L02",
  "content": {
    "element_2": "<div class=\"l02-observations-panel\" style=\"width: 540px; height: 720px; padding: 40px 32px; background: #f8f9fa; overflow-y: auto; box-sizing: border-box;\">...</div>",
    "element_3": "<div class=\"l02-chart-container\" style=\"width: 1260px; height: 720px; position: relative; background: white; padding: 20px;\">...</div>"
  }
}
```

**Lengths**:
- element_2: 998 characters (HTML observations panel)
- element_3: 3659 characters (Chart.js code with canvas)

---

## Expected Result After Fix

When the test opens the correct URL (`/p/{pres_id}`), you should see:

1. **Left side (1260×720px)**: Chart.js line chart showing Quarterly Revenue Growth
2. **Right side (540×720px)**: Formatted observations panel with "Key Insights" heading
3. **No blank screens**: HTML content renders properly
4. **Proper styling**: Background colors, typography, and layout as designed

---

## URLs Reference

### Wrong URL (404 Error)
```
https://web-production-f0d13.up.railway.app/static/builder.html?id=dd6d8551-64b3-4c13-91ed-f339667e387a
```
**Result**: 404 Not Found → Blank screen

### Correct URL (Works)
```
https://web-production-f0d13.up.railway.app/p/dd6d8551-64b3-4c13-91ed-f339667e387a
```
**Result**: Presentation renders with HTML charts and observations

---

## Testing

After applying the fix, test with:

```bash
cd /Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/director_agent/v3.4
python test_analytics_L02_layout.py
```

**Expected**: Browser opens to presentation showing chart on left, observations on right, no blank screens.

---

## Additional Context

### Layout Builder v7.5.1 Changes

The Layout Builder has been updated to support HTML in L02's element_2 and element_3:

1. **HTML Auto-Detection**: Checks if content contains `<` character
2. **Conditional Rendering**: HTML renders as-is, plain text gets default styling
3. **Grid Dimensions**: element_3 (1260×720px), element_2 (540×720px)
4. **Overflow Handling**: Charts use `overflow: hidden`, text uses `overflow: auto`

### Director Integration

Director should continue to:
- Pass through Analytics HTML without modification
- Send element_2 and element_3 exactly as received from Analytics Service
- Add required metadata fields (slide_title, element_1, presentation_name, company_logo)

**No changes needed in Director's content transformation** - just fix the test file URL.

---

## Summary

**The presentation is working correctly!** The only issue is the test file opening the wrong URL.

**Fix**: Change line 123 in `test_analytics_L02_layout.py` from:
```python
subprocess.run(["open", preview_url])  # Wrong
```

To:
```python
subprocess.run(["open", viewer_url])  # Correct
```

**Status**: Railway deployment verified, L02 HTML support confirmed, presentation data correct. Ready to test with fixed URL.

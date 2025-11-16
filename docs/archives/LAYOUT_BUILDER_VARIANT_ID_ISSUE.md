# Layout Builder v7.5 - variant_id Not Persisting Issue

**Date**: November 16, 2025
**Issue**: Blank screen when rendering L02 analytics slides
**Root Cause**: Layout Builder API strips `variant_id` field when saving presentations

---

## 🐛 Problem Description

When sending analytics slides with `variant_id: "L02"` to Layout Builder, the field is not saved to the database. This causes the frontend (builder.html) to not know which L25 variant template to use, resulting in a blank screen.

---

## 📊 Diagnosis Results

### Test Case
- **Analytics Type**: revenue_over_time
- **Layout**: L25
- **Variant**: L02
- **Presentation ID**: `8ad5ed63-1368-47f0-a413-4280a2294058`

### Request Payload (Sent to Layout Builder)
```json
{
  "title": "Analytics Demo - Revenue Performance",
  "slides": [
    {
      "layout": "L25",
      "variant_id": "L02",  // ← SENT
      "content": {
        "slide_title": "Quarterly Revenue Performance",
        "element_1": "FY 2024 Strong Growth",
        "element_3": "<div>...Chart HTML...</div>",
        "element_2": "<div>...Observations HTML...</div>",
        "presentation_name": "Analytics Demo"
      }
    }
  ]
}
```

### Response from Database (GET /api/presentations/{id})
```json
{
  "title": "Analytics Demo - Revenue Performance",
  "slides": [
    {
      "layout": "L25",
      // variant_id: "L02" ← MISSING!
      "content": {
        "slide_title": "Quarterly Revenue Performance",
        "element_1": "FY 2024 Strong Growth",
        "element_3": "<div>...Chart HTML...</div>",
        "element_2": "<div>...Observations HTML...</div>",
        "presentation_name": "Analytics Demo"
      }
    }
  ],
  "id": "8ad5ed63-1368-47f0-a413-4280a2294058",
  "created_at": "2025-11-16T19:26:39.123456"
}
```

### Fields Comparison

| Field | Sent to API | Saved in DB | Status |
|-------|-------------|-------------|--------|
| `layout` | ✅ "L25" | ✅ "L25" | Preserved |
| `variant_id` | ✅ "L02" | ❌ Missing | **DROPPED** |
| `content.slide_title` | ✅ | ✅ | Preserved |
| `content.element_1` | ✅ | ✅ | Preserved |
| `content.element_3` | ✅ | ✅ | Preserved |
| `content.element_2` | ✅ | ✅ | Preserved |

---

## 🔍 Impact Analysis

### Frontend Rendering
The frontend `builder.html` likely has logic like:
```javascript
if (slide.layout === "L25" && slide.variant_id === "L02") {
  renderL02Layout(slide.content);
} else if (slide.layout === "L25") {
  renderDefaultL25Layout(slide.content);
}
```

Without `variant_id`, it can't determine which L25 variant to use → **blank screen**.

### Analytics Integration
- ✅ Analytics Service generating charts correctly
- ✅ 2-field response (element_3 + element_2) working
- ✅ Chart HTML and observations HTML being saved
- ❌ **Frontend can't render because variant_id is missing**

---

## 🔧 Required Fix

### Location
Layout Builder backend (FastAPI/Python)
- File: Likely `main.py` or `models.py` in Layout Builder v7.5
- Endpoint: `POST /api/presentations`

### Current Behavior (Assumed)
```python
class Slide(BaseModel):
    layout: str
    content: Dict[str, Any]
    # variant_id field is NOT defined → gets stripped
```

### Required Change
```python
class Slide(BaseModel):
    layout: str
    variant_id: Optional[str] = None  # ADD THIS
    content: Dict[str, Any]
```

### Database Schema
Ensure database model also includes `variant_id`:
```python
# In database model
class PresentationSlide:
    layout: str
    variant_id: Optional[str]  # ADD THIS
    content: JSON
```

---

## ✅ Temporary Workarounds

While waiting for the backend fix, you could try:

### Option 1: Put variant in content
```json
{
  "layout": "L25",
  "content": {
    "_variant": "L02",  // Store in content as workaround
    "slide_title": "...",
    ...
  }
}
```

### Option 2: Use layout naming convention
```json
{
  "layout": "L25_L02",  // Encode variant in layout name
  "content": {...}
}
```

### Option 3: Create separate layout entries
Instead of `L25` with variants, use:
- `L25_RICH_CONTENT` (default)
- `L25_L02_ANALYTICS` (L02 variant)
- `L25_L03_GRID` (L03 variant)

---

## 🧪 Test URLs

**Current (broken) presentations**:
- https://web-production-f0d13.up.railway.app/static/builder.html?id=8ad5ed63-1368-47f0-a413-4280a2294058
- https://web-production-f0d13.up.railway.app/static/builder.html?id=3ae42050-a788-432b-b4a9-18c17d2f4a87

**Alternative viewer endpoint** (may work):
- https://web-production-f0d13.up.railway.app/p/8ad5ed63-1368-47f0-a413-4280a2294058

---

## 📝 Verification Steps (After Fix)

1. Deploy Layout Builder with `variant_id` field added to model
2. Create new presentation with `variant_id: "L02"`
3. Verify field is saved:
   ```bash
   curl https://web-production-f0d13.up.railway.app/api/presentations/{id} | grep variant_id
   ```
4. Open in builder.html and verify rendering works
5. Test all L25 variants:
   - No variant (default rich_content)
   - L02 (analytics: chart + observations)
   - L03 (grid layouts)

---

## 🎯 Expected Behavior After Fix

### Request
```json
POST /api/presentations
{
  "slides": [
    {
      "layout": "L25",
      "variant_id": "L02",  // ← Sent
      "content": {...}
    }
  ]
}
```

### Response (GET /api/presentations/{id})
```json
{
  "slides": [
    {
      "layout": "L25",
      "variant_id": "L02",  // ← Preserved!
      "content": {...}
    }
  ]
}
```

### Rendering
```
builder.html loads →
sees variant_id: "L02" →
renders L02 template →
displays chart on left + observations on right
```

---

## 🔗 Related Files

**Director Agent**:
- `src/clients/analytics_client.py` - ✅ Working
- `src/utils/service_router_v1_2.py` - ✅ Sending variant_id correctly
- `src/utils/content_transformer.py` - ✅ Creating proper L02 structure

**Layout Builder** (needs fix):
- Backend API model - ❌ Missing variant_id field
- Database model - ❌ Not storing variant_id
- Frontend builder.html - ⚠️ Expects variant_id but doesn't receive it

---

## 📊 Summary

| Component | Status | Issue |
|-----------|--------|-------|
| Analytics Service v3 | ✅ Working | None |
| Analytics Client | ✅ Working | None |
| L02 Assembly | ✅ Working | None |
| Layout Builder API | ❌ **Broken** | **Drops variant_id field** |
| Layout Builder DB | ❌ **Broken** | **Doesn't store variant_id** |
| Frontend Rendering | ❌ **Blocked** | **Can't render without variant_id** |

**Action Required**: Fix Layout Builder backend to preserve `variant_id` field in slide model and database schema.

---

**Diagnosed by**: Director Agent v3.4 Analytics Integration Test
**Test Script**: `test_analytics_fixed.py`
**Date**: November 16, 2025

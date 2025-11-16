# Railway Diagnostic Logging Fix

**Date**: November 10, 2025
**Commit**: cb17d0e
**Status**: ✅ **DEPLOYED - Railway rebuilding**

---

## 🐛 Issue Discovered

Railway production logs showed the deployed code was **missing our diagnostic lines** (lines 189-206 in streamlined_packager.py), suggesting an outdated deployment. Additionally, the WebSocket send diagnostic was using the wrong payload key.

### Production Log Evidence
**What Railway showed**:
```
📦 PACKAGING STAGE 4 SLIDE_UPDATE
   strawman type: <class 'src.models.agents.PresentationStrawman'>
   strawman.main_title: The Golden Standard...
   Total slides: 7
```

**What SHOULD have appeared** (our added lines 189-206):
```
   strawman class name: PresentationStrawman
   hasattr preview_url: True
   preview_url value: https://...
   hasattr preview_presentation_id: True          ← MISSING
   preview_presentation_id value: 92dd6e91-...    ← MISSING
   ✅ Preview URL will be sent to frontend
```

---

## 🔍 Root Causes Found

### 1. Railway Hadn't Redeployed
- Commit c56851c was on GitHub but Railway hadn't rebuilt
- Old code was still running in production
- Missing lines 189-206 from streamlined_packager.py

### 2. WebSocket Diagnostic Using Wrong Key
**File**: `src/handlers/websocket.py`
**Lines**: 100, 104, 109, 114-116

**Bug**: Diagnostic logging was accessing `message_data.get('data')`
**Issue**: Streamlined protocol uses `'payload'` key, not `'data'` key
**Result**: Logs showed "N/A" and empty metadata even when data was present

```python
# WRONG (old code):
print(f"   Session: {message_data.get('data', {}).get('session_id', 'N/A')}")
metadata = message_data.get('data', {}).get('metadata', {})

# CORRECT (fixed):
print(f"   Session: {message_data.get('payload', {}).get('session_id', 'N/A')}")
metadata = message_data.get('payload', {}).get('metadata', {})
```

---

## ✅ Fixes Applied

### Fix 1: Added `preview_presentation_id` to WebSocket Diagnostic
**File**: `src/handlers/websocket.py` (line 107)

```python
# Special logging for slide_update messages
if message_data.get('type') == 'slide_update':
    metadata = message_data.get('payload', {}).get('metadata', {})
    print(f"   📋 Slide Update Metadata:", flush=True)
    print(f"      - preview_url: {metadata.get('preview_url')}", flush=True)
    print(f"      - preview_presentation_id: {metadata.get('preview_presentation_id')}", flush=True)  # ← ADDED
    print(f"      - main_title: {metadata.get('main_title')}", flush=True)
    print(f"      - slide_count: {len(message_data.get('payload', {}).get('slides', []))}", flush=True)
```

### Fix 2: Corrected Payload Key Access
**File**: `src/handlers/websocket.py` (lines 100, 104, 109, 114-116)

Changed all instances of:
- `message_data.get('data')` → `message_data.get('payload')`

This affects:
- Session ID logging (line 100)
- slide_update metadata extraction (line 104)
- Slide count logging (line 109)
- presentation_url logging (lines 114-116)

### Fix 3: Forced Railway Redeploy
**Action**: Pushed commit cb17d0e to feature/variant-diversity-enhancement
**Result**: Railway auto-detected change and triggered rebuild
**Expected**: New deployment with all fixes in ~2-3 minutes

---

## 📊 Expected Output After Fix

### Stage 4 - Packaging Logs
```
================================================================================
📦 PACKAGING STAGE 4 SLIDE_UPDATE
   strawman type: <class 'src.models.agents.PresentationStrawman'>
   strawman class name: PresentationStrawman                               ← NOW VISIBLE
   hasattr preview_url: True                                               ← NOW VISIBLE
   preview_url value: https://web-production-f0d13.up.railway.app/p/...   ← NOW VISIBLE
   hasattr preview_presentation_id: True                                   ← NOW VISIBLE
   preview_presentation_id value: 92dd6e91-e9e7-4a72-96f1-4b0ab76206b4   ← NOW VISIBLE
   ✅ Preview URL will be sent to frontend                                ← NOW VISIBLE
   strawman.main_title: The Golden Standard...
   Total slides: 7
================================================================================
```

### WebSocket Send Logs
```
================================================================================
📤 SENDING MESSAGE 1/3
   Type: slide_update
   Session: f988b3f3-3840-4512-9cfc-856ef4b04a9b                          ← NOW SHOWS REAL ID
   📋 Slide Update Metadata:
      - preview_url: https://web-production-f0d13.up.railway.app/p/92dd6e91-e9e7-4a72-96f1-4b0ab76206b4
      - preview_presentation_id: 92dd6e91-e9e7-4a72-96f1-4b0ab76206b4    ← NEW FIELD
      - main_title: The Golden Standard: Unpacking Honey's Food Science Potential
      - slide_count: 7
================================================================================
```

---

## 🧪 Verification Steps

### 1. Wait for Railway Deployment
- Go to Railway dashboard → Deployments
- Wait for build to complete (~2-3 minutes)
- Status should change to "Active"

### 2. Generate Test Presentation
- Connect to frontend
- Create a new presentation
- Proceed through to Stage 4 (strawman generation)

### 3. Check Railway Logs
Look for the following markers:

**✅ Packager Diagnostic** (should show ALL lines now):
```
📦 PACKAGING STAGE 4 SLIDE_UPDATE
   ...
   preview_presentation_id value: <UUID>
```

**✅ WebSocket Send Diagnostic** (should show preview_presentation_id):
```
📤 SENDING MESSAGE
   📋 Slide Update Metadata:
      - preview_presentation_id: <UUID>
```

### 4. Check Frontend Console
Open browser DevTools and verify:
```javascript
// Should now log:
"✅ Found preview_presentation_id: 92dd6e91-e9e7-4a72-96f1-4b0ab76206b4"
"✅ Download buttons enabled"
```

---

## 🎯 Success Criteria

- [ ] Railway deployment completes successfully
- [ ] Packager logs show lines 189-206 (including preview_presentation_id value)
- [ ] WebSocket send logs show preview_presentation_id in metadata
- [ ] Frontend console shows "Found preview_presentation_id"
- [ ] Download buttons are enabled in Stage 4

---

## 🔧 Troubleshooting

### If Logs Still Missing Lines 189-206:
**Problem**: Packager diagnostic output not appearing
**Check**:
1. Verify Railway is deploying from feature/variant-diversity-enhancement branch
2. Check Railway environment variables (should auto-detect branch)
3. Manually trigger redeploy if needed

### If preview_presentation_id is Null:
**Problem**: Field is in message but value is null
**Possible Causes**:
1. Deck-builder API failed (check for error logs)
2. DECK_BUILDER_ENABLED=false
3. api_response['id'] missing from deck-builder response

**Check**:
```
✅ Deck-builder API call successful
   Presentation ID: <UUID>
```

### If Frontend Still Doesn't Receive Field:
**Problem**: Backend sends it but frontend doesn't parse it
**Check**:
1. Browser DevTools → Network → WS tab
2. Find slide_update message
3. Inspect raw JSON payload
4. Verify `payload.metadata.preview_presentation_id` exists

---

## 📝 Commits

### Commit 1: c56851c (Previous)
```
fix: Add preview_presentation_id to Stage 4 slide_update messages
- Added field to SlideMetadata model
- Updated streamlined packager to extract and pass field
```

### Commit 2: cb17d0e (This Fix)
```
fix: Correct WebSocket diagnostic logging for streamlined protocol
- Changed payload key from 'data' to 'payload'
- Added preview_presentation_id to diagnostic output
- Forces Railway redeploy with correct code
```

---

## 🚀 Next Steps

1. **Monitor Railway**: Watch deployment progress
2. **Test End-to-End**: Generate presentation and check logs
3. **Verify Frontend**: Confirm download buttons work
4. **Document Results**: Share final confirmation with frontend team

---

**Status**: 🟡 **AWAITING RAILWAY DEPLOYMENT**

Push successful at: 2025-11-10 22:40 UTC
Expected deployment completion: 2025-11-10 22:43 UTC

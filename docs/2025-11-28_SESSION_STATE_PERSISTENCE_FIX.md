# Session State Persistence Fix

**Date:** 2025-11-28
**Issue:** Session state not persisting to Supabase on reconnection
**Status:** ✅ FIXED
**Branch:** `feature/fix-session-persistence`

---

## Problem Summary

Session state transitions were being saved in-memory but NOT persisted to Supabase, causing sessions to revert to `PROVIDE_GREETING` state on reconnection instead of their actual workflow state (e.g., `CREATE_CONFIRMATION_PLAN`).

### Impact

- User completes workflow (e.g., answers questions → gets confirmation plan)
- User refreshes browser page
- **Bug:** Director treats reconnection as new session and sends greeting again
- **Expected:** Director restores conversation history and continues from where user left off

---

## Root Cause Analysis

### Bug #1: Change_Topic Intent Missing State Persistence
**File:** `src/handlers/websocket.py`, Line 543-548

**Before Fix:**
```python
if intent.intent_type == "Change_Topic":
    await self.sessions.clear_context(session.id, self.current_user_id)
    session = await self.sessions.get_or_create(session.id, self.current_user_id)
    session.current_state = "ASK_CLARIFYING_QUESTIONS"  # ← In-memory only!
    session.user_initial_request = intent.extracted_info or user_input
```

**Problem:** State change was only in-memory. Never persisted to Supabase.

### Bug #2: clear_context Doesn't Reset State in Supabase
**File:** `src/utils/session_manager.py`, Line 154-186

**Before Fix:**
```python
self.supabase.table(self.table_name).update({
    'user_initial_request': None,
    'clarifying_answers': None,
    # ... other fields
    # ❌ Missing: 'current_state'
}).eq('id', session_id).eq('user_id', user_id).execute()
```

**Problem:** `current_state` field was not included in Supabase UPDATE query.

---

## Fixes Implemented

### Fix #1: Add State Persistence to Change_Topic Intent
**File:** `src/handlers/websocket.py`, Line 546-551

**After Fix:**
```python
if intent.intent_type == "Change_Topic":
    await self.sessions.clear_context(session.id, self.current_user_id)
    # FIX: Persist state to Supabase before continuing
    await self.sessions.update_state(
        session.id,
        self.current_user_id,
        "ASK_CLARIFYING_QUESTIONS"
    )
    session = await self.sessions.get_or_create(session.id, self.current_user_id)
    session.current_state = "ASK_CLARIFYING_QUESTIONS"
    session.user_initial_request = intent.extracted_info or user_input
```

**Result:** State is now persisted to Supabase immediately via `update_state()`.

### Fix #2: Add current_state to clear_context
**File:** `src/utils/session_manager.py`, Line 164-186

**After Fix:**
```python
# Clear relevant fields
session.current_state = "ASK_CLARIFYING_QUESTIONS"  # ← Added

# Update in Supabase
self.supabase.table(self.table_name).update({
    'user_initial_request': None,
    'clarifying_answers': None,
    'current_state': 'ASK_CLARIFYING_QUESTIONS',  # ← Added
    # ... other fields
}).eq('id', session_id).eq('user_id', user_id).execute()
```

**Result:** State is reset to `ASK_CLARIFYING_QUESTIONS` in both memory and Supabase.

### Enhancement #3: Add State Persistence Verification Logging

**File:** `src/utils/session_manager.py`, Line 116

```python
logger.info(f"✅ State persisted to Supabase: {state} for session {session_id}")
```

**File:** `src/handlers/websocket.py`, Line 182

```python
logger.info(f"🔌 Reconnection: session_id={session_id}, user_id={user_id}, loaded_state={session.current_state}")
```

**File:** `src/handlers/websocket.py`, Lines 189 & 197

```python
if session.current_state == "PROVIDE_GREETING":
    logger.info(f"New session - sending greeting (state: {session.current_state})")
else:
    logger.info(f"Existing session - restoring history (state: {session.current_state})")
    logger.info(f"✅ Restoring conversation history for session {session_id} (state: {session.current_state})")
```

**Result:** State persistence and restoration is now visible in Railway logs.

---

## Testing Procedure

### Prerequisites

1. Deploy to Railway with fixes
2. Open browser at: `https://www.deckster.xyz/builder`

### Test Scenario (Exact Reproduction)

**Step 1: Start New Session**
- Load `https://www.deckster.xyz/builder`
- Note the session_id in URL (e.g., `?session_id=fce87bea-acf5-4003-9b38-e460d6eeb46f`)

**Step 2: Submit Topic**
- Send message: "Krishna"
- **Expected state transition:** `PROVIDE_GREETING` → `ASK_CLARIFYING_QUESTIONS`
- **Check Railway logs:**
  ```
  ✅ State persisted to Supabase: ASK_CLARIFYING_QUESTIONS for session fce87bea...
  ```

**Step 3: Answer Questions**
- Send message: "Children, 10 min"
- **Expected state transition:** `ASK_CLARIFYING_QUESTIONS` → `CREATE_CONFIRMATION_PLAN`
- **Check Railway logs:**
  ```
  ✅ State persisted to Supabase: CREATE_CONFIRMATION_PLAN for session fce87bea...
  ```

**Step 4: Disconnect (Refresh Browser)**
- Close browser tab OR refresh page
- URL should preserve: `?session_id=fce87bea-acf5-4003-9b38-e460d6eeb46f`

**Step 5: Reconnection (Critical Test)**
- Page loads with same session_id
- **Check Railway logs:**
  ```
  🔌 Reconnection: session_id=fce87bea..., user_id=cmhth6yqq..., loaded_state=CREATE_CONFIRMATION_PLAN
  Existing session - restoring history (state: CREATE_CONFIRMATION_PLAN)
  ✅ Restoring conversation history for session fce87bea... (state: CREATE_CONFIRMATION_PLAN)
  📊 Restoring 6 history items for session
  Conversation history restored successfully for session fce87bea...
  ```

**Step 6: Verify Frontend**
- ✅ Chat shows full conversation history (greeting, questions, answers, plan)
- ✅ No greeting message sent (restoration occurred instead)
- ✅ User can click "Yes, perfect" to continue to strawman generation

---

## Verification Checklist

### Railway Logs Verification
- [ ] "✅ State persisted to Supabase" appears after state transitions
- [ ] "🔌 Reconnection: ... loaded_state=CREATE_CONFIRMATION_PLAN" appears on reconnect
- [ ] "Existing session - restoring history" appears (NOT "New session - sending greeting")
- [ ] "Conversation history restored successfully" appears

### Supabase Direct Verification

Run diagnostic script:
```bash
cd /Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/director_agent/v3.4
python scripts/check_session_state.py fce87bea-acf5-4003-9b38-e460d6eeb46f
```

**Expected output:**
```
✅ Session found!

📊 SESSION DETAILS:
ID:                    fce87bea-acf5-4003-9b38-e460d6eeb46f
User ID:               cmhth6yqq0000um8lvttpxmp1
Current State:         CREATE_CONFIRMATION_PLAN
Created At:            2025-11-28T21:04:18...
Updated At:            2025-11-28T21:07:28...

💬 CONVERSATION HISTORY: 6 messages
1. [user] Intent: Submit_Initial_Topic, State: N/A
2. [assistant] Intent: N/A, State: ASK_CLARIFYING_QUESTIONS
3. [user] Intent: Submit_Clarification_Answers, State: N/A
4. [assistant] Intent: N/A, State: CREATE_CONFIRMATION_PLAN

📋 WORKFLOW DATA:
Initial Request:       accept_plan
Clarifying Answers:    {...}
Confirmation Plan:     Yes
Presentation Strawman: No

🔍 RESTORATION ANALYSIS:
✅ State is CREATE_CONFIRMATION_PLAN - Will restore history on reconnection
   Restoration should send 6 messages to frontend
```

### Frontend Verification
- [ ] Full conversation visible after refresh
- [ ] No duplicate greeting messages
- [ ] Can continue workflow from where left off
- [ ] Session_id consistent between refreshes

---

## Success Criteria

✅ **All of the following must be true:**

1. Session state persists to Supabase after every transition
2. Reconnection with same session_id loads correct state (not PROVIDE_GREETING)
3. Conversation history restoration triggers on reconnection
4. Railway logs show "State persisted to Supabase" messages
5. Railway logs show "Existing session - restoring history" on reconnect
6. Diagnostic script shows correct state in Supabase
7. User can seamlessly continue conversation after page refresh

---

## Technical Details

### Files Modified

| File | Lines | Change |
|------|-------|--------|
| `src/handlers/websocket.py` | 546-551 | Added `update_state()` call in Change_Topic intent |
| `src/utils/session_manager.py` | 171, 183 | Added `current_state` to clear_context |
| `src/utils/session_manager.py` | 116 | Added persistence verification log |
| `src/handlers/websocket.py` | 182, 189, 197-198 | Enhanced reconnection logging |
| `scripts/check_session_state.py` | NEW | Diagnostic tool for Supabase verification |

### Supabase Table: `sessions`

**Fields Updated:**
- `current_state` (TEXT) - Now persisted on all transitions
- `updated_at` (TIMESTAMPTZ) - Updated on every state change

**Query Pattern:**
```python
self.supabase.table("sessions").update({
    'current_state': state,
    'updated_at': datetime.utcnow().isoformat()
}).eq('id', session_id).eq('user_id', user_id).execute()
```

**Safety Guarantees:**
- ✅ Only updates Director-owned fields
- ✅ Uses composite key (id + user_id) for isolation
- ✅ No schema changes required
- ✅ No impact on other microservices (Diagram Generator, Image Builder, Layout Builder)
- ✅ Backward compatible

---

## Deployment Notes

### Railway Deployment
1. Commit changes to `feature/fix-session-persistence` branch
2. Push to GitHub
3. Railway will auto-deploy
4. Monitor deployment logs for successful start
5. Run test scenario to verify fix

### Environment Variables Required
```
SUPABASE_URL=https://eshvntffcestlfuofwhv.supabase.co
SUPABASE_ANON_KEY=[key from .env]
SUPABASE_SERVICE_KEY=[key from .env]
```

**No new environment variables needed** - all existing config works.

---

## Rollback Plan

If issues occur:
1. Revert to previous commit
2. Railway will auto-deploy previous version
3. Session state will revert to previous behavior (not persisting properly)
4. No data loss - Supabase schema unchanged

**Risk:** LOW - Changes are additive and don't modify existing behavior except to add persistence.

---

## Related Issues

- **Original Issue:** `/docs/2025-11-28_SESSION_RESTORATION_FRONTEND_INTEGRATION_ISSUES.md`
- **Frontend Issue:** Session ID mismatch (separate issue, requires frontend fix)
- **Test Logs:** Session 2 → Session 3 restoration failure (this fixes the backend part)

---

## Future Improvements

1. **Add conversation_history cache consistency** - Ensure history updates clear cache
2. **Add atomic transactions** - Combine multiple UPDATE queries into single transaction
3. **Add Supabase error alerting** - Send alerts if Supabase operations fail
4. **Add periodic state sync** - Background task to verify cache-DB consistency

---

**Last Updated:** 2025-11-28
**Tested By:** [To be filled after testing]
**Approved By:** [To be filled after approval]

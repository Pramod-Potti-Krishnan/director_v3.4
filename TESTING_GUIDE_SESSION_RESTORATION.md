# Testing Guide: Session History Restoration Feature

**Feature Branch:** `feature/session-history-restoration`
**Date:** 2025-11-27
**For:** Frontend Team Testing
**Related Issue:** `DIRECTOR_CONTEXT_RESTORATION_ISSUE.md`

---

## Overview

This feature fixes the conversation continuity issue where users reconnecting to existing sessions (browser refresh, loading from session history) would see empty chat and Director would re-ask clarifying questions.

### What Changed

**File Modified:** `src/handlers/websocket.py`

**Changes:**
1. Added `_restore_conversation_history()` method - reconstructs and sends all past messages
2. Added `_reconstruct_assistant_message()` helper - rebuilds messages by state
3. Modified `handle_connection()` - calls restoration for existing sessions (state != PROVIDE_GREETING)
4. Added `create_chat_message` import for user message reconstruction

---

## How It Works

### Before (Buggy Behavior ❌)
```
1. User progresses to strawman stage
2. User refreshes browser
3. Frontend reconnects with same session_id
4. Director loads session from Supabase
5. Director sends NOTHING (logs "no greeting needed")
6. Frontend shows empty conversation
7. User clicks button → Director re-asks clarifying questions
```

### After (Fixed Behavior ✅)
```
1. User progresses to strawman stage
2. User refreshes browser
3. Frontend reconnects with same session_id
4. Director loads session from Supabase
5. Director reconstructs conversation history:
   - Iterates through session.conversation_history
   - Rebuilds user messages as chat_message
   - Rebuilds assistant messages using streamlined_packager
   - Uses session.presentation_strawman (includes preview_url)
6. Director sends ALL reconstructed messages to frontend
7. Frontend displays full conversation
8. User clicks button → Director proceeds correctly (no re-asking)
```

---

## Testing Scenarios

### Test Case 1: Refresh at Greeting Stage (New Session)
**Expected:** No change from current behavior

**Steps:**
1. Open new session
2. See greeting message
3. Refresh browser
4. ✅ **Verify:** See greeting again (same as before)

### Test Case 2: Refresh After Providing Topic
**Expected:** See greeting + user's topic

**Steps:**
1. Create new session
2. Provide topic (e.g., "AI in Healthcare")
3. See clarifying questions
4. Refresh browser
5. ✅ **Verify:**
   - See greeting message
   - See your topic message
   - See clarifying questions
6. Answer questions
7. ✅ **Verify:** Director proceeds to plan (doesn't re-ask questions)

### Test Case 3: Refresh After Answering Questions
**Expected:** See full history including plan

**Steps:**
1. Create session, provide topic
2. Answer all clarifying questions
3. See confirmation plan
4. Refresh browser
5. ✅ **Verify:**
   - See greeting
   - See topic
   - See questions
   - See your answers
   - See plan with action buttons
6. Click "Accept" or "Modify"
7. ✅ **Verify:** Director proceeds appropriately

### Test Case 4: Refresh at Strawman Stage (CRITICAL TEST)
**Expected:** See full conversation + strawman preview in iframe

**Steps:**
1. Progress through full flow to strawman
2. Verify strawman preview loads in iframe
3. Note the preview URL
4. Refresh browser
5. ✅ **Verify:**
   - See complete conversation history (greeting → questions → answers → plan → strawman)
   - See strawman preview in iframe (same URL as before refresh)
   - See action buttons ("Looks perfect!", "Make changes")
6. Click "Looks perfect!"
7. ✅ **Verify:**
   - Director proceeds to final generation (Stage 6)
   - **Does NOT re-ask clarifying questions**
   - **Does NOT re-ask for topic**

### Test Case 5: Refresh After Final Generation
**Expected:** See full conversation + final presentation URL

**Steps:**
1. Complete full workflow to final presentation
2. Verify final deck loads in iframe
3. Refresh browser
4. ✅ **Verify:**
   - See complete conversation history
   - See final presentation in iframe
   - See "Your presentation is ready!" message

### Test Case 6: Refresh at Refinement Stage
**Expected:** See full history + refined strawman

**Steps:**
1. Progress to strawman
2. Click "Make changes"
3. Provide refinement feedback
4. See refined strawman
5. Refresh browser
6. ✅ **Verify:**
   - See full conversation including refinement request
   - See refined strawman in iframe
   - Can continue refining or accept

---

## Backend Logs to Watch

When reconnecting to an existing session, you should see these logs in Director:

```
INFO: Session abc-123 already in state: GENERATE_STRAWMAN, no greeting needed
INFO: Restoring conversation history for session abc-123 (state: GENERATE_STRAWMAN)
INFO: 📊 Restoring 8 history items for session abc-123
INFO: ✅ Sending 12 reconstructed messages to frontend
INFO: 📊 Restoration stats - Current state: GENERATE_STRAWMAN, Has strawman: True, Has final URL: False
INFO: Conversation history restored successfully for session abc-123
```

### Key Log Indicators

✅ **Success Indicators:**
- "Restoring X history items"
- "Sending Y reconstructed messages to frontend"
- "Conversation history restored successfully"

⚠️ **Warning Indicators (non-fatal):**
- "Invalid questions format in history[X]" - specific message reconstruction failed, others continue
- "No strawman in session for history[X]" - strawman not saved, but other messages work

❌ **Error Indicators (need investigation):**
- "Failed to restore conversation history" - restoration completely failed
- "Error reconstructing message at history[X]" - specific message failed with exception

---

## Frontend Verification Checklist

After reconnection, verify frontend receives messages:

- [ ] WebSocket connection successful
- [ ] Multiple messages received in batch
- [ ] Messages display in chronological order (user → assistant pairs)
- [ ] Chat shows full conversation (not empty)
- [ ] Strawman preview iframe loads (if applicable)
- [ ] Final presentation iframe loads (if applicable)
- [ ] Action buttons appear correctly
- [ ] Clicking buttons continues conversation (doesn't reset)

---

## Deployment Instructions

### For Railway Deployment

**Option A: Deploy Feature Branch Directly**
```bash
# In Railway dashboard:
1. Go to Director v3.4 service
2. Settings → Deploy → Branch
3. Change from "main" to "feature/session-history-restoration"
4. Trigger deployment
5. Wait for build + deploy
6. Test with frontend
```

**Option B: Merge to Main (After Testing)**
```bash
# After frontend confirms fix works:
1. git checkout main
2. git pull origin main
3. git merge feature/session-history-restoration
4. git push origin main
5. Railway auto-deploys main branch
```

### Environment Variables
No new environment variables required. Uses existing:
- `USE_STREAMLINED_PROTOCOL` (should be `true`)
- `STREAMLINED_PROTOCOL_PERCENTAGE` (should be `100`)
- `SUPABASE_URL`, `SUPABASE_ANON_KEY` (for session persistence)

---

## Troubleshooting

### Issue: Still seeing empty chat after refresh

**Diagnosis:**
1. Check Director logs - do you see restoration logs?
2. If NO logs → Branch not deployed, still using old code
3. If YES logs → Check frontend message handling

**Fix:** Verify correct branch is deployed on Railway

---

### Issue: Frontend receives messages but doesn't display

**Diagnosis:**
1. Check browser console for frontend errors
2. Verify message types are recognized: `chat_message`, `action_request`, `slide_update`
3. Check if messages are StreamlinedMessage format

**Fix:** Ensure frontend message handlers work for restored messages (should be same format as live messages)

---

### Issue: Preview URL not appearing in restored strawman

**Diagnosis:**
1. Check Director logs - does it say "Has strawman: True"?
2. Check Supabase - does `presentation_strawman` have `preview_url` field?
3. Check if `slide_update` message has `metadata.preview_url`

**Fix:**
- If strawman missing preview_url → Bug in original strawman generation, not restoration
- If strawman has URL but not sent → Check code at line 424 (`session.presentation_strawman`)

---

### Issue: Director re-asks questions despite restoration

**Diagnosis:**
1. Verify current_state is correct in session (should be GENERATE_STRAWMAN, not ASK_CLARIFYING_QUESTIONS)
2. Check Intent Router logs - what intent was classified?
3. Verify button action is sent correctly (e.g., "accept_strawman")

**Fix:**
- If state is wrong → Session not saving correctly (separate issue)
- If intent wrong → Check frontend button value being sent
- If button action not mapped → Check websocket.py lines 324-330

---

## Success Criteria

Before merging to main, verify:

✅ **Functional:**
- [ ] All 6 test cases pass
- [ ] No empty conversations on refresh
- [ ] Preview URLs persist correctly
- [ ] Director doesn't re-ask questions
- [ ] Buttons work correctly after refresh

✅ **Technical:**
- [ ] No Python errors in Director logs
- [ ] No frontend console errors
- [ ] Messages arrive in < 2 seconds
- [ ] Works for all states (greeting through final generation)

✅ **User Experience:**
- [ ] Smooth reconnection (no flicker)
- [ ] Full context maintained
- [ ] Natural conversation continuation

---

## Rollback Plan

If critical issues found during testing:

```bash
# In Railway dashboard:
1. Settings → Deploy → Branch
2. Change back to "main"
3. Trigger deployment
4. Notify frontend team of rollback
```

**Rollback Time:** ~5 minutes

---

## Contact & Support

**For Questions:**
- Review commit: `15b9da5`
- Check detailed investigation in comprehensive report
- Reference frontend issue doc: `DIRECTOR_CONTEXT_RESTORATION_ISSUE.md`

**Testing Session ID:**
Use session `7304dad9-0492-41b4-a174-c421107b38dc` (Jimmy Kimmel presentation) mentioned in frontend docs for consistent testing.

---

## Next Steps After Testing

1. **Frontend team tests** all scenarios
2. **Report results** (pass/fail for each test case)
3. **If all pass:** Merge feature branch to main
4. **If issues found:** Document specific failures, we'll debug

**Expected Testing Time:** 30-60 minutes for comprehensive testing

---

**Status:** ✅ Ready for frontend team testing
**Branch:** `feature/session-history-restoration`
**GitHub PR:** https://github.com/Pramod-Potti-Krishnan/director_v3.4/pull/new/feature/session-history-restoration

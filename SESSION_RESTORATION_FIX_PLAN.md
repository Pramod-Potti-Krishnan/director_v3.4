# Session Restoration Fix Plan

**Date**: November 30, 2025
**Branch**: `feature/session-history-restoration`
**Frontend Requirements**: `DIRECTOR_REQUIREMENTS.md`
**Status**: ✅ **ALL FIXES IMPLEMENTED**

---

## Executive Summary

The frontend team has documented 4 issues with session message restoration. This plan addresses each issue with specific code changes, estimated effort, and testing criteria.

### Issues & Priorities

| # | Issue | Priority | Effort | Impact |
|---|-------|----------|--------|--------|
| 1 | Timestamps without `Z` suffix | HIGH | 30 min | Timezone bugs across regions |
| 2 | Role field `null` in messages | HIGH | 45 min | User/assistant message misclassification |
| 3 | Excessive history replay | MEDIUM | 2 hrs | Bandwidth waste, deduplication overhead |
| 4 | Message ordering inconsistency | LOW | 30 min | Minor UX issue |

**Total Estimated Time**: ~4 hours

---

## Issue Analysis

### Current Data Flow

```
Frontend (has cached messages)
    │
    ▼ WebSocket connect with session_id + user_id
Director receives connection
    │
    ├─ If state == PROVIDE_GREETING → Send greeting only
    │
    └─ If state != PROVIDE_GREETING → Call _restore_conversation_history()
       │
       ├─ Iterate ALL conversation_history items
       ├─ Reconstruct each message
       └─ Send ALL messages to frontend (11+ messages)
           │
           ▼
Frontend receives duplicate messages
    ├─ Must deduplicate by message_id
    ├─ Timestamps parsed as local time (no Z)
    ├─ Role field is null for non-chat messages
    └─ Message order may be inconsistent
```

### Root Causes

1. **Timestamps**: Python's `datetime.isoformat()` doesn't add `Z` for naive (UTC) datetimes
2. **Role field**: Only set on `chat_message` type, not on `slide_update`, `action_request`, etc.
3. **No sync protocol**: Director doesn't know what messages frontend already has
4. **Ordering**: Messages are sent in history array order, but history may not be strictly chronological

---

## Fix 1: Add `Z` Suffix to All Timestamps (HIGH)

### Problem
```python
# Current
timestamp = datetime.utcnow().isoformat()
# Output: "2025-11-29T23:56:34.316197"

# JavaScript parses this as LOCAL time, not UTC
new Date("2025-11-29T23:56:34.316197")  // Wrong timezone!
```

### Solution

**File**: `src/models/websocket_messages.py`

Option A: Custom JSON encoder (centralized fix)
```python
class BaseMessage(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }
```

Option B: Use timezone-aware datetimes (more robust)
```python
from datetime import datetime, timezone

class BaseMessage(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat().replace('+00:00', 'Z')
        }
```

**Recommended**: Option B (timezone-aware) for correctness.

### Files to Modify
- `src/models/websocket_messages.py` - BaseMessage class
- `src/handlers/websocket.py` - History storage timestamps
- `src/utils/session_manager.py` - Verify stored timestamps

### Testing
```bash
# Verify all outgoing timestamps end with Z
grep -r "timestamp" test_output/ | grep -v "Z"
```

---

## Fix 2: Ensure Role Field on ALL Message Types (HIGH)

### Problem
```json
{
  "type": "slide_update",
  "role": null,  // <-- Frontend can't classify this
  "payload": {...}
}
```

### Current State

From commit `9408b24`, we added `role` to:
- `create_chat_message()` - ✅ Has role parameter
- `StreamlinedMessagePackager` - ✅ Passes role='assistant' for chat messages

But NOT to:
- `create_action_request()` - ❌ No role parameter
- `create_slide_update()` - ❌ No role parameter
- `create_status_update()` - ❌ No role parameter
- `create_presentation_url()` - ❌ No role parameter

### Solution

**File**: `src/models/websocket_messages.py`

1. `BaseMessage` already has `role: Optional[...]` - ✅ Good
2. Add role parameter to ALL factory functions:

```python
def create_action_request(
    session_id: str,
    prompt_text: str,
    actions: List[Dict[str, Any]],
    message_id: Optional[str] = None,
    role: Literal["user", "assistant"] = "assistant"  # NEW
) -> ActionRequest:
    msg = ActionRequest(...)
    msg.role = role  # NEW
    return msg

def create_slide_update(
    session_id: str,
    operation: Literal["full_update", "partial_update"],
    metadata: Dict[str, Any],
    slides: List[Dict[str, Any]],
    message_id: Optional[str] = None,
    affected_slides: Optional[List[str]] = None,
    role: Literal["user", "assistant"] = "assistant"  # NEW
) -> SlideUpdate:
    msg = SlideUpdate(...)
    msg.role = role  # NEW
    return msg

# Similar for create_status_update() and create_presentation_url()
```

**File**: `src/utils/streamlined_packager.py`

No changes needed if factory functions default to `role="assistant"`.

**File**: `src/handlers/websocket.py`

In `_restore_conversation_history()`, user messages already get `role='user'`.
No additional changes needed.

### Testing
```python
# All messages should have role='user' or role='assistant', never null
for msg in messages:
    assert msg.get('role') in ['user', 'assistant'], f"Missing role: {msg}"
```

---

## Fix 3: Implement Sync Protocol (MEDIUM)

### Problem
```
Frontend already has 12 messages cached
Director sends 12 messages again on reconnect
= 24 messages, frontend must deduplicate
```

### Solution Options

#### Option A: Simple Flag (Recommended - Quick Win)

Frontend sends `skip_history: true` when it has cached messages.

**Protocol**:
```json
// Frontend → Director (on connect via query param or first message)
{
  "type": "sync_request",
  "skip_history": true,
  "last_message_id": "msg_f084296c",  // Optional: for delta sync
  "message_count": 12                   // Optional: sanity check
}

// Director response
{
  "type": "sync_response",
  "action": "skip_history"  // or "send_history" if mismatch
}
```

**Implementation**:

1. **Frontend change**: Send `skip_history` flag on connect
   - Add to WebSocket URL: `?session_id=...&skip_history=true`
   - OR send as first message after connect

2. **Director change**: Check flag in `handle_connection()`
```python
async def handle_connection(self, websocket: WebSocket, session_id: str, user_id: str):
    # ... existing code ...

    # Parse query params for sync flag
    query_params = dict(websocket.query_params)
    skip_history = query_params.get('skip_history', 'false').lower() == 'true'
    last_message_id = query_params.get('last_message_id')

    if session.current_state != "PROVIDE_GREETING":
        if skip_history:
            logger.info(f"Frontend requested skip_history for session {session_id}")
            # Send sync_response confirming skip
            await websocket.send_json({
                "type": "sync_response",
                "action": "skip_history"
            })
        else:
            # Full history restoration (existing behavior)
            await self._restore_conversation_history(websocket, session)
```

#### Option B: Delta Sync (More Complex)

Frontend sends `last_message_id`, Director only sends newer messages.

```python
async def _restore_conversation_history(self, websocket, session, last_message_id=None):
    # Find index of last_message_id in history
    start_idx = 0
    if last_message_id:
        for idx, item in enumerate(session.conversation_history):
            if item.get('message_id') == last_message_id:
                start_idx = idx + 1
                break

    # Only send messages after start_idx
    for idx, history_item in enumerate(session.conversation_history[start_idx:]):
        # ... reconstruct and send ...
```

#### Option C: Hash-Based Sync (Most Robust)

Both sides compute hash of message_ids, only resync if mismatch.

**Recommendation**: Start with **Option A** (simple flag) for immediate relief, then evolve to Option B if needed.

### Files to Modify
- `src/handlers/websocket.py` - Parse skip_history, implement conditional restore
- Frontend: `use-deckster-websocket-v2.ts` - Send skip_history when cache exists

### Testing
```
1. Load session with 12 messages in cache
2. Reconnect with skip_history=true
3. Verify Director sends sync_response, not 12 messages
4. Verify frontend state unchanged
```

---

## Fix 4: Ensure Chronological Message Ordering (LOW)

### Problem
Messages may arrive out of order due to:
1. History array not sorted by timestamp
2. Async message sending with `asyncio.sleep(0.1)` delays

### Solution

**File**: `src/handlers/websocket.py`

Sort history before restoration:
```python
async def _restore_conversation_history(self, websocket, session):
    # Sort history by timestamp before processing
    sorted_history = sorted(
        session.conversation_history,
        key=lambda x: x.get('timestamp', '1970-01-01T00:00:00Z')
    )

    for idx, history_item in enumerate(sorted_history):
        # ... existing reconstruction logic ...
```

### Testing
```python
# Verify messages are in chronological order
timestamps = [msg['timestamp'] for msg in received_messages]
assert timestamps == sorted(timestamps), "Messages not in chronological order"
```

---

## Implementation Order

### Phase 1: Quick Wins ✅ COMPLETE
1. ✅ Fix 1: Add Z suffix to timestamps
2. ✅ Fix 2: Ensure role on all messages
3. ✅ Fix 4: Sort history before restoration

### Phase 2: Performance Optimization ✅ COMPLETE
4. ✅ Fix 3: Implement sync protocol (skip_history flag)

### Phase 3: Future Enhancements (Optional)
- Delta sync based on last_message_id
- Message deduplication on Director side
- Compression for large histories

---

## Rollback Plan

If issues arise:
1. Revert to previous commit on branch
2. All changes are additive (no breaking changes to protocol)
3. Frontend workarounds remain in place as fallback

---

## Success Criteria

After deployment, verify:

- [ ] All timestamps end with `Z` suffix
- [ ] All message types have `role: "user"` or `role: "assistant"`
- [ ] Frontend displays user's first message correctly (e.g., "Stranger Things")
- [ ] Reconnecting with cache doesn't cause duplicate messages
- [ ] Messages display in correct chronological order
- [ ] No timezone offset bugs in different regions

---

## Contact

**Director Service**: This document
**Frontend Reference**: `DIRECTOR_REQUIREMENTS.md`
**Test Session**: `4ec948ca-a0fd-4635-bec2-d9f0cb8e6a12`

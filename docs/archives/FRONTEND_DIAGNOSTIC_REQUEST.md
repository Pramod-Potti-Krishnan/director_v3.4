# Request to Frontend Team: WebSocket Message Diagnostic

**Date**: November 10, 2025
**Issue**: `preview_presentation_id` field not reaching frontend
**Status**: Need raw WebSocket message data to diagnose

---

## 🎯 What We Need From Frontend Team

### Request: Capture Raw WebSocket Message

Please share the **complete, unmodified WebSocket message** that you receive during Stage 4 (strawman generation).

---

## 📋 How to Capture the Message

### Option 1: Browser DevTools (Recommended)

1. **Open Browser DevTools**:
   - Chrome/Edge: F12 or Right-click → Inspect
   - Safari: Develop → Show Web Inspector
   - Firefox: F12 or Tools → Browser Tools → Web Developer Tools

2. **Go to Network Tab**:
   - Click "Network" tab in DevTools
   - Filter by "WS" (WebSocket connections)

3. **Start Fresh Session**:
   - Refresh the page or start new presentation
   - Connect to Director WebSocket

4. **Find slide_update Message**:
   - Look for WebSocket messages after Stage 4 starts
   - Find message with `"type": "slide_update"`
   - This should contain the strawman data

5. **Copy Complete Message**:
   - Click on the message
   - Click "Messages" sub-tab
   - Find the `slide_update` message
   - **Copy the ENTIRE JSON**
   - Share it with us (can paste in a file or text)

### Option 2: Console Logging

Add this temporary code to your WebSocket handler:

```javascript
// In your WebSocket message handler (use-deckster-websocket-v2.ts or similar)
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  // ADD THIS TEMPORARY LOGGING:
  if (message.type === 'slide_update') {
    console.log('========================================');
    console.log('RAW SLIDE_UPDATE MESSAGE:');
    console.log(JSON.stringify(message, null, 2));
    console.log('========================================');

    // Also log the specific metadata:
    console.log('metadata:', message.payload?.metadata);
    console.log('preview_url:', message.payload?.metadata?.preview_url);
    console.log('preview_presentation_id:', message.payload?.metadata?.preview_presentation_id);
    console.log('========================================');
  }

  // ... rest of your handler code
};
```

Then:
1. Generate a presentation
2. Open Console tab in DevTools
3. Copy the logged JSON output
4. Share with us

---

## 🔍 What We're Looking For

### Scenario A: Field IS Present ✅
```json
{
  "type": "slide_update",
  "payload": {
    "metadata": {
      "main_title": "The Golden Harvest...",
      "preview_url": "https://web-production-f0d13.up.railway.app/p/abc-123",
      "preview_presentation_id": "abc-123"  // ← IF THIS IS HERE
    }
  }
}
```
**Conclusion**: Backend is working, frontend parsing issue.

### Scenario B: Field IS Present But Null
```json
{
  "preview_presentation_id": null  // ← IF THIS IS HERE BUT NULL
}
```
**Conclusion**: Backend passing field but value is None, deck-builder issue.

### Scenario C: Field Is Missing ❌
```json
{
  "type": "slide_update",
  "payload": {
    "metadata": {
      "main_title": "...",
      "preview_url": "..."
      // preview_presentation_id is COMPLETELY MISSING
    }
  }
}
```
**Conclusion**: Backend not including field, serialization issue.

---

## 📤 What to Share With Us

### Minimum Information Needed:
1. **Complete `slide_update` message JSON** (full structure)
2. **The metadata object specifically**
3. **Screenshot of Network tab** showing the WebSocket message (optional but helpful)

### Where to Share:
- Reply with the JSON in your next message
- Or paste into a `.json` file and share
- Or screenshot the DevTools showing the message

---

## 🎯 Additional Helpful Information (Optional)

If you can also share:

### 1. Your Parsing Code
Show us the code where you're trying to access `preview_presentation_id`:

```javascript
// Example of what you're currently doing:
const previewId = message.payload.metadata.preview_presentation_id;
```

### 2. All Paths You're Checking
```javascript
// Show us all the places you're looking:
const id1 = message.payload.preview_presentation_id;
const id2 = message.payload.metadata.preview_presentation_id;
const id3 = message.payload.strawman?.preview_presentation_id;
// etc.
```

### 3. TypeScript Interface (if applicable)
```typescript
interface SlideUpdateMessage {
  type: 'slide_update';
  payload: {
    metadata: {
      // What fields are defined here?
    }
  }
}
```

---

## 🔧 Expected Timeline

### After We Receive Your Data:
1. **5 minutes**: Analyze the raw message structure
2. **10 minutes**: Identify exact location of issue
3. **15 minutes**: Implement precise fix
4. **20 minutes**: Push fix to Railway
5. **25 minutes**: You can test again

---

## 📝 Example of Good Diagnostic Data

### Perfect Example:
```
From: Frontend Team
Date: 2025-11-10

Here's the complete slide_update message we received:

{
  "message_id": "msg_abc123",
  "session_id": "f988b3f3-3840-4512-9cfc-856ef4b04a9b",
  "timestamp": "2025-11-10T23:00:00Z",
  "type": "slide_update",
  "payload": {
    "operation": "full_update",
    "metadata": {
      "main_title": "The Golden Harvest: Understanding and Appreciating Honey",
      "overall_theme": "Educational and informative",
      "design_suggestions": "Clean, modern design...",
      "target_audience": "Beekeepers",
      "presentation_duration": 10,
      "preview_url": "https://web-production-f0d13.up.railway.app/p/f2bc6e24-bab0-493e-9909-b3c090176914"
      // NOTE: preview_presentation_id is MISSING here
    },
    "slides": [...]
  }
}

We're checking: message.payload.metadata.preview_presentation_id
Result: undefined
```

This tells us EXACTLY where the problem is! ✅

---

## ❓ Questions We Can Answer After Seeing Your Data

- Is the field in the message? (yes/no)
- Is it in the right location? (path check)
- Is it null or undefined? (value check)
- Is the structure different than expected? (schema check)

---

## 🚀 Why This Helps

Without seeing the actual message you're receiving, we're working blind. The diagnostic we added to Railway logs shows what we're **sending**, but we don't know what you're **receiving**.

Possible issues:
- ✅ Field is there, wrong path being checked
- ✅ Field is null, need fallback generation
- ✅ Field is missing, serialization bug
- ✅ Different message format, protocol mismatch

**Your data will tell us exactly which one it is!**

---

Thank you for your help! This will allow us to fix the issue quickly and definitively.

**Director Team**

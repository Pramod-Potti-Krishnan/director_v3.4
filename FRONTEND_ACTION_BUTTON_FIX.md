# 🚨 CRITICAL: Frontend Action Button Implementation

## Problem Identified
Backend sends `action_request` messages with buttons after strawman generation, but frontend is **not rendering the buttons**. This causes users to get stuck at Stage 4 unable to proceed to Stage 6 (content generation).

## Root Cause
Frontend may be:
1. Not handling `action_request` message type
2. Using wrong field (`.data` instead of `.payload`)
3. Sending button label instead of button value

---

## ✅ Required Implementation

### **1. Message Handler - Handle action_request Type**

```javascript
// In your WebSocket message handler
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  switch (message.type) {
    case "chat_message":
      handleChatMessage(message.payload);  // ← Use .payload
      break;

    case "action_request":  // ← CRITICAL: Must handle this!
      handleActionRequest(message.payload);  // ← Use .payload
      break;

    case "slide_update":
      handleSlideUpdate(message.payload);
      break;

    case "presentation_url":
      handlePresentationUrl(message.payload);
      break;

    case "status_update":
      handleStatusUpdate(message.payload);
      break;
  }
};
```

### **2. Action Request Handler - Render Buttons**

```javascript
function handleActionRequest(payload) {
  const { prompt_text, actions } = payload;  // ← Use payload, NOT data

  // Display prompt text
  appendToChatInterface({
    sender: "assistant",
    content: prompt_text
  });

  // Create button container
  const buttonContainer = document.createElement('div');
  buttonContainer.className = 'action-buttons';

  // Render each action as a button
  actions.forEach(action => {
    const button = document.createElement('button');
    button.textContent = action.label;  // Display text
    button.className = action.primary ? 'btn-primary' : 'btn-secondary';

    // ✅ CRITICAL: Send action.value, NOT action.label
    button.onclick = () => {
      // Remove buttons to prevent double-click
      buttonContainer.remove();

      // Send the VALUE field to backend
      ws.send(JSON.stringify({
        type: "user_message",
        data: { text: action.value }  // ← "accept_strawman", NOT "Looks perfect!"
      }));

      // Show what user selected in chat
      appendToChatInterface({
        sender: "user",
        content: action.label
      });
    };

    buttonContainer.appendChild(button);
  });

  // Add to chat interface
  document.getElementById('chat-messages').appendChild(buttonContainer);

  // Scroll to bottom
  document.getElementById('chat-messages').scrollTop =
    document.getElementById('chat-messages').scrollHeight;
}
```

### **3. Message Structure Verification**

**ALL messages from backend use `.payload`, NOT `.data`**:

```javascript
// ✅ CORRECT
message.payload.text
message.payload.actions
message.payload.url
message.payload.slides

// ❌ WRONG (will cause undefined errors)
message.data.text
message.data.actions
```

If you see errors like:
```
TypeError: undefined is not an object (evaluating 'message.data.text')
```

This means you're using `.data` instead of `.payload`.

### **4. Action Button Values Reference**

| Stage | Button Label | Button Value (what to send) |
|-------|-------------|---------------------------|
| Stage 3 (Plan) | "Yes, let's build it!" | `"accept_plan"` |
| Stage 3 (Plan) | "I'd like to make changes" | `"reject_plan"` |
| Stage 4 (Strawman) | "Looks perfect!" | `"accept_strawman"` ← **CRITICAL** |
| Stage 4 (Strawman) | "Make some changes" | `"request_refinement"` |
| Stage 5 (Refined) | "All done, looks great!" | `"accept_strawman"` |
| Stage 5 (Refined) | "More changes needed" | `"request_refinement"` |

---

## 🧪 Testing Checklist

After implementation, verify:

- [ ] Action buttons appear after plan (Stage 3)
- [ ] Action buttons appear after strawman (Stage 4) ← **MOST CRITICAL**
- [ ] Clicking "Looks perfect!" sends `"accept_strawman"` to backend
- [ ] Backend transitions to Stage 6 (CONTENT_GENERATION)
- [ ] Progress updates appear during content generation
- [ ] Final `presentation_url` received and displayed
- [ ] No undefined/null errors in console
- [ ] Buttons remove after click (no double-clicks)

---

## 🔍 Debugging Tips

### **Check if action_request is received:**
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('📨 Received:', message.type, message);

  if (message.type === "action_request") {
    console.log('🎯 ACTION REQUEST:', message.payload);
  }
  // ... rest of handler
};
```

### **Check what's being sent when button clicked:**
```javascript
button.onclick = () => {
  console.log('🔘 Button clicked:', action.label);
  console.log('📤 Sending value:', action.value);

  ws.send(JSON.stringify({
    type: "user_message",
    data: { text: action.value }
  }));
};
```

### **Common Issues:**

**Problem**: "Buttons don't appear"
- Check: Is `message.type === "action_request"` handler present?
- Check: Are you using `message.payload.actions` not `message.data.actions`?

**Problem**: "Buttons appear but clicking does nothing"
- Check: Are you sending `action.value` not `action.label`?
- Check: Is WebSocket still connected?

**Problem**: "Gets stuck after clicking button"
- Check Railway logs: Was "Accept_Strawman" intent classified?
- Check: Did state transition to CONTENT_GENERATION?

---

## 📄 Example Complete Implementation

```javascript
// Complete WebSocket integration
class DecksterClient {
  constructor(sessionId, userId) {
    this.ws = new WebSocket(
      `wss://directorv33-production.up.railway.app/ws?session_id=${sessionId}&user_id=${userId}`
    );

    this.ws.onmessage = (event) => this.handleMessage(event);
    this.ws.onopen = () => console.log('✅ Connected');
    this.ws.onerror = (err) => console.error('❌ Error:', err);
  }

  handleMessage(event) {
    const message = JSON.parse(event.data);

    switch (message.type) {
      case "chat_message":
        this.renderChatMessage(message.payload);
        break;

      case "action_request":
        this.renderActionButtons(message.payload);
        break;

      case "presentation_url":
        this.loadPresentation(message.payload);
        break;
    }
  }

  renderActionButtons(payload) {
    const { prompt_text, actions } = payload;

    // Show prompt
    this.addMessage('assistant', prompt_text);

    // Create buttons
    const container = document.createElement('div');
    container.className = 'action-buttons';

    actions.forEach(action => {
      const btn = document.createElement('button');
      btn.textContent = action.label;
      btn.className = action.primary ? 'btn-primary' : 'btn-secondary';

      btn.onclick = () => {
        container.remove();
        this.sendMessage(action.value);  // ← Send value!
        this.addMessage('user', action.label);
      };

      container.appendChild(btn);
    });

    document.getElementById('chat').appendChild(container);
  }

  sendMessage(text) {
    this.ws.send(JSON.stringify({
      type: "user_message",
      data: { text: text }
    }));
  }
}
```

---

**This is the CRITICAL fix for frontend integration. Without this, users cannot proceed from strawman to content generation!**

# 🔧 Director Agent v3.4 - Critical Fixes Implementation Checklist

## 📋 Overview

This checklist documents all fixes implemented to resolve frontend integration issues and Vertex AI rate limiting errors.

**Issues Addressed**:
1. ❌ **Vercel Production**: Strawman generates but no action buttons appear - users stuck at Stage 4
2. ❌ **Local Development**: 429 RESOURCE_EXHAUSTED errors from Vertex AI API
3. ❌ **Intent Classification**: Users forced to type free text instead of clicking buttons

**Root Causes Identified**:
- Deck-builder integration returning `{"type": "presentation_url"}` dict instead of strawman object
- Streamlined packager skipping action buttons when detecting presentation_url type
- No retry logic for Vertex AI 429 errors
- No rate limiting between slide processing calls

---

## ✅ Fix #1: Deck-Builder Integration & Action Buttons

### Goal
Ensure action buttons ALWAYS appear after strawman generation, even when deck-builder preview is enabled.

### Changes Made

#### 1.1 ✅ Modified `src/agents/director.py` (Lines 475-482)

**Before**:
```python
response = {
    "type": "presentation_url",  # ← PROBLEM: Wrong type
    "url": presentation_url,
    "presentation_id": api_response['id'],
    "slide_count": len(strawman.slides),
    "message": f"Your presentation is ready! View it at: {presentation_url}",
    "strawman": strawman
}
```

**After**:
```python
logger.info(f"✅ Preview created: {presentation_url}")

# v3.4 FIX: Store preview URL in strawman, but return strawman object
# This allows packager to send BOTH preview link AND action buttons
strawman.preview_url = presentation_url
strawman.preview_presentation_id = api_response['id']
response = strawman  # Return PresentationStrawman object, not dict
```

**Why This Works**:
- Returns `PresentationStrawman` object (correct type)
- Stores preview URL as attribute (accessible to packager)
- Packager no longer detects `presentation_url` type

---

#### 1.2 ✅ Modified `src/utils/streamlined_packager.py` (Lines 196-227)

**Before**:
```python
# v2.0: Check if this is a URL response from deck-builder
if isinstance(strawman, dict) and strawman.get("type") == "presentation_url":
    # Send ONLY presentation_url - SKIPS action buttons
    return [create_presentation_url(...)]

# Message 2: Action request
messages.append(create_action_request(...))
```

**After**:
```python
# v3.4 FIX: If preview URL exists, send it as a chat message before action buttons
if hasattr(strawman, 'preview_url') and strawman.preview_url:
    messages.append(
        create_chat_message(
            session_id=session_id,
            text=f"📊 **Preview your presentation:** [{strawman.preview_url}]({strawman.preview_url})\n\n"
                 f"Review the outline above. If you're happy with it, click 'Looks perfect!' to generate rich content for all slides.",
            format="markdown"
        )
    )

# Message 2: Action request (ALWAYS send this!)
messages.append(
    create_action_request(
        session_id=session_id,
        prompt_text="Your presentation is ready! What would you like to do?",
        actions=[
            {"label": "Looks perfect!", "value": "accept_strawman", "primary": True, "requires_input": False},
            {"label": "Make some changes", "value": "request_refinement", "primary": False, "requires_input": True}
        ]
    )
)
```

**Why This Works**:
- Checks for `preview_url` attribute (not dict type)
- Sends preview link as chat message
- ALWAYS sends action buttons afterward
- Maintains backward compatibility with v1.0 (no deck-builder)

---

#### 1.3 ✅ Created `FRONTEND_ACTION_BUTTON_FIX.md`

Complete frontend integration guide documenting:
- Correct `action_request` handler implementation
- Use of `message.payload` (not `message.data`)
- Sending `action.value` (not `action.label`)
- Button rendering and removal patterns

**Purpose**: Ensures frontend team implements buttons correctly.

---

## ✅ Fix #2: Vertex AI Retry Logic (429 Error Handling)

### Goal
Handle Vertex AI rate limit errors gracefully with exponential backoff retry logic.

### Changes Made

#### 2.1 ✅ Created `src/utils/vertex_retry.py` (NEW FILE)

**Full Implementation**:
```python
"""
Vertex AI Retry Utility with Exponential Backoff

Handles 429 RESOURCE_EXHAUSTED errors from Google Vertex AI
by implementing exponential backoff retry logic.
"""

import asyncio
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)
T = TypeVar('T')

async def call_with_retry(
    func: Callable[[], T],
    max_retries: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 60.0,
    operation_name: str = "Vertex AI call"
) -> T:
    """
    Call async function with exponential backoff retry for 429 errors.

    Args:
        func: Async function to call (should be a lambda or callable)
        max_retries: Maximum number of retry attempts (default: 5)
        base_delay: Base delay in seconds (default: 2.0)
        max_delay: Maximum delay in seconds (default: 60.0)
        operation_name: Description of operation for logging

    Returns:
        Result from successful function call

    Raises:
        Exception: If all retries exhausted or non-429 error occurs
    """
    last_exception = None

    for attempt in range(max_retries):
        try:
            result = await func()

            if attempt > 0:
                logger.info(f"✅ {operation_name} succeeded after {attempt} retries")

            return result

        except Exception as e:
            last_exception = e
            error_str = str(e)

            # Check if this is a 429 error
            is_429_error = (
                "429" in error_str or
                "RESOURCE_EXHAUSTED" in error_str or
                "Quota exceeded" in error_str or
                "rate limit" in error_str.lower()
            )

            if is_429_error and attempt < max_retries - 1:
                # Calculate exponential backoff delay
                delay = min(base_delay * (2 ** attempt), max_delay)

                logger.warning(
                    f"⚠️  {operation_name} hit rate limit (attempt {attempt + 1}/{max_retries}). "
                    f"Retrying in {delay:.1f}s..."
                )

                await asyncio.sleep(delay)
                continue

            # Either not a 429 error, or we've exhausted retries
            if is_429_error:
                logger.error(
                    f"❌ {operation_name} failed after {max_retries} retry attempts due to rate limiting"
                )
            else:
                logger.error(f"❌ {operation_name} failed with non-retryable error: {error_str}")

            raise

    raise last_exception or Exception(f"{operation_name} failed after {max_retries} attempts")
```

**Features**:
- Exponential backoff: 2s → 4s → 8s → 16s → 32s
- Max delay capped at 60 seconds
- Detects 429 errors by multiple patterns
- Detailed logging with retry counts
- Configurable via settings

---

#### 2.2 ✅ Modified `src/agents/director.py` - Added Import (Line 34)

```python
# v3.4: Vertex AI retry logic for 429 errors
from src.utils.vertex_retry import call_with_retry
```

---

#### 2.3 ✅ Modified `src/agents/director.py` - Wrapped Layout Selection (Lines 364-377)

**Before**:
```python
layout_selection = await self._select_layout_by_use_case(
    slide=slide,
    position=position,
    total_slides=total_slides
)
```

**After**:
```python
# AI-powered semantic layout selection with retry logic
from config.settings import get_settings
settings = get_settings()

layout_selection = await call_with_retry(
    lambda: self._select_layout_by_use_case(
        slide=slide,
        position=position,
        total_slides=total_slides
    ),
    max_retries=settings.MAX_VERTEX_RETRIES,
    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
    operation_name=f"Layout selection for slide {slide.slide_number}"
)
```

---

#### 2.4 ✅ Modified `src/agents/director.py` - Wrapped Title Generation (Lines 421-437)

**Before**:
```python
generated_title = await self._generate_slide_title(
    original_title=slide.title,
    narrative=slide.narrative or "",
    max_chars=50
)
```

**After**:
```python
generated_title = await call_with_retry(
    lambda: self._generate_slide_title(
        original_title=slide.title,
        narrative=slide.narrative or "",
        max_chars=50
    ),
    max_retries=settings.MAX_VERTEX_RETRIES,
    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
    operation_name=f"Title generation for slide {slide.slide_number}"
)
```

---

#### 2.5 ✅ Modified `src/agents/director.py` - Wrapped Subtitle Generation (Lines 439-456)

**Before**:
```python
generated_subtitle = await self._generate_slide_subtitle(
    narrative=slide.narrative or "",
    key_message=key_message,
    max_chars=90
)
```

**After**:
```python
generated_subtitle = await call_with_retry(
    lambda: self._generate_slide_subtitle(
        narrative=slide.narrative or "",
        key_message=key_message,
        max_chars=90
    ),
    max_retries=settings.MAX_VERTEX_RETRIES,
    base_delay=settings.VERTEX_RETRY_BASE_DELAY,
    operation_name=f"Subtitle generation for slide {slide.slide_number}"
)
```

---

## ✅ Fix #3: Rate Limiting Between Slides

### Goal
Add delays between slide processing to prevent hitting Vertex AI quota limits.

### Changes Made

#### 3.1 ✅ Modified `src/agents/director.py` (Lines 469-475)

**Added After Slide Processing**:
```python
# Track previous slide type for relationship analysis
previous_slide_type = slide_type_classification

# v3.4: Rate limiting - delay between slides to prevent 429 errors
# Skip delay for the last slide
if idx < total_slides - 1:
    import asyncio
    delay = settings.RATE_LIMIT_DELAY_SECONDS
    logger.debug(f"Rate limiting: waiting {delay}s before processing next slide")
    await asyncio.sleep(delay)
```

**Why This Works**:
- Adds 2-second delay between slides (configurable via `RATE_LIMIT_DELAY_SECONDS`)
- Prevents burst of API calls
- Skips delay for last slide (no need to wait after completion)
- Works in combination with retry logic

---

## ✅ Fix #4: Frontend Documentation

### Goal
Provide complete guide for frontend team to implement action buttons correctly.

### Changes Made

#### 4.1 ✅ Created `FRONTEND_ACTION_BUTTON_FIX.md`

**Sections Included**:
1. **Problem Identified**: Root cause analysis
2. **Required Implementation**: Step-by-step code examples
   - Message handler with `action_request` type
   - Action request handler rendering buttons
   - Using `message.payload` not `message.data`
   - Sending `action.value` not `action.label`
3. **Message Structure Verification**: Common errors and fixes
4. **Action Button Values Reference**: Complete mapping of stages to button values
5. **Testing Checklist**: Verification steps
6. **Debugging Tips**: Console logging and troubleshooting
7. **Example Complete Implementation**: Full working code

---

## 📊 Configuration Settings

All fixes use existing settings from `config/settings.py`:

```python
# v3.4: Rate Limiting & 429 Error Prevention (Stage 6)
# Prevents Vertex AI quota exhaustion by controlling API call frequency
RATE_LIMIT_DELAY_SECONDS: int = Field(2, env="RATE_LIMIT_DELAY_SECONDS")  # Delay between slides
MAX_VERTEX_RETRIES: int = Field(5, env="MAX_VERTEX_RETRIES")  # Max retry attempts for 429 errors
VERTEX_RETRY_BASE_DELAY: int = Field(2, env="VERTEX_RETRY_BASE_DELAY")  # Base delay (exponential backoff)
```

**Tuning Guidelines**:
- **RATE_LIMIT_DELAY_SECONDS**: Increase if still hitting 429 errors (try 3-5 seconds)
- **MAX_VERTEX_RETRIES**: Increase for more aggressive retry (but longer wait times)
- **VERTEX_RETRY_BASE_DELAY**: Decrease for faster retries (but higher quota usage)

---

## 🧪 Testing Checklist

### Local Testing (DECK_BUILDER_ENABLED=False)

- [ ] Start director agent: `python main.py`
- [ ] Connect frontend WebSocket client
- [ ] Complete flow: Greeting → Questions → Plan → Strawman
- [ ] **VERIFY**: Action buttons appear after strawman
- [ ] **VERIFY**: Clicking "Looks perfect!" sends `"accept_strawman"`
- [ ] **VERIFY**: No 429 errors in logs
- [ ] **VERIFY**: Delays between slides logged (e.g., "Rate limiting: waiting 2s...")
- [ ] **VERIFY**: Retry messages if any 429s occur (e.g., "⚠️ Layout selection hit rate limit")

### Local Testing (DECK_BUILDER_ENABLED=True)

- [ ] Update `.env`: `DECK_BUILDER_ENABLED=True`
- [ ] Start deck-builder service on port 8504
- [ ] Start director agent: `python main.py`
- [ ] Connect frontend WebSocket client
- [ ] Complete flow: Greeting → Questions → Plan → Strawman
- [ ] **VERIFY**: Preview URL chat message appears
- [ ] **VERIFY**: Action buttons appear AFTER preview link
- [ ] **VERIFY**: Clicking "Looks perfect!" sends `"accept_strawman"`
- [ ] **VERIFY**: Stage 6 content generation proceeds
- [ ] **VERIFY**: No 429 errors in logs

### Production Testing (Railway/Vercel)

- [ ] Deploy updated director agent to Railway
- [ ] Deploy updated frontend to Vercel
- [ ] Test complete E2E flow on production
- [ ] **VERIFY**: Action buttons appear consistently
- [ ] **VERIFY**: No users getting stuck at Stage 4
- [ ] Monitor Railway logs for:
  - [ ] No 429 errors
  - [ ] Successful retry messages (if any rate limits hit)
  - [ ] Rate limiting delays working
  - [ ] Preview URLs being sent before action buttons

---

## 🔍 Log Patterns to Watch For

### ✅ Success Patterns

```
✅ Preview created: https://deckbuilder.example.com/presentations/abc123
Rate limiting: waiting 2s before processing next slide
✅ Layout selection for slide 3 succeeded after 1 retries
✅ Assigned layouts, classifications, and content guidance to all 7 slides
```

### ⚠️ Warning Patterns (Expected, Handled)

```
⚠️  Title generation for slide 5 hit rate limit (attempt 1/5). Retrying in 2.0s...
⚠️  Subtitle generation for slide 6 hit rate limit (attempt 2/5). Retrying in 4.0s...
```

### ❌ Error Patterns (Should NOT Occur)

```
❌ Layout selection for slide 4 failed after 5 retry attempts due to rate limiting
Error: 429 RESOURCE_EXHAUSTED
TypeError: undefined is not an object (evaluating 'message.data.actions')
```

---

## 📁 Files Modified

### Backend Changes

1. **`src/agents/director.py`**
   - Line 34: Added retry utility import
   - Lines 364-377: Wrapped layout selection with retry
   - Lines 421-437: Wrapped title generation with retry
   - Lines 439-456: Wrapped subtitle generation with retry
   - Lines 469-475: Added rate limiting delay
   - Lines 475-482: Changed deck-builder response to return strawman object

2. **`src/utils/streamlined_packager.py`**
   - Lines 196-227: Added preview URL chat message before action buttons

3. **`src/utils/vertex_retry.py`** (NEW)
   - Complete exponential backoff retry utility

4. **`config/settings.py`** (Existing, No Changes)
   - Already had rate limiting settings

### Documentation Created

1. **`FRONTEND_ACTION_BUTTON_FIX.md`** (NEW)
   - Complete frontend integration guide

2. **`IMPLEMENTATION_CHECKLIST.md`** (THIS FILE)
   - Comprehensive implementation documentation

---

## 🚀 Deployment Steps

### 1. Backend Deployment (Railway)

```bash
# Verify all changes committed
git status

# Add all modified files
git add src/agents/director.py
git add src/utils/streamlined_packager.py
git add src/utils/vertex_retry.py
git add FRONTEND_ACTION_BUTTON_FIX.md
git add IMPLEMENTATION_CHECKLIST.md

# Commit with descriptive message
git commit -m "Fix: Resolve action button integration and 429 rate limiting errors

- Fix #1: Return strawman object instead of presentation_url dict
- Fix #1: Send preview URL as chat message before action buttons
- Fix #2: Add exponential backoff retry for Vertex AI 429 errors
- Fix #3: Add rate limiting delays between slide processing
- Fix #4: Add comprehensive frontend integration documentation

Resolves issues with:
- Action buttons not appearing on Vercel production
- 429 RESOURCE_EXHAUSTED errors on local development
- Intent classification ambiguity from manual text entry"

# Push to Railway
git push origin main
```

### 2. Frontend Deployment (Vercel)

Follow steps in `FRONTEND_ACTION_BUTTON_FIX.md`:

1. Implement `action_request` handler
2. Use `message.payload` for all message types
3. Send `action.value` when button clicked
4. Test locally before deploying
5. Deploy to Vercel

### 3. Verification

1. Monitor Railway logs for 15 minutes after deployment
2. Test 3-5 complete flows on production
3. Confirm no 429 errors
4. Confirm action buttons appearing consistently

---

## 🎯 Success Criteria

All of the following must be true:

- ✅ Action buttons appear after strawman generation (both local and production)
- ✅ Users can click "Looks perfect!" and proceed to Stage 6
- ✅ No 429 RESOURCE_EXHAUSTED errors in logs
- ✅ Preview URLs display when deck-builder enabled
- ✅ Preview URLs appear BEFORE action buttons (correct order)
- ✅ Rate limiting delays logged between slides
- ✅ Retry logic activates if 429 errors occur
- ✅ Frontend handles `action_request` messages correctly
- ✅ Frontend sends `action.value` not `action.label`
- ✅ No users manually typing "go ahead build it"

---

## 🔧 Rollback Plan

If issues occur after deployment:

### Quick Rollback (Director Agent)

```bash
# Revert to previous commit
git revert HEAD
git push origin main
```

### Gradual Rollback (Individual Fixes)

**Disable Fix #1 (Action Buttons)**:
```python
# In src/agents/director.py line 482
response = {
    "type": "presentation_url",
    "url": presentation_url,
    "presentation_id": api_response['id'],
    "slide_count": len(strawman.slides),
    "strawman": strawman
}
```

**Disable Fix #2 (Retry Logic)**:
```python
# Remove call_with_retry wrapper, call functions directly
layout_selection = await self._select_layout_by_use_case(...)
```

**Disable Fix #3 (Rate Limiting)**:
```python
# Comment out rate limiting delay
# if idx < total_slides - 1:
#     await asyncio.sleep(delay)
```

---

## 📞 Support

**Issues During Testing**:
- Check Railway logs: https://railway.app/project/[PROJECT_ID]/logs
- Check browser console for WebSocket messages
- Enable debug logging: Set `LOG_LEVEL=DEBUG` in `.env`

**Questions**:
- Review `FRONTEND_ACTION_BUTTON_FIX.md` for frontend integration
- Review `SERVICE_INTEGRATION_OVERVIEW.md` for architecture
- Check `config/settings.py` for configuration options

---

**Implementation Status**: ✅ ALL FIXES COMPLETE
**Ready for Testing**: ✅ YES
**Ready for Deployment**: ⏳ PENDING LOCAL TESTING

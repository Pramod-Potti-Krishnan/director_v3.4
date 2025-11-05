# Stage 6 (CONTENT_GENERATION) Standalone Test

## Purpose

Isolated testing of Stage 6 (CONTENT_GENERATION) without running Stages 1-5.

This test suite allows you to test the Text Service v1.2 integration independently by using a pre-prepared presentation strawman with all required v1.2 fields already populated.

## What It Tests

- ✅ Text Service v1.2 client initialization
- ✅ ServiceRouterV1_2 routing logic
- ✅ V1_2_Transformer request transformation
- ✅ Content generation for all slide types (hero and content)
- ✅ Error handling and fallbacks
- ✅ Enriched presentation creation
- ✅ Deck-builder integration (if enabled)

## Pre-Prepared Strawman

The `test_strawman.json` contains a complete presentation with:

- **3 slides**: title_slide, matrix_2x2, closing_slide
- **All v1.2 fields**:
  - `variant_id` (e.g., "hero_centered", "matrix_2x2")
  - `generated_title` (max 50 chars)
  - `generated_subtitle` (max 90 chars)
  - `slide_type_classification` (13-type taxonomy)
- **Presentation metadata**:
  - `footer_text` (max 20 chars)
- **Content guidance** for each slide
- **Layout IDs** pre-assigned (L29 for hero, L25 for content)

## Directory Structure

```
tests/stage6_only/
├── README.md                    # This file
├── test_strawman.json           # Pre-prepared strawman
├── test_content_generation.py   # Test script
└── output/                      # Test output (created at runtime)
    ├── test_results_*.json      # Test results with timestamps
    └── (other output files)
```

## Usage

### Basic Test Run

```bash
# From v3.4 directory
python tests/stage6_only/test_content_generation.py
```

### Expected Output

```
Stage 6 (CONTENT_GENERATION) Standalone Test
======================================================================
Text Service: https://web-production-5daf.up.railway.app
Version: v1.2
======================================================================

📄 Loading test strawman...
   Path: tests/stage6_only/test_strawman.json
✅ Strawman loaded
   Title: AI in Healthcare: Transforming Diagnostics
   Slides: 3
   Footer: AI Healthcare 2025

🔍 Validating v1.2 fields...
✅ All v1.2 fields present

🎬 Initializing Director Agent...
✅ Director initialized

📍 Creating StateContext for CONTENT_GENERATION...
✅ StateContext created

🚀 Running Stage 6 (CONTENT_GENERATION)...
This may take 30-60 seconds...

✅ Stage 6 completed in 45.32s

📊 Test Results
======================================================================
Total Slides: 3
Successful: 3
Failed: 0
Content Generated: True

🔗 Presentation URL:
   http://localhost:8504/p/abc-123-def
======================================================================

💾 Results saved:
   tests/stage6_only/output/test_results_20251104_143022.json

✅ TEST PASSED
```

## What Gets Tested

### 1. Strawman Validation
- Verifies all v1.2 fields are present
- Checks character limits (title: 50, subtitle: 90, footer: 20)
- Validates slide classifications

### 2. Text Service v1.2 Integration
- Tests unified `/v1.2/generate` endpoint
- Validates request transformation
- Tests variant-specific generation
- Verifies HTML output

### 3. Content Generation
- Generates real content for all 3 slides
- Tests both hero (L29) and content (L25) layouts
- Validates element-based generation
- Tests character count validation

### 4. Error Handling
- Tests fallback behavior
- Validates error reporting
- Tests partial failure scenarios

## Output Files

### test_results_[timestamp].json

Contains complete test results:

```json
{
  "timestamp": "2025-11-04T14:30:22.123Z",
  "duration_seconds": 45.32,
  "strawman_title": "AI in Healthcare: Transforming Diagnostics",
  "slide_count": 3,
  "result": {
    "type": "presentation_url",
    "url": "http://localhost:8504/p/abc-123",
    "slide_count": 3,
    "content_generated": true,
    "successful_slides": 3,
    "failed_slides": 0
  }
}
```

## Troubleshooting

### Test Fails with "Missing variant_id"

**Cause**: test_strawman.json is missing v1.2 fields

**Fix**: Ensure test_strawman.json has all fields (see template in this directory)

### Test Fails with "Text Service connection error"

**Cause**: Text Service v1.2 is unreachable

**Fix**:
1. Check `TEXT_SERVICE_URL` in `.env`
2. Verify Text Service is running: `curl https://web-production-5daf.up.railway.app/health`
3. Check network connectivity

### Test Fails with "Deck-builder API error"

**Cause**: deck-builder service unavailable

**Fix**:
1. Ensure deck-builder is running on port 8504
2. Check `DECK_BUILDER_API_URL` in config/settings.py
3. Or set `DECK_BUILDER_ENABLED=false` to skip deck-builder integration

## Benefits of This Test

1. **Fast Iteration**: No LLM calls for Stages 1-5 (saves 2-3 minutes per test)
2. **Isolated Testing**: Debug Stage 6 issues without Stage 1-5 interference
3. **Reproducible**: Same strawman every test run
4. **Focused**: Only tests Text Service v1.2 integration
5. **Development**: Perfect for v1.2 feature development

## Related Files

- **Main Test Suite**: `tests/test_director_standalone.py` (tests all stages 1-6)
- **Service Router**: `src/utils/service_router_v1_2.py`
- **v1.2 Client**: `src/utils/text_service_client_v1_2.py`
- **v1.2 Transformer**: `src/utils/v1_2_transformer.py`

## Version

- **Director**: v3.4
- **Text Service**: v1.2
- **Test Suite**: v1.0
- **Last Updated**: 2025-11-04

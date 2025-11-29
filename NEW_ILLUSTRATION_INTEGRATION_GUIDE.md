# New Illustration Integration Guide
**Director Agent v3.4 - Illustrator Service Integration**

**Document Version**: 1.0
**Date**: November 29, 2025
**Status**: Comprehensive Integration & Testing Guide

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Current Illustration Integration Status](#current-illustration-integration-status)
4. [Step-by-Step Integration Process](#step-by-step-integration-process)
5. [Testing Strategy](#testing-strategy)
6. [Registration Checklist](#registration-checklist)
7. [Troubleshooting & Common Issues](#troubleshooting--common-issues)
8. [Future Illustrations Roadmap](#future-illustrations-roadmap)

---

## Executive Summary

This guide documents the **complete process for integrating new illustration variants** from the Illustrator Service v1.0 into Director Agent v3.4. The process follows a proven pattern established with Pyramid, Funnel, and Concentric Circles illustrations.

### What This Guide Covers

- ✅ **Registration Process**: How to register new illustration types in Director
- ✅ **Code Changes**: Exact files to modify and code patterns to follow
- ✅ **Classification**: How to add keyword-based detection for new illustrations
- ✅ **Routing**: How Director routes slides to Illustrator Service
- ✅ **Testing**: Comprehensive local and integration testing strategies
- ✅ **Validation**: Success criteria and quality gates

### Current Integration Status

| Illustration | Illustrator Service | Director v3.4 | Status |
|--------------|-------------------|---------------|--------|
| **Pyramid** (3-6 levels) | ✅ Production | ✅ Integrated | **Production** |
| **Funnel** (3-5 stages) | ✅ Complete | ⚠️ Partial | **Ready for Integration** |
| **Concentric Circles** (3-5 circles) | ✅ Complete | ⚠️ Partial | **Ready for Integration** |

### Key Insight

The integration architecture is **highly extensible** - adding a new illustration type requires:
- **~5 code changes** across 4 files
- **~30-50 keywords** for classification
- **~2-3 hours** of development time
- **~1-2 hours** of testing

---

## Architecture Overview

### Multi-Service Architecture

Director v3.4 uses a **service-based routing architecture** where different slide types are routed to specialized content generation services:

```
Director Agent v3.4
        ↓
    [Slide Type Classifier]
        ↓
    [Service Router v1.2]
        ↓
    ┌──────────────┬──────────────────┬───────────────────┐
    ↓              ↓                  ↓                   ↓
Text Service   Illustrator      Analytics          Hero Service
  (v1.2)       Service v1.0    Service v3.7         (v1.2)
    ↓              ↓                  ↓                   ↓
10 content     Visualizations     18 chart types      3 hero types
 layouts        (pyramid,           (pie, bar,        (title, section,
(matrix_2x2,    funnel,             line, etc.)        closing)
 bilateral,    concentric,
 sequential,    etc.)
 etc.)
```

### Illustration Integration Flow

```
Stage 4: Generate Strawman
    ↓
LLM selects slide_type = "funnel"
(based on keywords + context)
    ↓
Stage 5: Refine Strawman
(user can modify visualization config)
    ↓
Stage 6: Content Generation
    ↓
1. Slide Type Classifier validates: "funnel"
2. Service Registry lookup: "funnel" → illustrator_service
3. Service Router calls: IllustratorClient.generate_funnel()
4. Illustrator Service returns: HTML + metadata
5. Director wraps in Layout (L25, L01, or L02)
    ↓
Layout Builder renders slide
```

---

## Current Illustration Integration Status

### ✅ Fully Integrated: Pyramid

**Illustrator Service**: `/v1.0/pyramid/generate`
**Director Integration**: Complete and production-ready

**Integration Points**:
- ✅ `service_registry.py`: Registered in illustrator_service.slide_types
- ✅ `illustrator_client.py`: `generate_pyramid()` method implemented
- ✅ `slide_type_classifier.py`: PYRAMID_KEYWORDS defined (30+ keywords)
- ✅ `service_router_v1_2.py`: Pyramid routing logic implemented
- ✅ `generate_strawman.md`: Pyramid documented as available slide type

**Testing**:
- ✅ Unit tests: `tests/test_illustrator_client.py`
- ✅ Integration tests: `tests/illustrations/test_pyramid_*.py`
- ✅ End-to-end: Director Stage 4 → Stage 6 → Layout Builder

### ⚠️ Partially Integrated: Funnel

**Illustrator Service**: `/v1.0/funnel/generate` ✅ Complete
**Director Integration**: **Missing classification and routing**

**What's Missing**:
- ❌ `slide_type_classifier.py`: No FUNNEL_KEYWORDS defined
- ❌ `service_router_v1_2.py`: No funnel routing logic
- ❌ `generate_strawman.md`: Funnel not documented for LLM

**What's Already Done**:
- ✅ `service_registry.py`: Funnel endpoint registered (line 234)
- ✅ `illustrator_client.py`: `generate_funnel()` method exists (commented out, lines 424-513)

### ⚠️ Partially Integrated: Concentric Circles

**Illustrator Service**: `/v1.0/concentric_circles/generate` ✅ Complete
**Director Integration**: **Missing client method, classification, and routing**

**What's Missing**:
- ❌ `illustrator_client.py`: No `generate_concentric_circles()` method
- ❌ `service_registry.py`: Concentric circles endpoint not registered
- ❌ `slide_type_classifier.py`: No CONCENTRIC_CIRCLES_KEYWORDS defined
- ❌ `service_router_v1_2.py`: No concentric circles routing logic
- ❌ `generate_strawman.md`: Concentric circles not documented for LLM

**Integration Guide Available**:
- ✅ Complete guide: `illustrator/v1.0/docs/guides/CONCENTRIC_CIRCLES_DIRECTOR_INTEGRATION_GUIDE.md`

---

## Step-by-Step Integration Process

### Prerequisites

1. **Illustrator Service Running**: Verify at `http://localhost:8000`
2. **Endpoint Available**: Test the illustration endpoint directly
3. **Integration Guide**: Read the Illustrator service integration guide for the specific illustration

### Process Overview

```
Phase 1: Service Registry Registration (5 min)
    ↓
Phase 2: Illustrator Client Method (15 min)
    ↓
Phase 3: Slide Type Classification (20 min)
    ↓
Phase 4: Service Router Logic (30 min)
    ↓
Phase 5: LLM Prompt Update (20 min)
    ↓
Phase 6: Local Testing (30 min)
    ↓
Phase 7: Integration Testing (30 min)
    ↓
Total Time: ~2.5-3 hours per illustration
```

---

## Phase 1: Service Registry Registration

**File**: `src/utils/service_registry.py`

**What to Change**: Add the new illustration type to the `illustrator_service` configuration.

### Example: Adding Concentric Circles

**Location**: Line ~230-250

```python
"illustrator_service": ServiceConfig(
    enabled=True,
    base_url="http://localhost:8000",  # From settings
    slide_types=[
        "pyramid",
        "funnel",
        "concentric_circles",  # ✅ ADD THIS
    ],
    endpoints={
        "pyramid": ServiceEndpoint(
            path="/v1.0/pyramid/generate",
            method="POST",
            timeout=60
        ),
        "funnel": ServiceEndpoint(
            path="/v1.0/funnel/generate",
            method="POST",
            timeout=60
        ),
        "concentric_circles": ServiceEndpoint(  # ✅ ADD THIS
            path="/v1.0/concentric_circles/generate",
            method="POST",
            timeout=60
        )
    }
)
```

**Validation**:
```python
# Quick test in Python REPL
from src.utils.service_registry import get_service_for_slide_type

service = get_service_for_slide_type("concentric_circles")
print(service)  # Should print: "illustrator_service"
```

---

## Phase 2: Illustrator Client Method

**File**: `src/clients/illustrator_client.py`

**What to Add**: A new async method for generating the illustration.

### Template Pattern

All Illustrator client methods follow this pattern:

```python
async def generate_{illustration_name}(
    self,
    num_{elements}: int,           # e.g., num_circles, num_levels
    topic: str,
    presentation_id: Optional[str] = None,
    slide_id: Optional[str] = None,
    slide_number: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    target_points: Optional[List[str]] = None,
    tone: str = "professional",
    audience: str = "general",
    validate_constraints: bool = True
) -> Dict[str, Any]:
    """
    Generate {illustration_name} visualization with AI-generated content.

    Args:
        num_{elements}: Number of {elements} (X-Y range)
        topic: Main topic/theme
        presentation_id: Optional presentation identifier
        slide_id: Optional slide identifier
        slide_number: Optional slide position
        context: Additional context for content generation
        target_points: Optional suggested labels
        tone: Writing tone
        audience: Target audience
        validate_constraints: Whether to enforce character limits

    Returns:
        Dict with success, html, metadata, generated_content, validation
    """
    if not self.enabled:
        raise RuntimeError("Illustrator service is disabled in settings")

    # Build request payload
    payload = {
        "num_{elements}": num_{elements},
        "topic": topic,
        "tone": tone,
        "audience": audience,
        "validate_constraints": validate_constraints
    }

    # Add optional session tracking fields
    if presentation_id:
        payload["presentation_id"] = presentation_id
    if slide_id:
        payload["slide_id"] = slide_id
    if slide_number is not None:
        payload["slide_number"] = slide_number

    # Add context
    if context:
        payload["context"] = context
    if target_points:
        payload["target_points"] = target_points

    logger.info(
        f"Generating {num_{elements}} {illustration_name}: '{topic}'",
        extra={
            "num_{elements}": num_{elements},
            "topic": topic,
            "presentation_id": presentation_id,
            "slide_id": slide_id
        }
    )

    try:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/v1.0/{illustration_name}/generate",
                json=payload
            )

            if response.status_code == 200:
                result = response.json()

                # Log generation results
                validation = result.get("validation", {})
                logger.info(
                    "{illustration_name} generated successfully",
                    extra={
                        "topic": topic,
                        "html_size": len(result.get("html", "")),
                        "generation_time_ms": result.get("metadata", {}).get("generation_time_ms"),
                        "validation_valid": validation.get("valid")
                    }
                )

                return result

            elif response.status_code == 422:
                error_detail = response.json().get("detail", "Validation error")
                logger.error(
                    f"{illustration_name} validation error: {error_detail}",
                    extra={"topic": topic, "status_code": 422}
                )
                raise ValueError(f"{illustration_name} validation error: {error_detail}")

            else:
                logger.error(
                    f"Illustrator API error: {response.status_code}",
                    extra={"status_code": response.status_code}
                )
                raise httpx.HTTPError(
                    f"Illustrator API error: {response.status_code}"
                )

    except httpx.TimeoutException as e:
        logger.error(
            f"Illustrator service timeout after {self.timeout}s",
            extra={"topic": topic, "timeout": self.timeout}
        )
        raise

    except Exception as e:
        logger.error(
            f"Unexpected error generating {illustration_name}: {str(e)}",
            extra={"topic": topic, "error_type": type(e).__name__}
        )
        raise
```

### Example: Concentric Circles Method

```python
async def generate_concentric_circles(
    self,
    num_circles: int,
    topic: str,
    presentation_id: Optional[str] = None,
    slide_id: Optional[str] = None,
    slide_number: Optional[int] = None,
    context: Optional[Dict[str, Any]] = None,
    target_points: Optional[List[str]] = None,
    tone: str = "professional",
    audience: str = "general",
    validate_constraints: bool = True
) -> Dict[str, Any]:
    """
    Generate concentric circles visualization with AI-generated content.

    The Illustrator service will:
    1. Generate circle labels and legend content using Gemini LLM
    2. Apply character constraints (with auto-retry)
    3. Create HTML visualization with embedded CSS
    4. Consider previous slides context for narrative continuity

    Args:
        num_circles: Number of concentric circles (3-5)
        topic: Main topic/theme for the circles
        presentation_id: Optional presentation identifier (for logging)
        slide_id: Optional slide identifier (for logging)
        slide_number: Optional slide position (for context)
        context: Additional context dict with keys:
            - presentation_title: Overall presentation title
            - previous_slides: List of previous slide summaries (for LLM context)
            - slide_purpose: Purpose of this specific slide
            - industry: Industry context (optional)
        target_points: Optional list of circle labels (e.g., ["Core", "Extended", "Reach"])
        tone: Content tone (professional, casual, technical, etc.)
        audience: Target audience type
        validate_constraints: Enable character constraint validation

    Returns:
        Dict containing:
            - html: Complete HTML visualization (ready for L25 rich_content)
            - generated_content: Structured data (circle labels, legend bullets)
            - metadata: Generation metadata (model, time, version)
            - validation: Constraint validation results

    Raises:
        httpx.HTTPError: If API call fails
        ValueError: If response is invalid
    """
    # [Implementation follows template pattern above]
    # Replace {illustration_name} with "concentric_circles"
    # Replace num_{elements} with "num_circles"
```

**Location**: Add after the `generate_funnel()` method (around line 513)

---

## Phase 3: Slide Type Classification

**File**: `src/utils/slide_type_classifier.py`

**What to Add**: Keyword set for detecting the new illustration type.

### Keyword Design Principles

1. **Comprehensive Coverage**: Include 30-50 keywords
2. **Specific Terms**: Technical terms that uniquely identify this illustration
3. **Common Phrases**: How users naturally describe this visual
4. **Variations**: Singular, plural, hyphenated variants
5. **Use Cases**: When this illustration is appropriate

### Example: Funnel Keywords

```python
# Add around line 126 (after ANALYTICS_KEYWORDS)

FUNNEL_KEYWORDS = {
    # Core funnel terms
    "funnel", "sales funnel", "conversion funnel", "marketing funnel",
    "customer funnel", "pipeline", "sales pipeline", "lead pipeline",

    # Funnel stages
    "awareness", "consideration", "decision", "conversion",
    "tofu", "mofu", "bofu",  # Top/Middle/Bottom of funnel
    "lead generation", "qualification", "nurturing", "closing",

    # Funnel concepts
    "conversion rate", "conversion optimization", "drop-off",
    "customer journey", "buyer journey", "purchase journey",
    "stages of buying", "sales process", "conversion process",

    # Funnel metrics
    "funnel metrics", "funnel analysis", "funnel optimization",
    "conversion tracking", "stage conversion", "funnel drop-off",

    # Funnel variations
    "inverted funnel", "hourglass funnel", "bowtie funnel",
    "4-stage funnel", "5-stage funnel", "multi-stage funnel",

    # Funnel applications
    "lead to customer", "prospect to sale", "awareness to purchase",
    "from lead to close", "acquisition funnel", "retention funnel",
    "email funnel", "content funnel", "social media funnel",

    # Visual indicators
    "narrowing", "filtering", "progressive", "step-by-step reduction",
    "decreasing stages", "elimination process"
}
```

### Example: Concentric Circles Keywords

```python
# Add after FUNNEL_KEYWORDS

CONCENTRIC_CIRCLES_KEYWORDS = {
    # Core concentric terms
    "concentric", "concentric circles", "nested circles", "circular layers",
    "rings", "orbital", "radial", "ripple effect", "ripples",

    # Circle/layer concepts
    "inner circle", "outer circle", "core and periphery",
    "center outward", "from center", "expanding circles",
    "layered circles", "multiple circles", "circular zones",

    # Spatial relationships
    "influence zones", "zones of influence", "reach layers",
    "impact radius", "sphere of influence", "concentric zones",
    "proximity circles", "distance from core",

    # Common use cases
    "stakeholder map", "stakeholder circles", "influence mapping",
    "target audience layers", "customer segments",
    "market reach", "market penetration", "market layers",
    "engagement levels", "user segmentation circles",

    # Business applications
    "core competency", "core capabilities", "extended capabilities",
    "core team", "extended team", "partner network",
    "primary market", "secondary market", "tertiary market",
    "first-tier", "second-tier", "third-tier",

    # Organizational concepts
    "organizational layers", "reporting circles", "decision circles",
    "inner workings", "expanding scope", "broadening reach",

    # Visual descriptors
    "bull's eye", "bullseye", "target circles", "dartboard",
    "onion layers", "layered approach", "nested structure",
    "radiating", "emanating", "outward expansion"
}
```

### Update Classification Priority

**Location**: `_classify_content()` method (around line 252)

Add the new illustration type to the priority list:

```python
def _classify_content(cls, slide: Slide) -> str:
    """
    Classify as L25 content type using priority heuristics.

    Priority Order:
    1. Quote → impact_quote
    2. Analytics → analytics
    3. Metrics → metrics_grid
    4. Pyramid → pyramid
    5. Funnel → funnel              # ✅ ADD THIS
    6. Concentric Circles → concentric_circles  # ✅ ADD THIS
    7. Matrix → matrix_2x2
    8. Grid → grid_3x3
    9. Table → styled_table
    10. Comparison → bilateral_comparison
    11. Sequential → sequential_3col
    12. Hybrid → hybrid_1_2x2
    13. Asymmetric → asymmetric_8_4
    14. Default → single_column
    """
    text_corpus = cls._build_text_corpus(slide)

    # Priority 1: Quote
    if cls._contains_keywords(text_corpus, cls.QUOTE_KEYWORDS):
        return "impact_quote"

    # Priority 2: Analytics
    if cls._contains_keywords(text_corpus, cls.ANALYTICS_KEYWORDS):
        return "analytics"

    # Priority 3: Metrics
    if cls._contains_keywords(text_corpus, cls.METRICS_KEYWORDS):
        if "3" in text_corpus or "three" in text_corpus:
            return "metrics_grid"

    # Priority 4: Pyramid
    if cls._contains_keywords(text_corpus, cls.PYRAMID_KEYWORDS):
        return "pyramid"

    # ✅ Priority 5: Funnel (ADD THIS)
    if cls._contains_keywords(text_corpus, cls.FUNNEL_KEYWORDS):
        return "funnel"

    # ✅ Priority 6: Concentric Circles (ADD THIS)
    if cls._contains_keywords(text_corpus, cls.CONCENTRIC_CIRCLES_KEYWORDS):
        return "concentric_circles"

    # [Rest of priority checks...]
```

**Important**: The priority order matters! Illustrations with more specific keywords should come before generic ones.

---

## Phase 4: Service Router Logic

**File**: `src/utils/service_router_v1_2.py`

**What to Add**: Routing logic that detects the illustration type and calls the appropriate client method.

### Step 4.1: Add Detection Helper Method

**Location**: Around line 1018 (after `_is_pyramid_slide()`)

```python
def _is_funnel_slide(self, slide: Slide) -> bool:
    """
    Check if slide is a funnel visualization slide.

    Funnel slides are generated by Illustrator Service v1.0,
    not Text Service v1.2.

    Args:
        slide: Slide object to check

    Returns:
        True if funnel slide, False otherwise
    """
    return slide.slide_type_classification == 'funnel'

def _is_concentric_circles_slide(self, slide: Slide) -> bool:
    """
    Check if slide is a concentric circles visualization slide.

    Concentric circles slides are generated by Illustrator Service v1.0,
    not Text Service v1.2.

    Args:
        slide: Slide object to check

    Returns:
        True if concentric circles slide, False otherwise
    """
    return slide.slide_type_classification == 'concentric_circles'
```

### Step 4.2: Add Routing Logic in `process_slides()`

**Location**: Around line 637-750 (in the main slide processing loop)

**Pattern**: Add detection and routing logic for each illustration type, following the pyramid pattern.

```python
# Inside process_slides() method, after analytics check

# Check if this is a funnel slide
is_funnel = self._is_funnel_slide(slide)

if is_funnel:
    # Generate funnel using Illustrator Service
    logger.info(
        f"🔻 Generating funnel slide {slide_number}/{len(slides)}: "
        f"{slide.slide_id}"
    )

    # Check if Illustrator client is available
    if not self.illustrator_client:
        error_msg = "Funnel slide requires IllustratorClient but none provided"
        logger.error(error_msg)
        failed_slides.append({
            "slide_number": slide_number,
            "slide_id": slide.slide_id,
            "slide_type": slide.slide_type_classification,
            "error": error_msg,
            "service": "illustrator_v1.0",
            "endpoint": None,
            "error_category": "validation",
            "suggested_action": "Ensure IllustratorClient is properly initialized.",
            "http_status": None
        })
        continue

    try:
        # Build funnel configuration from key_points
        num_stages = len(slide.key_points) if slide.key_points else 4
        num_stages = max(3, min(5, num_stages))  # Clamp to 3-5
        target_points = slide.key_points if slide.key_points else None

        logger.info(
            f"   🔻 CALLING ILLUSTRATOR SERVICE /v1.0/funnel/generate"
        )
        logger.info(f"      Topic: {slide.generated_title}")
        logger.info(f"      Num Stages: {num_stages}")
        logger.info(f"      Target Points: {target_points}")

        # Call Illustrator Service to generate funnel
        start = datetime.utcnow()
        funnel_response = await self.illustrator_client.generate_funnel(
            num_stages=num_stages,
            topic=slide.generated_title,
            target_points=target_points,
            tone=strawman.overall_theme or "professional",
            audience=strawman.target_audience or "general",
            presentation_id=getattr(strawman, 'preview_presentation_id', None),
            slide_id=slide.slide_id,
            slide_number=slide_number,
            validate_constraints=True
        )
        duration = (datetime.utcnow() - start).total_seconds()

        logger.info(
            f"   ✅ Illustrator Service returned in {duration:.2f}s"
        )
        logger.info(
            f"      HTML length: {len(funnel_response.get('html', ''))} chars"
        )
        logger.info(
            f"      Validation status: {funnel_response.get('validation', {}).get('valid', 'unknown')}"
        )

        total_generation_time += duration

        # Build successful result
        slide_result = {
            "slide_number": slide_number,
            "slide_id": slide.slide_id,
            "content": funnel_response["html"],
            "metadata": {
                "generated_content": funnel_response.get("generated_content", {}),
                "validation": funnel_response.get("validation", {}),
                "service": "illustrator_v1.0",
                "slide_type": "funnel"
            },
            "generation_time_ms": int(duration * 1000),
            "endpoint_used": "/v1.0/funnel/generate",
            "slide_type": "funnel"
        }

        generated_slides.append(slide_result)
        logger.info(
            f"✅ Funnel slide {slide_number} generated successfully "
            f"({duration:.2f}s)"
        )

    except Exception as funnel_error:
        # Error handling
        error_info = self._classify_error(funnel_error)

        logger.error(
            f"   ❌ FUNNEL GENERATION FAILED"
        )
        logger.error(f"      Error Type: {type(funnel_error).__name__}")
        logger.error(f"      Error Message: {str(funnel_error)}")

        failed_slides.append({
            "slide_number": slide_number,
            "slide_id": slide.slide_id,
            "slide_type": slide.slide_type_classification,
            "error": str(funnel_error),
            "service": "illustrator_v1.0",
            "endpoint": "/v1.0/funnel/generate",
            **error_info
        })

    continue  # Skip to next slide

# [Repeat similar pattern for concentric_circles]
```

### Step 4.3: Update Validation Check

**Location**: Around line 370 (where pyramid slides are checked)

```python
# v3.4-illustrations: Check if this is an illustration slide
is_pyramid = self._is_pyramid_slide(slide)
is_funnel = self._is_funnel_slide(slide)               # ✅ ADD THIS
is_concentric = self._is_concentric_circles_slide(slide)  # ✅ ADD THIS
is_illustration = is_pyramid or is_funnel or is_concentric  # ✅ ADD THIS

# Illustrations don't need variant_id (use Illustrator Service)
if not is_hero and not is_illustration and not is_analytics and not slide.variant_id:
    logger.error(
        f"Slide {slide_number} ({slide.slide_id}) has no variant_id. "
        f"Type: {slide.slide_type_classification}"
    )
    # [Error handling...]
```

---

## Phase 5: LLM Prompt Update

**File**: `config/prompts/modular/generate_strawman.md`

**What to Add**: Documentation for the LLM to understand when and how to use the new illustration type.

### Template for Illustration Documentation

```markdown
## Available Slide Types (X types)

### Illustrator Service Types (Visualizations)

[...existing pyramid entry...]

**X. {illustration_name}** ({range} {elements})
   - **Use for**: {primary use cases}
   - **Best for**: {specific scenarios}
   - **{Elements}**: {range} {element description}
   - **Config**: Specify `{element_count}` in `visualization_config`
   - **Example**: {concrete example with data}
   - **Keywords**: {key terms that trigger this type}

### When to Use {Illustration Name}

**Choose {illustration_name} when presenting**:
- {Use case 1 with specific example}
- {Use case 2 with specific example}
- {Use case 3 with specific example}
- {Use case 4 with specific example}

**{Element} Count Guidelines**:
- **{min} {elements}**: {scenario}
- **{mid} {elements}**: {scenario}
- **{max} {elements}**: {scenario}

**Key Points as {Element} Labels**:
When you identify a {illustration_name} slide, put {element} labels in `key_points` array.

Example:
```json
{
  "slide_type": "{illustration_name}",
  "title": "{Example Title}",
  "key_points": ["{Label 1}", "{Label 2}", "{Label 3}", "{Label 4}"],
  "visualization_config": {
    "{element_count}": 4
  }
}
```
```

### Example: Funnel Documentation

```markdown
### Illustrator Service Types (Visualizations)

1. **pyramid** (3-6 levels) - [existing entry]

2. **funnel** (3-5 stages)
   - **Use for**: Sales pipelines, conversion processes, customer journeys,
     marketing funnels, lead qualification stages, progressive filtering
   - **Best for**: Showing volume reduction through stages, conversion rates,
     pipeline analysis, stage-by-stage processes with decreasing quantities
   - **Stages**: 3-5 stages (wide to narrow funnel)
   - **Config**: Specify `funnel_stages` in `visualization_config`
   - **Example**: "Sales Pipeline" with 4 stages (Awareness → Interest → Decision → Purchase)
   - **Keywords**: funnel, pipeline, conversion, customer journey, stages,
     lead generation, qualification, TOFU/MOFU/BOFU

3. **concentric_circles** (3-5 circles)
   - **Use for**: Influence zones, stakeholder mapping, market reach layers,
     organizational proximity, target audience segmentation, sphere of influence
   - **Best for**: Showing relationships from core to periphery, nested structures,
     expanding scope, layers of engagement, radiating impact
   - **Circles**: 3-5 concentric circles (inner to outer)
   - **Config**: Specify `num_circles` in `visualization_config`
   - **Example**: "Market Reach Strategy" with 3 circles (Core Customers → Active Users → Potential Market)
   - **Keywords**: concentric, circles, zones, influence, core to periphery,
     stakeholder map, layers, radiating, nested

### When to Use Funnel

**Choose funnel when presenting**:
- Sales pipelines showing lead-to-customer conversion (Leads → Qualified → Proposals → Closed)
- Marketing funnels with awareness-to-purchase stages (TOFU → MOFU → BOFU → Customers)
- Customer journey mapping (Awareness → Consideration → Decision → Retention)
- Conversion optimization processes (Traffic → Signups → Trials → Paid Customers)
- Lead qualification processes (Inquiry → MQL → SQL → Opportunity → Win)

**Stage Count Guidelines**:
- **3 stages**: Simple funnels (Awareness → Consideration → Purchase)
- **4 stages**: Standard sales funnels (Awareness → Interest → Decision → Action)
- **5 stages**: Detailed conversion funnels (Awareness → Interest → Consideration → Intent → Purchase)

**Key Points as Funnel Stages**:
When you identify a funnel slide, put stage names in `key_points` array (top to bottom).

Example:
```json
{
  "slide_type": "funnel",
  "title": "Sales Conversion Funnel",
  "key_points": ["Website Visitors", "Qualified Leads", "Sales Opportunities", "Closed Deals"],
  "visualization_config": {
    "funnel_stages": 4
  }
}
```

### When to Use Concentric Circles

**Choose concentric_circles when presenting**:
- Stakeholder influence mapping (Core Team → Department → Company → Partners)
- Market reach strategy (Primary Market → Secondary → Tertiary → Future Opportunities)
- Organizational structure (Executive → Management → Team Leads → Staff → Contractors)
- Customer segmentation (VIP Customers → Active Users → Occasional Users → Potential Users)
- Impact zones (Direct Impact → Indirect Impact → Ripple Effects → Long-term Effects)

**Circle Count Guidelines**:
- **3 circles**: Simple core-to-periphery (Core → Extended → Outer)
- **4 circles**: Standard layered model (Inner → Mid-inner → Mid-outer → Outer)
- **5 circles**: Detailed nested structure (Center → Ring 1 → Ring 2 → Ring 3 → Periphery)

**Key Points as Circle Labels**:
When you identify a concentric_circles slide, put circle labels in `key_points` array (innermost to outermost).

Example:
```json
{
  "slide_type": "concentric_circles",
  "title": "Stakeholder Influence Map",
  "key_points": ["Core Team", "Department Leads", "Company-wide", "External Partners"],
  "visualization_config": {
    "num_circles": 4
  }
}
```
```

---

## Phase 6: Local Testing

### Test Suite Structure

```
tests/
├── test_illustrator_client.py           # Unit tests for client methods
├── illustrations/
│   ├── test_funnel_generation.py        # Funnel-specific tests
│   ├── test_concentric_production.py    # Concentric circles tests
│   └── test_full_gallery_with_layout.py # Integration tests
└── test_service_router_v1_2.py          # Routing logic tests
```

### Test 1: Illustrator Client Method

**File**: `tests/test_illustrator_client.py`

```python
import pytest
from src.clients.illustrator_client import IllustratorClient

@pytest.mark.asyncio
async def test_funnel_generation():
    """Test funnel illustration generation"""
    client = IllustratorClient("http://localhost:8000")

    result = await client.generate_funnel(
        num_stages=4,
        topic="Sales Conversion Pipeline",
        tone="professional",
        audience="sales team"
    )

    assert result["success"] is True
    assert "html" in result
    assert result["metadata"]["num_stages"] == 4
    assert len(result["html"]) > 1000  # Substantial HTML
    print(f"✅ Generated funnel HTML: {len(result['html'])} bytes")

@pytest.mark.asyncio
async def test_concentric_circles_generation():
    """Test concentric circles illustration generation"""
    client = IllustratorClient("http://localhost:8000")

    result = await client.generate_concentric_circles(
        num_circles=3,
        topic="Market Reach Strategy",
        target_points=["Core Market", "Extended Reach", "Future Opportunities"],
        tone="professional",
        audience="executives"
    )

    assert result["success"] is True
    assert "html" in result
    assert result["metadata"]["num_circles"] == 3
    assert "Core Market" in result["html"] or "core market" in result["html"].lower()
    print(f"✅ Generated concentric circles HTML: {len(result['html'])} bytes")

@pytest.mark.asyncio
async def test_illustration_with_context():
    """Test illustration generation with previous slides context"""
    client = IllustratorClient()

    context = {
        "presentation_title": "Q4 Strategy Review",
        "slide_purpose": "Show our sales process stages",
        "industry": "B2B SaaS",
        "previous_slides": [
            {
                "title": "Market Overview",
                "key_points": ["Growing demand", "Competitive landscape"]
            }
        ]
    }

    result = await client.generate_funnel(
        num_stages=5,
        topic="Enterprise Sales Funnel",
        context=context,
        presentation_id="test-pres-001",
        slide_id="slide-5",
        slide_number=5
    )

    assert result["success"] is True
    assert result["presentation_id"] == "test-pres-001"
    assert result["slide_id"] == "slide-5"
    assert result["slide_number"] == 5
    print("✅ Context and session tracking working correctly")
```

### Test 2: Slide Type Classification

**File**: `tests/test_slide_type_classifier.py`

```python
import pytest
from src.models.agents import Slide
from src.utils.slide_type_classifier import SlideTypeClassifier

def test_funnel_classification():
    """Test that funnel keywords trigger funnel classification"""
    slide = Slide(
        slide_number=3,
        slide_id="slide-3",
        title="Sales Conversion Funnel",
        narrative="Show our sales pipeline from lead to customer",
        key_points=[
            "Website Visitors",
            "Qualified Leads",
            "Sales Opportunities",
            "Closed Deals"
        ],
        layout_id="L25",
        slide_type_classification="",  # Will be set by classifier
        variant_id=None,
        generated_title="",
        tables_needed=None,
        analytics_needed=None,
        diagrams_needed=None,
        structure_preference=None
    )

    slide_type = SlideTypeClassifier.classify(slide, position=3, total_slides=10)

    assert slide_type == "funnel", f"Expected 'funnel', got '{slide_type}'"
    print(f"✅ Funnel keywords correctly classified as: {slide_type}")

def test_concentric_circles_classification():
    """Test that concentric circles keywords trigger classification"""
    slide = Slide(
        slide_number=5,
        slide_id="slide-5",
        title="Stakeholder Influence Map",
        narrative="Show concentric circles of influence from core team outward",
        key_points=[
            "Core Leadership",
            "Department Managers",
            "Company-wide Teams",
            "External Partners"
        ],
        layout_id="L25",
        slide_type_classification="",
        variant_id=None,
        generated_title="",
        tables_needed=None,
        analytics_needed=None,
        diagrams_needed=None,
        structure_preference=None
    )

    slide_type = SlideTypeClassifier.classify(slide, position=5, total_slides=10)

    assert slide_type == "concentric_circles", f"Expected 'concentric_circles', got '{slide_type}'"
    print(f"✅ Concentric circles keywords correctly classified as: {slide_type}")

def test_keyword_priority():
    """Test that illustration keywords take priority over generic keywords"""
    # Slide with both funnel and comparison keywords
    slide = Slide(
        slide_number=4,
        slide_id="slide-4",
        title="Sales Funnel Comparison",  # Has "comparison" but "funnel" should win
        narrative="Compare our sales funnel stages across regions",
        key_points=["Stage 1", "Stage 2", "Stage 3", "Stage 4"],
        layout_id="L25",
        slide_type_classification="",
        variant_id=None,
        generated_title="",
        tables_needed=None,
        analytics_needed=None,
        diagrams_needed=None,
        structure_preference=None
    )

    slide_type = SlideTypeClassifier.classify(slide, position=4, total_slides=10)

    # Funnel should win because it's higher priority than bilateral_comparison
    assert slide_type == "funnel", f"Expected 'funnel', got '{slide_type}' (priority issue)"
    print(f"✅ Keyword priority working correctly: {slide_type}")
```

### Test 3: Service Routing

**File**: `tests/test_service_router_illustrations.py`

```python
import pytest
from src.utils.service_router_v1_2 import ServiceRouterV1_2
from src.utils.text_service_client_v1_2 import TextServiceClientV1_2
from src.clients.illustrator_client import IllustratorClient
from src.models.agents import Slide, PresentationStrawman

@pytest.mark.asyncio
async def test_funnel_routing():
    """Test that funnel slides route to Illustrator Service"""

    # Create router with clients
    text_client = TextServiceClientV1_2()
    illustrator_client = IllustratorClient()
    router = ServiceRouterV1_2(
        text_service_client=text_client,
        illustrator_client=illustrator_client
    )

    # Create funnel slide
    funnel_slide = Slide(
        slide_number=3,
        slide_id="slide-3",
        title="Sales Funnel",
        narrative="Our sales conversion process",
        key_points=["Leads", "Qualified", "Opportunities", "Closed"],
        layout_id="L25",
        slide_type_classification="funnel",
        variant_id=None,
        generated_title="Sales Funnel",
        tables_needed=None,
        analytics_needed=None,
        diagrams_needed=None,
        structure_preference=None
    )

    # Create strawman
    strawman = PresentationStrawman(
        main_title="Q4 Sales Review",
        target_audience="executives",
        overall_theme="professional",
        estimated_duration=20,
        slides=[funnel_slide]
    )

    # Process slides
    result = await router.process_slides(strawman)

    assert result["success"] is True
    assert len(result["generated_slides"]) == 1

    generated = result["generated_slides"][0]
    assert generated["slide_type"] == "funnel"
    assert generated["endpoint_used"] == "/v1.0/funnel/generate"
    assert "html" in generated["content"] or len(generated["content"]) > 1000

    print(f"✅ Funnel slide routed correctly to Illustrator Service")
    print(f"   Generated HTML: {len(generated['content'])} bytes")
    print(f"   Generation time: {generated['generation_time_ms']}ms")

@pytest.mark.asyncio
async def test_mixed_slide_types_routing():
    """Test routing with multiple illustration types in one presentation"""

    text_client = TextServiceClientV1_2()
    illustrator_client = IllustratorClient()
    router = ServiceRouterV1_2(
        text_service_client=text_client,
        illustrator_client=illustrator_client
    )

    slides = [
        # Slide 1: Pyramid
        Slide(
            slide_number=1,
            slide_id="slide-1",
            title="Organizational Hierarchy",
            narrative="Our org structure",
            key_points=["Leadership", "Management", "Team", "Staff"],
            layout_id="L25",
            slide_type_classification="pyramid",
            variant_id=None,
            generated_title="Organizational Hierarchy",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        ),
        # Slide 2: Funnel
        Slide(
            slide_number=2,
            slide_id="slide-2",
            title="Sales Pipeline",
            narrative="Sales funnel stages",
            key_points=["Leads", "Qualified", "Closed"],
            layout_id="L25",
            slide_type_classification="funnel",
            variant_id=None,
            generated_title="Sales Pipeline",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        ),
        # Slide 3: Concentric Circles
        Slide(
            slide_number=3,
            slide_id="slide-3",
            title="Market Reach",
            narrative="Our market influence zones",
            key_points=["Core", "Extended", "Potential"],
            layout_id="L25",
            slide_type_classification="concentric_circles",
            variant_id=None,
            generated_title="Market Reach",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        )
    ]

    strawman = PresentationStrawman(
        main_title="Business Overview",
        target_audience="executives",
        overall_theme="professional",
        estimated_duration=15,
        slides=slides
    )

    result = await router.process_slides(strawman)

    assert result["success"] is True
    assert len(result["generated_slides"]) == 3

    # Verify each illustration type was routed correctly
    pyramid = result["generated_slides"][0]
    assert pyramid["slide_type"] == "pyramid"
    assert pyramid["endpoint_used"] == "/v1.0/pyramid/generate"

    funnel = result["generated_slides"][1]
    assert funnel["slide_type"] == "funnel"
    assert funnel["endpoint_used"] == "/v1.0/funnel/generate"

    concentric = result["generated_slides"][2]
    assert concentric["slide_type"] == "concentric_circles"
    assert concentric["endpoint_used"] == "/v1.0/concentric_circles/generate"

    print(f"✅ Mixed illustration types routed correctly")
    print(f"   Pyramid: {len(pyramid['content'])} bytes")
    print(f"   Funnel: {len(funnel['content'])} bytes")
    print(f"   Concentric: {len(concentric['content'])} bytes")
```

### Running the Tests

```bash
# Run all illustration tests
pytest tests/test_illustrator_client.py -v
pytest tests/test_slide_type_classifier.py -v
pytest tests/test_service_router_illustrations.py -v

# Run specific test
pytest tests/test_illustrator_client.py::test_funnel_generation -v

# Run with output
pytest tests/illustrations/ -v -s
```

---

## Phase 7: Integration Testing

### End-to-End Test

**File**: `tests/test_e2e_illustrations.py`

```python
import pytest
from src.agents.director import DirectorAgent

@pytest.mark.asyncio
async def test_full_pipeline_funnel():
    """Test complete Director pipeline with funnel illustration"""

    # Create Director agent
    director = DirectorAgent()

    # Simulate user request for funnel
    user_request = "Create a presentation showing our sales funnel from leads to customers"

    # Stage 4: Generate strawman
    strawman = await director.handle_strawman_generation(
        user_request=user_request,
        slide_count=5
    )

    # Verify funnel slide was selected
    funnel_slides = [s for s in strawman.slides if s.slide_type_classification == "funnel"]
    assert len(funnel_slides) > 0, "LLM should have selected at least one funnel slide"

    print(f"✅ Stage 4: LLM selected {len(funnel_slides)} funnel slide(s)")

    # Stage 6: Generate content
    enriched = await director.handle_content_generation(strawman)

    # Verify funnel HTML was generated
    funnel_results = [s for s in enriched["generated_slides"] if s["slide_type"] == "funnel"]
    assert len(funnel_results) > 0

    for result in funnel_results:
        assert "html" in result["content"] or len(result["content"]) > 1000
        assert result["endpoint_used"] == "/v1.0/funnel/generate"
        print(f"✅ Stage 6: Funnel slide {result['slide_number']} generated")
        print(f"   HTML size: {len(result['content'])} bytes")
        print(f"   Generation time: {result['generation_time_ms']}ms")

@pytest.mark.asyncio
async def test_illustration_gallery():
    """Test presentation with all illustration types"""

    director = DirectorAgent()

    # Create strawman with all illustration types
    from src.models.agents import Slide, PresentationStrawman

    slides = [
        Slide(
            slide_number=1,
            slide_id="slide-1",
            title="Organizational Hierarchy",
            narrative="pyramid structure",
            key_points=["Vision", "Strategy", "Operations", "Execution"],
            layout_id="L25",
            slide_type_classification="pyramid",
            variant_id=None,
            generated_title="Organizational Hierarchy",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        ),
        Slide(
            slide_number=2,
            slide_id="slide-2",
            title="Sales Funnel",
            narrative="conversion funnel",
            key_points=["Awareness", "Interest", "Decision", "Purchase"],
            layout_id="L25",
            slide_type_classification="funnel",
            variant_id=None,
            generated_title="Sales Funnel",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        ),
        Slide(
            slide_number=3,
            slide_id="slide-3",
            title="Market Reach",
            narrative="concentric circles showing influence zones",
            key_points=["Core Market", "Extended Reach", "Potential Markets"],
            layout_id="L25",
            slide_type_classification="concentric_circles",
            variant_id=None,
            generated_title="Market Reach",
            tables_needed=None,
            analytics_needed=None,
            diagrams_needed=None,
            structure_preference=None
        )
    ]

    strawman = PresentationStrawman(
        main_title="Illustration Gallery",
        target_audience="executives",
        overall_theme="professional",
        estimated_duration=15,
        slides=slides
    )

    # Generate all content
    result = await director.handle_content_generation(strawman)

    assert result["success"] is True
    assert len(result["generated_slides"]) == 3

    # Verify each type
    types_generated = [s["slide_type"] for s in result["generated_slides"]]
    assert "pyramid" in types_generated
    assert "funnel" in types_generated
    assert "concentric_circles" in types_generated

    print(f"✅ All illustration types generated successfully:")
    for slide in result["generated_slides"]:
        print(f"   - {slide['slide_type']}: {len(slide['content'])} bytes, {slide['generation_time_ms']}ms")
```

---

## Testing Strategy

### Testing Pyramid

```
Level 1: Unit Tests (Fast, Isolated)
    ├── Illustrator Client Methods
    ├── Slide Type Classifier
    └── Service Registry Lookup

Level 2: Integration Tests (Medium Speed)
    ├── Service Router Logic
    ├── Illustrator Service API Calls
    └── HTML Rendering

Level 3: End-to-End Tests (Slower, Complete)
    ├── Director Stage 4 → Stage 6
    ├── Multiple Illustration Types
    └── Layout Builder Integration
```

### Test Coverage Goals

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| `illustrator_client.py` | >90% | High |
| `slide_type_classifier.py` | >85% | High |
| `service_router_v1_2.py` | >80% | High |
| `service_registry.py` | >75% | Medium |
| End-to-end flows | 100% | High |

### Testing Checklist

**Before Integration (Pre-flight)**:
- [ ] Illustrator Service running on port 8000
- [ ] Test illustration endpoint directly (curl/Postman)
- [ ] Verify all variants work (3, 4, 5, etc.)
- [ ] Check response structure matches docs
- [ ] Confirm character constraint validation works

**After Code Changes (Integration)**:
- [ ] Unit test: Client method generates HTML
- [ ] Unit test: Keywords trigger correct classification
- [ ] Unit test: Service registry returns correct endpoint
- [ ] Integration test: Router calls correct client method
- [ ] Integration test: Mixed slide types route correctly
- [ ] E2E test: Director Stage 4 selects illustration
- [ ] E2E test: Director Stage 6 generates HTML
- [ ] Visual test: HTML renders correctly in layout

**Production Readiness**:
- [ ] All tests passing
- [ ] No console errors or warnings
- [ ] Generation time < 10s per illustration
- [ ] Character validation working
- [ ] Error handling graceful
- [ ] Logging informative

---

## Registration Checklist

Use this checklist when integrating a new illustration type:

### Phase 1: Service Registry (5 min)
- [ ] Add illustration type to `slide_types` array
- [ ] Add endpoint configuration to `endpoints` dict
- [ ] Verify `get_service_for_slide_type()` returns `"illustrator_service"`

### Phase 2: Illustrator Client (15 min)
- [ ] Add `async def generate_{illustration}()` method
- [ ] Follow template pattern (parameters, error handling, logging)
- [ ] Test method independently with curl to Illustrator service
- [ ] Verify response structure matches Illustrator docs

### Phase 3: Classification (20 min)
- [ ] Add `{ILLUSTRATION}_KEYWORDS` set (30-50 keywords)
- [ ] Add classification check in `_classify_content()` at correct priority
- [ ] Test keywords trigger correct classification
- [ ] Verify priority order (specific before generic)

### Phase 4: Service Router (30 min)
- [ ] Add `_is_{illustration}_slide()` helper method
- [ ] Add routing logic in `process_slides()` method
- [ ] Follow pyramid/funnel pattern exactly
- [ ] Include error handling and logging
- [ ] Update validation check to exclude illustration from variant_id requirement

### Phase 5: LLM Prompt (20 min)
- [ ] Add illustration to "Available Slide Types" section
- [ ] Document use cases and when to choose it
- [ ] Provide element count guidelines
- [ ] Include example JSON with visualization_config
- [ ] Add keywords reference

### Phase 6: Testing (1-2 hours)
- [ ] Unit test: Client method
- [ ] Unit test: Classification keywords
- [ ] Integration test: Service routing
- [ ] E2E test: Director Stage 4 selection
- [ ] E2E test: Director Stage 6 generation
- [ ] Visual test: HTML rendering in layouts

### Phase 7: Documentation (30 min)
- [ ] Update integration documentation
- [ ] Document any gotchas or edge cases
- [ ] Add to illustration types table
- [ ] Update README if needed

---

## Troubleshooting & Common Issues

### Issue 1: Illustration Not Being Selected in Stage 4

**Symptom**: LLM doesn't select the illustration type even when appropriate

**Possible Causes**:
1. Keywords not added to `slide_type_classifier.py`
2. Keywords too specific or not common enough
3. Priority order wrong (generic type selected instead)
4. LLM prompt not updated with illustration documentation

**Solutions**:
```python
# 1. Verify keywords are registered
from src.utils.slide_type_classifier import SlideTypeClassifier
print(SlideTypeClassifier.FUNNEL_KEYWORDS)  # Should print keyword set

# 2. Test classification manually
slide = create_test_slide_with_keywords()
slide_type = SlideTypeClassifier.classify(slide, 3, 10)
assert slide_type == "funnel"

# 3. Check priority order
# Ensure illustration comes before generic types in _classify_content()

# 4. Review LLM prompt
# Read config/prompts/modular/generate_strawman.md
# Verify illustration is documented with examples
```

### Issue 2: Routing to Wrong Service

**Symptom**: Illustration slide routes to Text Service instead of Illustrator

**Possible Causes**:
1. Service registry not updated
2. Classification returning wrong type
3. Routing logic missing or incorrect

**Solutions**:
```python
# 1. Check service registry
from src.utils.service_registry import get_service_for_slide_type
service = get_service_for_slide_type("funnel")
print(service)  # Should be "illustrator_service"

# 2. Verify classification
from src.utils.slide_type_classifier import SlideTypeClassifier
slide_type = SlideTypeClassifier.classify(slide, 3, 10)
print(slide_type)  # Should be "funnel"

# 3. Check routing detection
from src.utils.service_router_v1_2 import ServiceRouterV1_2
router = ServiceRouterV1_2(text_client, illustrator_client)
is_funnel = router._is_funnel_slide(slide)
print(is_funnel)  # Should be True
```

### Issue 3: Client Method Not Found

**Symptom**: `AttributeError: 'IllustratorClient' object has no attribute 'generate_funnel'`

**Possible Causes**:
1. Method not implemented in `illustrator_client.py`
2. Method name mismatch
3. Client not properly initialized

**Solutions**:
```python
# 1. Verify method exists
from src.clients.illustrator_client import IllustratorClient
client = IllustratorClient()
print(dir(client))  # Should include 'generate_funnel'

# 2. Check method signature
import inspect
print(inspect.signature(client.generate_funnel))

# 3. Test method directly
result = await client.generate_funnel(
    num_stages=4,
    topic="Test Funnel"
)
```

### Issue 4: Illustrator Service Timeout

**Symptom**: `httpx.TimeoutException` after 60 seconds

**Possible Causes**:
1. Illustrator service not running
2. LLM taking too long to generate content
3. Network issues
4. Complex illustration with many elements

**Solutions**:
```bash
# 1. Check Illustrator service health
curl http://localhost:8000/health

# 2. Increase timeout in settings.py
ILLUSTRATOR_SERVICE_TIMEOUT: int = Field(90, env="ILLUSTRATOR_SERVICE_TIMEOUT")

# 3. Test illustration endpoint directly
curl -X POST http://localhost:8000/v1.0/funnel/generate \
  -H "Content-Type: application/json" \
  -d '{"num_stages": 4, "topic": "Test"}'

# 4. Check Illustrator service logs
tail -f illustrator/v1.0/logs/app.log
```

### Issue 5: Character Constraint Violations

**Symptom**: Validation warnings about character limits exceeded

**Possible Causes**:
1. LLM generated content too long
2. Illustrator constraints too strict
3. Retry logic not working

**Impact**: Usually minor - illustrations still render correctly

**Solutions**:
```python
# 1. Check validation details
result = await client.generate_funnel(...)
if not result["validation"]["valid"]:
    for violation in result["validation"]["violations"]:
        print(f"{violation['field']}: {violation['actual_length']} chars (max: {violation['max_length']})")

# 2. This is expected behavior - Illustrator retries up to 3 times
# Minor violations (1-2 chars) don't affect visual quality

# 3. If violations are severe (>10 chars), check Illustrator service logs
```

### Issue 6: HTML Not Rendering in Layout

**Symptom**: Blank slide or rendering errors in Layout Builder

**Possible Causes**:
1. HTML structure incompatible with layout
2. Missing CSS styles
3. Incorrect field name in layout payload

**Solutions**:
```python
# 1. Check HTML structure
result = await client.generate_funnel(...)
print(result["html"][:500])  # First 500 chars
# Should have <div class="funnel-container"> structure

# 2. Verify layout payload
layout_content = {
    "slide_title": slide.title,
    "subtitle": "",
    "rich_content": result["html"]  # For L25 layout
}

# 3. Test HTML standalone
with open("test_funnel.html", "w") as f:
    f.write(result["html"])
# Open in browser to verify rendering

# 4. Check Layout Builder compatibility
# Illustrator HTML is self-contained with inline CSS
# Should work with L25, L01, L02 layouts
```

### Issue 7: Session Tracking Not Working

**Symptom**: `presentation_id`, `slide_id` not echoed in response

**Possible Causes**:
1. Fields not passed to client method
2. Illustrator service version mismatch
3. API contract change

**Solutions**:
```python
# 1. Verify fields are passed
result = await client.generate_funnel(
    num_stages=4,
    topic="Test",
    presentation_id="pres-123",  # ✅ Include this
    slide_id="slide-5",          # ✅ Include this
    slide_number=5               # ✅ Include this
)

# 2. Check response
assert result["presentation_id"] == "pres-123"
assert result["slide_id"] == "slide-5"
assert result["slide_number"] == 5

# 3. Check Illustrator service API docs
# Session fields should be optional and echoed back
```

---

## Future Illustrations Roadmap

### Illustrations Ready for Integration

| Illustration | Illustrator Service Status | Estimated Integration Time |
|--------------|---------------------------|--------------------------|
| **Funnel** (3-5 stages) | ✅ Complete | 2-3 hours |
| **Concentric Circles** (3-5 circles) | ✅ Complete | 2-3 hours |

### Future Illustration Ideas

Based on the established pattern, these illustrations could be added to the Illustrator service and integrated into Director:

| Illustration Type | Use Cases | Elements | Complexity |
|------------------|-----------|----------|------------|
| **SWOT Matrix** | Strategic analysis | 4 quadrants | Low |
| **BCG Matrix** | Portfolio analysis | 4 quadrants + bubbles | Medium |
| **Gantt Chart** | Project timelines | Bars on timeline | Medium |
| **Org Chart** | Organizational structure | Boxes + lines | Medium |
| **Value Chain** | Process flows | Sequential boxes | Low |
| **Mind Map** | Concept relationships | Central node + branches | High |
| **Venn Diagram** | Set relationships | 2-3 overlapping circles | Low |
| **Timeline** | Historical events | Points on line | Low |

### Integration Effort Estimates

**Per Illustration Type**:
- ⏱️ Illustrator Service endpoint: 8-12 hours (already done for Funnel/Concentric)
- ⏱️ Director integration: 2-3 hours (this guide's process)
- ⏱️ Testing: 1-2 hours
- ⏱️ Documentation: 1 hour
- **Total**: 12-18 hours from scratch, 4-6 hours if endpoint exists

---

## Summary

### What We've Learned

1. **Extensible Architecture**: Director's service-based routing makes adding illustrations straightforward
2. **Proven Pattern**: Pyramid integration established a template that Funnel/Concentric follow exactly
3. **5-File Integration**: Only 5 files need modification per illustration type
4. **Keyword-Based**: LLM selection relies on comprehensive keyword sets (30-50 keywords)
5. **Rapid Testing**: Well-structured tests enable quick validation

### Integration Workflow

```
1. Verify Illustrator endpoint ready (5 min)
    ↓
2. Update service registry (5 min)
    ↓
3. Add client method (15 min)
    ↓
4. Add classification keywords (20 min)
    ↓
5. Add routing logic (30 min)
    ↓
6. Update LLM prompt (20 min)
    ↓
7. Write tests (1-2 hours)
    ↓
8. Run end-to-end validation (30 min)
    ↓
Total: 2.5-3 hours per illustration
```

### Key Takeaways

✅ **Follow the Pattern**: Pyramid integration is the gold standard - replicate it exactly
✅ **Test Early**: Unit test each component before integration testing
✅ **Keywords Matter**: Spend time on comprehensive, specific keywords
✅ **Priority Order**: Place illustration types before generic content types
✅ **Error Handling**: Follow established error handling patterns
✅ **Documentation**: Update LLM prompts immediately - they guide selection

---

## Next Steps

### To Integrate Funnel

1. Read this guide thoroughly
2. Uncomment `generate_funnel()` in `illustrator_client.py` (lines 424-513)
3. Add FUNNEL_KEYWORDS to `slide_type_classifier.py`
4. Add funnel detection and routing to `service_router_v1_2.py`
5. Update `generate_strawman.md` with funnel documentation
6. Write and run tests
7. Validate end-to-end

### To Integrate Concentric Circles

1. Read `illustrator/v1.0/docs/guides/CONCENTRIC_CIRCLES_DIRECTOR_INTEGRATION_GUIDE.md`
2. Follow the step-by-step guide there
3. Use this document for testing strategy
4. Reference Funnel integration as parallel example

### General Integration

1. Use this guide as checklist
2. Follow the proven pattern
3. Test thoroughly at each phase
4. Document any deviations or issues

---

**Document Status**: ✅ Complete - Ready for Use
**Last Updated**: November 29, 2025
**Maintained By**: Director v3.4 Team

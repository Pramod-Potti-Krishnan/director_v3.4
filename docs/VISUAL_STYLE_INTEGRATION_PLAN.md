# Director Agent v3.4 - Visual Style System Integration Plan

**Document Version**: 1.0
**Date**: 2025-01-26
**Status**: Planning Phase
**Supersedes**: BACKGROUND_INTEGRATION_PLAN.md (merged concepts)
**Target Implementation**: v3.5

---

## Executive Summary

This document outlines the integration of the **Visual Style System** into Director Agent v3.4, enabling hero slides (title, section, closing) to use AI-generated background images with three distinct visual styles: **Professional**, **Illustrated**, and **Kids**.

**Key Features**:
- ✅ **New Endpoints**: `-with-image` variants for title, section, and closing slides
- ✅ **Visual Styles**: Professional (photorealistic), Illustrated (Ghibli-style), Kids (vibrant/playful)
- ✅ **Smart Defaults**: Title slides ALWAYS use images, section/closing configurable
- ✅ **Cost Optimization**: Fast models for illustrated/kids, standard for professional titles
- ✅ **Backward Compatible**: Existing presentations continue to work unchanged

---

## Table of Contents

1. [Visual Style System Overview](#visual-style-system-overview)
2. [Relationship to Background Integration Plan](#relationship-to-background-integration-plan)
3. [Integration Strategy](#integration-strategy)
4. [Implementation Phases](#implementation-phases)
5. [File Changes Summary](#file-changes-summary)
6. [Testing Strategy](#testing-strategy)
7. [Rollout Plan](#rollout-plan)

---

## Visual Style System Overview

### New Text Service v1.2 Endpoints

**With Images** (NEW):
- `/v1.2/hero/title-with-image` - Title slides with AI-generated backgrounds
- `/v1.2/hero/section-with-image` - Section dividers with AI-generated backgrounds
- `/v1.2/hero/closing-with-image` - Closing slides with AI-generated backgrounds

**Without Images** (Existing):
- `/v1.2/hero/title` - Title slides with gradient backgrounds (no images)
- `/v1.2/hero/section` - Section dividers with gradient backgrounds
- `/v1.2/hero/closing` - Closing slides with gradient backgrounds

### Visual Style Options

| Style | Description | Archetype | Use Case | Example Domains |
|-------|-------------|-----------|----------|-----------------|
| **professional** | Photorealistic, modern, clean | `photorealistic` | Corporate, business, healthcare | Modern hospitals, tech offices |
| **illustrated** | Ghibli-style, anime, hand-painted | `spot_illustration` | Creative, storytelling, engaging | Illustrated hospitals, cartoon tech |
| **kids** | Bright, vibrant, playful, exciting | `spot_illustration` | Children's content, education | Colorful adventures, fun scenes |

### Cost Structure

| Slide Type | Visual Style | Model | Cost | Generation Time |
|------------|--------------|-------|------|-----------------|
| Title | Professional | `imagen-3.0-generate-001` (standard) | $0.04 | ~10s |
| Title | Illustrated | `imagen-3.0-fast-generate-001` (fast) | $0.02 | ~5s |
| Title | Kids | `imagen-3.0-fast-generate-001` (fast) | $0.02 | ~5s |
| Section | All styles | `imagen-3.0-fast-generate-001` (fast) | $0.02 | ~5s |
| Closing | All styles | `imagen-3.0-fast-generate-001` (fast) | $0.02 | ~5s |

**Example Presentation Cost** (1 title + 3 sections + 1 closing):
- **Professional**: $0.12 (title $0.04 + sections $0.06 + closing $0.02)
- **Illustrated/Kids**: $0.10 (all fast models)
- **Savings**: 17% cost reduction with illustrated/kids vs professional

### Request Format

```json
{
  "slide_number": 1,
  "slide_type": "title_slide",
  "narrative": "AI-powered diagnostic accuracy in healthcare",
  "topics": ["AI", "Diagnostics", "Innovation"],
  "visual_style": "illustrated",  // NEW: professional, illustrated, or kids
  "context": {
    "theme": "professional",
    "audience": "healthcare executives"
  }
}
```

**Default Behavior**:
- If `visual_style` is omitted, defaults to `"professional"`
- Fully backward compatible with existing Director implementations

---

## Relationship to Background Integration Plan

### Clarification of Background Strategy

The **BACKGROUND_INTEGRATION_PLAN.md** documented a generic approach for adding `background_color` and `background_image` fields to slides. However, with the Visual Style System now available, we have a more specific and integrated solution:

**BACKGROUND_INTEGRATION_PLAN.md Approach** (generic):
```
Director → Image Generation Service → background_image URL → Layout Architect
```

**Visual Style System Approach** (integrated):
```
Director → Text Service v1.2 (/hero/*-with-image) → complete hero HTML with embedded image → Layout Architect
```

### Key Differences

| Aspect | Background Integration Plan | Visual Style System |
|--------|----------------------------|---------------------|
| **Image Source** | Generic Image Generation Service | Text Service v1.2 (Imagen integration) |
| **Integration** | Separate service call for images | Single call generates content + image |
| **Fields Added** | `background_color`, `background_image` | `visual_style`, `use_image_background` |
| **Endpoints** | No endpoint changes | New `-with-image` endpoints |
| **Scope** | All 6 layouts (L29, L25, L02, etc.) | Hero slides only (L29) |
| **Pass-through** | Background fields passed to services | Style parameter determines generation |

### Unified Strategy

**For Hero Slides (L29)**: Use Visual Style System
- Route to `/v1.2/hero/*-with-image` endpoints
- Pass `visual_style` parameter
- Text Service generates complete HTML with embedded background image
- No separate image generation needed

**For Content Slides (L25)**: Future enhancement
- Keep simple `background_color` approach from BACKGROUND_INTEGRATION_PLAN.md
- Subtle colors (#f8f9fa, #f0f9ff) for visual interest
- No images (focus on content readability)

**For Analytics Slides (L02, L01, L03, L27)**: Minimal backgrounds
- White or very light gray backgrounds only
- No images (avoid competing with data visualizations)

---

## Integration Strategy

### Complete Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: ASK_CLARIFYING_QUESTIONS                              │
│ Ask user: "What visual style for your presentation?"           │
│   - Professional (default - modern, clean)                      │
│   - Illustrated (creative, Ghibli-style)                        │
│   - Kids (bright, playful, fun)                                 │
│ Store preference: {"visual_style": "illustrated"}              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 4: GENERATE_STRAWMAN                                      │
│ For each HERO slide (title, section, closing):                 │
│   ├─ Assign visual_style (user preference OR AI default)       │
│   ├─ Decide: use_image_background = True/False                 │
│   │   └─ Title slides: ALWAYS True (user requirement)          │
│   │   └─ Section/Closing: Based on preference or theme         │
│   └─ Store in slide data structure                             │
│                                                                 │
│ For NON-HERO slides (content, analytics):                      │
│   └─ No visual_style needed (not applicable)                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 6: CONTENT_GENERATION - Hero Slide Routing               │
│ For each HERO slide:                                            │
│   ├─ Check: use_image_background?                              │
│   │   ├─ YES → Route to /v1.2/hero/{type}-with-image           │
│   │   │   ├─ Build payload with visual_style parameter         │
│   │   │   └─ Text Service generates hero HTML + background     │
│   │   └─ NO → Route to /v1.2/hero/{type} (existing)            │
│   │       └─ Text Service generates hero HTML with gradients   │
│   └─ Return complete hero HTML to Layout Architect             │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ CONTENT_TRANSFORMER                                             │
│ Transform to Layout Architect format:                          │
│ {                                                               │
│   "layout": "L29",                                             │
│   "variant_id": "hero_...",                                    │
│   "content": {                                                 │
│     "hero_content": "<div>Complete HTML with background</div>" │
│   }                                                            │
│ }                                                              │
│ Note: No separate background_color/background_image fields     │
│       Image is embedded in hero_content HTML                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ LAYOUT ARCHITECT (Layout Builder v7.5-main)                    │
│ Renders L29 slide with hero_content (includes background)      │
└─────────────────────────────────────────────────────────────────┘
```

### Decision Logic

#### When to Use -with-image Endpoints?

**Title Slides**: ALWAYS use images
```python
if slide.slide_type_classification == "title_slide":
    use_image_background = True  # User requirement: "Title slide with image is always preferred"
```

**Section Dividers**: Based on preference or theme
```python
if slide.slide_type_classification == "section_divider":
    if user_preferences.use_images_for_sections:
        use_image_background = True
    elif presentation_theme in ["creative", "storytelling", "engaging"]:
        use_image_background = True  # AI recommendation
    else:
        use_image_background = False  # Use gradient backgrounds
```

**Closing Slides**: Based on preference or theme
```python
if slide.slide_type_classification == "closing_slide":
    if user_preferences.use_images_for_closing:
        use_image_background = True
    elif presentation_theme in ["impactful", "memorable", "inspiring"]:
        use_image_background = True  # AI recommendation
    else:
        use_image_background = False  # Use gradient backgrounds
```

#### Visual Style Assignment

**User Preference** (highest priority):
```python
if user_preferences.visual_style:
    visual_style = user_preferences.visual_style  # "professional", "illustrated", "kids"
```

**AI Default** (based on audience/theme):
```python
else:
    if audience.includes("children") or theme == "educational_kids":
        visual_style = "kids"
    elif theme in ["creative", "storytelling", "artistic"]:
        visual_style = "illustrated"
    else:
        visual_style = "professional"  # Default
```

---

## Implementation Phases

### Phase 1: Data Model Extensions

**Files**: `src/models/agents.py`, `src/models/visual_styles.py` (new)

#### 1.1 Extend Slide Model

```python
# src/models/agents.py (add after generated_subtitle field)

class Slide(BaseModel):
    # ... existing fields ...
    generated_subtitle: Optional[str] = Field(...)

    # v3.5-visual-styles: Visual style configuration for hero slides
    visual_style: Optional[Literal["professional", "illustrated", "kids"]] = Field(
        default=None,
        description=(
            "Visual style for hero slide images. Only applicable to hero slides (L29). "
            "Options: professional (photorealistic), illustrated (Ghibli-style), kids (vibrant/playful). "
            "Assigned in GENERATE_STRAWMAN based on user preference or AI defaults."
        )
    )
    use_image_background: bool = Field(
        default=False,
        description=(
            "Whether to use AI-generated image background for hero slides. "
            "Title slides: ALWAYS True. Section/Closing: Based on preference or theme. "
            "Determines routing to /hero/*-with-image vs /hero/* endpoints."
        )
    )
```

#### 1.2 Extend PresentationStrawman Model

```python
# src/models/agents.py (add to PresentationStrawman)

class PresentationStrawman(BaseModel):
    # ... existing fields ...

    # v3.5-visual-styles: User visual style preferences
    visual_style_preference: Optional[Literal["professional", "illustrated", "kids"]] = Field(
        default=None,
        description="User's preferred visual style from Stage 2 clarifying questions"
    )
    use_images_for_sections: bool = Field(
        default=False,
        description="Whether to use images for section divider slides (user preference)"
    )
    use_images_for_closing: bool = Field(
        default=True,
        description="Whether to use images for closing slide (default: True for impact)"
    )
```

#### 1.3 Create Visual Style Models

```python
# src/models/visual_styles.py (new file)

from typing import Literal
from pydantic import BaseModel, Field

class VisualStylePreferences(BaseModel):
    """User preferences for visual styles from Stage 2."""
    visual_style: Literal["professional", "illustrated", "kids"] = Field(
        default="professional",
        description="Preferred visual style for hero slides"
    )
    use_images_for_title: bool = Field(
        default=True,
        description="Use images for title slide (always True per requirements)"
    )
    use_images_for_sections: bool = Field(
        default=False,
        description="Use images for section divider slides"
    )
    use_images_for_closing: bool = Field(
        default=True,
        description="Use images for closing slide"
    )

class VisualStyleAssignmentRules(BaseModel):
    """Rules for AI-driven visual style assignment."""
    kids_audience_keywords: list[str] = Field(
        default=["children", "kids", "students", "elementary", "kindergarten"]
    )
    creative_theme_keywords: list[str] = Field(
        default=["creative", "storytelling", "artistic", "imaginative", "innovative"]
    )
    professional_theme_keywords: list[str] = Field(
        default=["corporate", "business", "professional", "executive", "formal"]
    )
```

---

### Phase 2: Stage 2 Enhancement - User Preferences

**Files**: `config/prompts/modular/02_ask_clarifying_questions.md`, `src/agents/director.py`

#### 2.1 Update Clarifying Questions Prompt

```markdown
# config/prompts/modular/02_ask_clarifying_questions.md

<!-- Add as question 6 or 7, after audience/theme questions -->

### Visual Style (Optional)

What visual style would you like for your presentation's title and hero slides?

**Options:**

1. **Professional** (Default)
   - Modern, photorealistic backgrounds
   - Clean, corporate aesthetic
   - Best for: Business presentations, corporate meetings, professional conferences

2. **Illustrated**
   - Artistic, Ghibli-style anime illustrations
   - Hand-painted, creative aesthetic
   - Best for: Storytelling, creative pitches, engaging narratives

3. **Kids**
   - Bright, vibrant, playful backgrounds
   - Colorful, exciting aesthetic
   - Best for: Educational content, children's presentations, fun topics

**Image Background Options:**
- Title slide: Will ALWAYS use image background (for maximum impact)
- Section dividers: Would you like images here? [Yes/No/Let AI decide]
- Closing slide: Would you like an image? [Yes/No/Let AI decide]

If you're unsure, I can select the best visual style based on your audience and theme.
```

#### 2.2 Parse Visual Style Preferences

```python
# src/agents/director.py (in Stage 2 processing)

def _parse_visual_style_preferences(self, user_response: str) -> VisualStylePreferences:
    """
    Extract visual style preferences from user's clarifying answers.

    Examples:
    - "Professional style" → VisualStylePreferences(visual_style="professional")
    - "Illustrated, use images for sections" →
        VisualStylePreferences(visual_style="illustrated", use_images_for_sections=True)
    - "Let AI decide" → Returns None, will use AI defaults in Stage 4

    Returns:
        VisualStylePreferences or None if user wants AI to decide
    """
    # Implementation with LLM extraction
    prompt = f"""
    Extract visual style preferences from this user response: "{user_response}"

    Return JSON:
    {{
        "visual_style": "professional" | "illustrated" | "kids" | null,
        "use_images_for_sections": true | false | null,
        "use_images_for_closing": true | false | null
    }}

    If user says "let AI decide" or doesn't specify, return null for that field.
    """

    # Call LLM to extract structured preferences
    result = await self._call_llm(prompt, response_format="json")

    if result.get("visual_style"):
        return VisualStylePreferences(**result)
    else:
        return None  # AI will decide in Stage 4
```

---

### Phase 3: Stage 4 Enhancement - Visual Style Assignment

**Files**: `src/agents/director.py`, `src/utils/visual_style_assigner.py` (new)

#### 3.1 Create VisualStyleAssigner Class

```python
# src/utils/visual_style_assigner.py (new file)

from typing import Optional, Literal
from src.models.visual_styles import VisualStylePreferences, VisualStyleAssignmentRules
from src.models.agents import Slide, PresentationStrawman

class VisualStyleAssigner:
    """
    Assign visual styles to hero slides with user override support.

    Responsibilities:
    1. Apply user preferences if provided (hybrid approach)
    2. Use AI default rules based on audience and theme
    3. Determine use_image_background for each hero slide
    4. Assign visual_style (professional, illustrated, kids)
    """

    def __init__(
        self,
        user_preferences: Optional[VisualStylePreferences] = None,
        rules: Optional[VisualStyleAssignmentRules] = None
    ):
        self.user_preferences = user_preferences
        self.rules = rules or VisualStyleAssignmentRules()

    def assign_visual_style(
        self,
        slide: Slide,
        strawman: PresentationStrawman
    ) -> dict:
        """
        Assign visual style configuration to a hero slide.

        Args:
            slide: Slide to configure
            strawman: Presentation context

        Returns:
            Dictionary with:
            - visual_style: "professional", "illustrated", or "kids"
            - use_image_background: True/False
        """
        # Only applies to hero slides
        if slide.layout_id != "L29":
            return {
                "visual_style": None,
                "use_image_background": False
            }

        classification = slide.slide_type_classification

        # Determine use_image_background
        use_image = self._should_use_image_background(classification, strawman)

        # Determine visual_style
        style = self._determine_visual_style(strawman)

        return {
            "visual_style": style if use_image else None,
            "use_image_background": use_image
        }

    def _should_use_image_background(
        self,
        classification: str,
        strawman: PresentationStrawman
    ) -> bool:
        """Determine if slide should use image background."""

        # Title slides: ALWAYS use images (user requirement)
        if classification == "title_slide":
            return True

        # Section dividers: User preference or AI decision
        if classification == "section_divider":
            if self.user_preferences and self.user_preferences.use_images_for_sections is not None:
                return self.user_preferences.use_images_for_sections

            # AI recommendation: Use images for creative/storytelling themes
            theme = strawman.overall_theme.lower()
            creative_keywords = self.rules.creative_theme_keywords
            return any(keyword in theme for keyword in creative_keywords)

        # Closing slides: User preference or AI decision (default: True for impact)
        if classification == "closing_slide":
            if self.user_preferences and self.user_preferences.use_images_for_closing is not None:
                return self.user_preferences.use_images_for_closing

            # AI recommendation: Default to True for memorable closing
            return strawman.use_images_for_closing  # Default from strawman

        return False

    def _determine_visual_style(
        self,
        strawman: PresentationStrawman
    ) -> Literal["professional", "illustrated", "kids"]:
        """Determine visual style based on preferences or AI defaults."""

        # User preference takes precedence
        if self.user_preferences and self.user_preferences.visual_style:
            return self.user_preferences.visual_style

        # AI default based on audience and theme
        audience = strawman.target_audience.lower()
        theme = strawman.overall_theme.lower()

        # Kids audience → kids style
        if any(keyword in audience for keyword in self.rules.kids_audience_keywords):
            return "kids"

        # Creative theme → illustrated style
        if any(keyword in theme for keyword in self.rules.creative_theme_keywords):
            return "illustrated"

        # Default: professional
        return "professional"
```

#### 3.2 Integration into Director Agent

```python
# src/agents/director.py (in GENERATE_STRAWMAN state processing, after variant selection)

async def _post_process_strawman(self, strawman: PresentationStrawman) -> PresentationStrawman:
    """Post-process strawman slides with layout, classification, variant, and visual styles."""

    # Initialize visual style assigner
    visual_style_assigner = VisualStyleAssigner(
        user_preferences=strawman.visual_style_preference
    )

    for idx, slide in enumerate(strawman.slides):
        # ... existing layout selection, classification, variant selection ...

        # NEW: Assign visual style for hero slides (after variant selection, around line 533)
        if slide.layout_id == "L29":  # Hero slides only
            style_config = visual_style_assigner.assign_visual_style(
                slide=slide,
                strawman=strawman
            )

            slide.visual_style = style_config["visual_style"]
            slide.use_image_background = style_config["use_image_background"]

            logger.info(
                f"Slide {slide.slide_number} ({slide.slide_type_classification}): "
                f"visual_style={slide.visual_style}, use_image={slide.use_image_background}"
            )

        # ... continue with title/subtitle generation ...

    return strawman
```

---

### Phase 4: Stage 6 Enhancement - Service Routing with Visual Styles

**Files**: `src/utils/hero_request_transformer.py`, `src/utils/service_router_v1_2.py`

#### 4.1 Update Hero Request Transformer

```python
# src/utils/hero_request_transformer.py (modify CLASSIFICATION_TO_ENDPOINT mapping)

class HeroRequestTransformer:
    """
    Transforms Director slide data to Text Service v1.2 hero requests.

    v3.5 UPDATE: Supports -with-image endpoints and visual_style parameter.
    """

    # v3.5: Extended mapping for both regular and -with-image endpoints
    # Format: classification → base_endpoint_name
    CLASSIFICATION_TO_BASE_ENDPOINT = {
        "title_slide": "title",
        "section_divider": "section",
        "closing_slide": "closing"
    }

    def transform_to_hero_request(
        self,
        slide: Slide,
        strawman: PresentationStrawman
    ) -> Dict[str, Any]:
        """
        Transform Director slide to hero endpoint request format.

        v3.5 UPDATE: Determines endpoint based on use_image_background flag.
        Adds visual_style parameter for -with-image endpoints.
        """
        classification = slide.slide_type_classification

        if not self.is_hero_slide(classification):
            raise ValueError(
                f"Not a hero slide: {classification}. "
                f"Expected one of: {list(self.CLASSIFICATION_TO_BASE_ENDPOINT.keys())}"
            )

        # Get base endpoint name
        base_endpoint = self.CLASSIFICATION_TO_BASE_ENDPOINT[classification]

        # v3.5: Determine endpoint variant based on use_image_background
        if slide.use_image_background:
            endpoint = f"/v1.2/hero/{base_endpoint}-with-image"
        else:
            endpoint = f"/v1.2/hero/{base_endpoint}"

        logger.info(
            f"Transforming slide #{slide.slide_number} ({classification}) to {endpoint} "
            f"(visual_style: {slide.visual_style})"
        )

        # Build context from strawman and slide
        context = self._build_context(slide, strawman)

        # Build payload
        payload = {
            "slide_number": slide.slide_number,
            "slide_type": classification,
            "narrative": slide.narrative,
            "topics": self._extract_topics(slide),
            "context": context
        }

        # v3.5: Add visual_style parameter for -with-image endpoints
        if slide.use_image_background and slide.visual_style:
            payload["visual_style"] = slide.visual_style

        logger.debug(f"Hero request payload: {payload}")

        return {
            "endpoint": endpoint,
            "payload": payload
        }
```

#### 4.2 Service Router Logging

```python
# src/utils/service_router_v1_2.py (add diagnostic logging for visual styles)

# In the hero slide routing section (around line 438-486)

if is_hero:
    # NEW v3.5: Log visual style information
    logger.info(
        f"🎬 Generating hero slide {slide_number}/{len(slides)}: "
        f"{slide.slide_id} (type: {slide.slide_type_classification}) "
        f"[use_image: {slide.use_image_background}, style: {slide.visual_style}]"
    )

    # ... existing hero endpoint call code ...

    # v3.5 DIAGNOSTIC: Log endpoint used
    print(f"   🎬 CALLING HERO ENDPOINT", flush=True)
    print(f"      Endpoint: {hero_request_data['endpoint']}", flush=True)
    print(f"      Use Image: {slide.use_image_background}", flush=True)
    print(f"      Visual Style: {slide.visual_style}", flush=True)
    sys.stdout.flush()
```

---

### Phase 5: Testing & Validation

**Files**: `tests/test_visual_styles/` (new directory)

#### 5.1 Unit Tests - Visual Style Assignment

```python
# tests/test_visual_styles/test_style_assignment.py (new file)

import pytest
from src.utils.visual_style_assigner import VisualStyleAssigner
from src.models.visual_styles import VisualStylePreferences
from src.models.agents import Slide, PresentationStrawman

class TestVisualStyleAssigner:
    """Test visual style assignment logic."""

    def test_title_slide_always_uses_image(self):
        """Title slides ALWAYS use image background (user requirement)."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Introduction",
            layout_id="L29",
            slide_type_classification="title_slide",
            narrative="Welcome"
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["use_image_background"] is True
        assert result["visual_style"] == "professional"  # Default

    def test_user_preference_overrides_ai(self):
        """User visual style preference overrides AI defaults."""
        preferences = VisualStylePreferences(
            visual_style="illustrated",
            use_images_for_sections=True
        )
        assigner = VisualStyleAssigner(user_preferences=preferences)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type_classification="title_slide",
            narrative="Welcome"
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="corporate",  # Would normally be "professional"
            target_audience="executives"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["visual_style"] == "illustrated"  # User preference wins

    def test_kids_audience_gets_kids_style(self):
        """AI assigns kids style for children's audiences."""
        assigner = VisualStyleAssigner(user_preferences=None)

        strawman = PresentationStrawman(
            main_title="Fun Learning",
            overall_theme="educational",
            target_audience="children and elementary students"
        )

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type_classification="title_slide",
            narrative="Welcome"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["visual_style"] == "kids"

    def test_creative_theme_gets_illustrated_style(self):
        """AI assigns illustrated style for creative themes."""
        assigner = VisualStyleAssigner(user_preferences=None)

        strawman = PresentationStrawman(
            main_title="Creative Pitch",
            overall_theme="creative storytelling",
            target_audience="investors"
        )

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type_classification="title_slide",
            narrative="Our story"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["visual_style"] == "illustrated"

    def test_section_divider_without_preference(self):
        """Section dividers without user preference use AI logic."""
        assigner = VisualStyleAssigner(user_preferences=None)

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="corporate",  # Not creative
            target_audience="business"
        )

        slide = Slide(
            slide_number=2,
            slide_id="s2",
            title="Section",
            layout_id="L29",
            slide_type_classification="section_divider",
            narrative="New section"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["use_image_background"] is False  # Corporate theme, no images for sections

    def test_closing_slide_default_uses_image(self):
        """Closing slides default to using image for impact."""
        assigner = VisualStyleAssigner(user_preferences=None)

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business",
            use_images_for_closing=True  # Default
        )

        slide = Slide(
            slide_number=10,
            slide_id="s10",
            title="Closing",
            layout_id="L29",
            slide_type_classification="closing_slide",
            narrative="Thank you"
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result["use_image_background"] is True
        assert result["visual_style"] == "professional"
```

#### 5.2 Integration Tests - Endpoint Routing

```python
# tests/test_visual_styles/test_endpoint_routing.py (new file)

import pytest
from src.utils.hero_request_transformer import HeroRequestTransformer
from src.models.agents import Slide, PresentationStrawman

class TestEndpointRouting:
    """Test routing to correct -with-image vs regular endpoints."""

    def test_title_with_image_endpoint(self):
        """Title slides with use_image_background route to -with-image endpoint."""
        transformer = HeroRequestTransformer()

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type_classification="title_slide",
            narrative="Welcome",
            use_image_background=True,
            visual_style="professional"
        )

        strawman = PresentationStrawman(main_title="Test")

        result = transformer.transform_to_hero_request(slide, strawman)

        assert result["endpoint"] == "/v1.2/hero/title-with-image"
        assert result["payload"]["visual_style"] == "professional"

    def test_section_without_image_endpoint(self):
        """Section dividers without images route to regular endpoint."""
        transformer = HeroRequestTransformer()

        slide = Slide(
            slide_number=5,
            slide_id="s5",
            title="Section",
            layout_id="L29",
            slide_type_classification="section_divider",
            narrative="New section",
            use_image_background=False,
            visual_style=None
        )

        strawman = PresentationStrawman(main_title="Test")

        result = transformer.transform_to_hero_request(slide, strawman)

        assert result["endpoint"] == "/v1.2/hero/section"
        assert "visual_style" not in result["payload"]

    def test_closing_with_illustrated_style(self):
        """Closing slides with illustrated style route correctly."""
        transformer = HeroRequestTransformer()

        slide = Slide(
            slide_number=10,
            slide_id="s10",
            title="Closing",
            layout_id="L29",
            slide_type_classification="closing_slide",
            narrative="Thank you",
            use_image_background=True,
            visual_style="illustrated"
        )

        strawman = PresentationStrawman(main_title="Test")

        result = transformer.transform_to_hero_request(slide, strawman)

        assert result["endpoint"] == "/v1.2/hero/closing-with-image"
        assert result["payload"]["visual_style"] == "illustrated"
```

#### 5.3 End-to-End Test

```python
# tests/test_visual_styles/test_e2e_visual_styles.py (new file)

import pytest
from tests.test_utils import create_test_session, wait_for_stage

@pytest.mark.asyncio
async def test_e2e_illustrated_presentation():
    """
    End-to-end test: Create presentation with illustrated visual style.

    Tests complete flow:
    1. User requests presentation with illustrated style
    2. Stage 2: Visual style preference captured
    3. Stage 4: All hero slides assigned illustrated style
    4. Stage 6: Routes to -with-image endpoints with visual_style
    5. Text Service generates Ghibli-style backgrounds
    6. Presentation renders with illustrated aesthetics
    """
    session = await create_test_session()

    # Stage 1: Greeting
    await session.send_message("I need a creative presentation about sustainable energy")
    await wait_for_stage(session, "ASK_CLARIFYING_QUESTIONS")

    # Stage 2: Request illustrated style
    await session.send_message(
        "Target audience: investors, 8 slides, "
        "Visual style: illustrated (Ghibli-style), "
        "Use images for all hero slides"
    )
    await wait_for_stage(session, "CREATE_CONFIRMATION_PLAN")

    # Stage 3: Confirmation
    await session.send_message("accept")
    await wait_for_stage(session, "GENERATE_STRAWMAN")

    # Stage 4: Verify visual styles assigned
    strawman = await session.get_strawman()

    title_slide = strawman.slides[0]
    assert title_slide.slide_type_classification == "title_slide"
    assert title_slide.use_image_background is True
    assert title_slide.visual_style == "illustrated"

    # Accept strawman
    await session.send_message("accept")
    await wait_for_stage(session, "CONTENT_GENERATION")

    # Stage 6: Verify routing to -with-image endpoints
    generation_log = await session.get_generation_log()

    title_endpoint = generation_log["slides"][0]["endpoint_used"]
    assert title_endpoint == "/v1.2/hero/title-with-image"

    # Verify presentation generated
    presentation_url = await session.get_presentation_url()
    assert presentation_url is not None

    # Verify slides have illustrated backgrounds
    slides = await session.fetch_slides_from_layout_architect(presentation_url)

    # Title slide should have Ghibli-style background in hero_content
    title_html = slides[0]["content"]["hero_content"]
    assert "<div" in title_html  # Has hero content
    assert len(title_html) > 1000  # Substantial HTML with embedded image
```

---

## File Changes Summary

### New Files (4)

| File | Purpose | Lines (est.) |
|------|---------|--------------|
| `src/models/visual_styles.py` | Visual style data models (VisualStylePreferences, VisualStyleAssignmentRules) | ~80 |
| `src/utils/visual_style_assigner.py` | AI visual style assignment logic with user override | ~200 |
| `tests/test_visual_styles/test_style_assignment.py` | Unit tests for visual style assignment | ~150 |
| `tests/test_visual_styles/test_endpoint_routing.py` | Integration tests for endpoint routing | ~100 |

**Total new lines**: ~530

### Modified Files (5)

| File | Changes | Lines (est.) |
|------|---------|--------------|
| `src/models/agents.py` | Add visual_style, use_image_background to Slide; visual_style_preference to PresentationStrawman | +15 |
| `src/agents/director.py` | Integrate VisualStyleAssigner in Stage 4; parse preferences in Stage 2 | +40 |
| `config/prompts/modular/02_ask_clarifying_questions.md` | Add visual style selection question | +20 |
| `src/utils/hero_request_transformer.py` | Update endpoint routing logic for -with-image variants; add visual_style to payload | +25 |
| `src/utils/service_router_v1_2.py` | Add diagnostic logging for visual styles | +10 |

**Total modified lines**: ~110

### Total Implementation Size

- **New code**: ~530 lines
- **Modified code**: ~110 lines
- **Total**: ~640 lines

**Comparison to BACKGROUND_INTEGRATION_PLAN.md**:
- Original plan: ~1,277 lines (for generic image service integration)
- Visual Style System: ~640 lines (50% less code - more focused solution)
- **Reason**: Reuses Text Service's built-in image generation, no separate Image Service needed

---

## Backward Compatibility

### Guaranteed Compatibility

✅ **100% backward compatible** - All changes are additive and optional:

1. **Slide Model**:
   - `visual_style` and `use_image_background` are optional (defaults: None/False)
   - Existing slides without these fields work unchanged
   - Default routing to regular `/v1.2/hero/*` endpoints (no images)

2. **Text Service v1.2**:
   - `visual_style` parameter defaults to "professional" if omitted
   - Existing requests without `visual_style` work unchanged
   - Backward compatible with all current Director implementations

3. **Endpoint Selection**:
   - If `use_image_background=False`, routes to existing endpoints
   - No breaking changes to current hero slide generation

### Migration Path

**Existing presentations**: No changes required
- Continue using regular hero endpoints
- Gradient backgrounds still work
- Can add visual styles in future iterations

**New presentations**: Automatic visual style assignment
- Title slides get image backgrounds by default
- AI assigns appropriate visual style based on audience/theme
- Users can customize via Stage 2 preferences

---

## Rollout Plan

### Week 1: Core Implementation

**Day 1-2**: Data model extensions
- Create `src/models/visual_styles.py`
- Update `src/models/agents.py` (Slide, PresentationStrawman)
- Add visual_style and use_image_background fields

**Day 3-4**: Visual style assignment logic
- Create `src/utils/visual_style_assigner.py`
- Implement AI default rules
- Add user preference override logic

**Day 5**: Stage 2 integration
- Update clarifying questions prompt
- Add preference parsing in director.py

### Week 2: Service Integration & Routing

**Day 6-7**: Stage 4 integration
- Integrate VisualStyleAssigner into post_process_strawman
- Add assignment logic after variant selection
- Test with mock data

**Day 8-9**: Stage 6 endpoint routing
- Update hero_request_transformer.py
- Add -with-image endpoint logic
- Add visual_style to payload

**Day 10**: Service router enhancements
- Add diagnostic logging
- Test routing decisions
- Verify endpoint selection

### Week 3: Testing & Validation

**Day 11-12**: Unit tests
- Test visual style assignment rules
- Test AI defaults vs user preferences
- Test endpoint routing logic

**Day 13-14**: Integration tests
- Test Stage 4 → Stage 6 flow
- Test with Text Service v1.2 (local)
- Verify -with-image endpoints work

**Day 15**: End-to-end testing
- Complete presentation generation test
- All three visual styles (professional, illustrated, kids)
- Verify costs and generation times

### Week 4: Production Deployment

**Day 16-17**: Code review & documentation
- Team code review
- Update README.md
- Create user guide

**Day 18**: Staging deployment
- Deploy to staging environment
- QA testing with real presentations
- Performance monitoring

**Day 19**: Production deployment
- Deploy to production
- Monitor generation metrics
- Gather user feedback

**Day 20**: Post-deployment
- Bug fixes if needed
- Performance optimization
- Documentation updates

---

## Success Metrics

### Feature Completeness
- [ ] Title slides ALWAYS use image backgrounds
- [ ] Section/closing slides configurable for images
- [ ] Three visual styles (professional, illustrated, kids) functional
- [ ] AI assigns appropriate defaults based on audience/theme
- [ ] User preferences override AI defaults correctly
- [ ] Cost optimization working (fast models for illustrated/kids)

### Technical Quality
- [ ] 100% backward compatibility maintained
- [ ] Test coverage >90% for visual style logic
- [ ] All endpoints route correctly (-with-image vs regular)
- [ ] visual_style parameter passed to Text Service
- [ ] No breaking changes to existing presentations

### Performance & Cost
- [ ] Title + Professional: $0.04 (standard model)
- [ ] Title + Illustrated/Kids: $0.02 (fast model)
- [ ] Section/Closing: $0.02 (all styles, fast model)
- [ ] Generation time: <10s for title, <5s for section/closing
- [ ] Cost savings: 17% with illustrated/kids vs professional

### User Experience
- [ ] Clear visual style options in Stage 2
- [ ] Natural language parsing of preferences
- [ ] "Let AI decide" option works correctly
- [ ] Generated images match selected visual style
- [ ] End-to-end test passes with 8-slide presentation

---

## Open Questions

### 1. Default Image Usage for Section/Closing Slides

**Question**: Should section dividers and closing slides use image backgrounds by default?

**Current Plan**:
- Title: ALWAYS images (user requirement)
- Section: No images by default (only for creative themes or user request)
- Closing: Images by default (for memorable impact)

**Recommendation**: Validate with product/design team.

### 2. Visual Style Persistence

**Question**: Should visual style be stored with saved presentations for consistency?

**Consideration**: If a presentation is regenerated or edited, should it maintain the same visual style?

**Recommendation**: Yes - store visual_style in presentation metadata for consistency.

### 3. Mixed Visual Styles

**Question**: Can users mix visual styles within a single presentation?

**Current Plan**: Single visual style applies to all hero slides.

**Future Enhancement**: Allow per-slide visual style specification.

### 4. Cost Alerting

**Question**: Should we alert users about cost differences between visual styles?

**Consideration**: Professional title slides cost 2x more than illustrated/kids.

**Recommendation**: Display cost information in Stage 2 clarifying questions.

---

## Next Steps

1. **Review this plan** with Director, Text Service, and Layout Builder teams
2. **Confirm default image usage** for section/closing slides
3. **Validate cost assumptions** with actual generation metrics
4. **Begin Week 1 implementation** (data models)
5. **Set up testing infrastructure** for visual styles
6. **Update BACKGROUND_INTEGRATION_PLAN.md** (mark as superseded by this plan)

---

## References

### Text Service v1.2 Documentation
- Visual Style System: `/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/text_table_builder/v1.2/test_outputs/VISUAL_STYLE_SYSTEM_IMPLEMENTATION.md`
- Hero Endpoints: Text Service v1.2 API documentation
- Image Generation: Imagen 3.0 integration details

### Director Agent Architecture
- Director Agent: `src/agents/director.py` (lines 384-633)
- Slide Model: `src/models/agents.py` (lines 96-239)
- Hero Transformer: `src/utils/hero_request_transformer.py` (lines 42-127)
- Service Router: `src/utils/service_router_v1_2.py` (lines 430-499)

### Related Documentation
- Background Integration Plan: `docs/BACKGROUND_INTEGRATION_PLAN.md` (superseded)
- V3.4 Implementation Plan: `docs/V3.4_IMPLEMENTATION_PLAN.md`
- README: `README.md`

---

**Document Status**: ✅ Ready for Review
**Last Updated**: 2025-01-26
**Version**: 1.0
**Author**: Director Team
**Reviewers**: Text Service Team, Layout Builder Team

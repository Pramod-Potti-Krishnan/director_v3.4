# Director Agent v3.4 - Architecture Documentation

## Executive Summary

Director Agent v3.4 implements a **6-stage state machine** that orchestrates complete presentation generation from initial greeting to final content generation. The key innovation in v3.4 is **Stage 6 (CONTENT_GENERATION)**, which integrates with Text Service v1.2 to automatically generate visually stunning slide content.

**Key Architectural Achievements:**
- ✅ **6-stage workflow**: Greeting → Questions → Plan → Strawman → Refinement → **Content Generation**
- ✅ **Text Service v1.2 integration**: Seamless routing to hero and content endpoints
- ✅ **Service Router**: Intelligent endpoint selection based on slide classification
- ✅ **Content Transformer**: Maps generated content to L25/L29 layout formats
- ✅ **Hero Request Transformer**: Builds rich context for hero slide generation
- ✅ **Real-time updates**: WebSocket progress notifications during content generation
- ✅ **End-to-end automation**: From user request to presentation URL

---

## Architecture Philosophy

### Design Principles

1. **State-Driven Workflow**: Each stage has clear inputs, processing, and outputs
2. **Service Orchestration**: Director coordinates multiple services (Text, Layout, Supabase)
3. **Separation of Concerns**: Content generation delegated to specialized Text Service
4. **Format Ownership**: Text Service owns HTML generation, Director handles orchestration
5. **Real-time Feedback**: Users see progress updates as content generates
6. **Error Resilience**: Graceful handling of service failures with partial results

### Why 6 Stages?

| Stage | Purpose | AI Complexity | Service Integration |
|-------|---------|---------------|---------------------|
| 1. PROVIDE_GREETING | Set context | Low | None |
| 2. ASK_CLARIFYING_QUESTIONS | Gather requirements | Medium | None |
| 3. CREATE_CONFIRMATION_PLAN | Propose structure | High | None |
| 4. GENERATE_STRAWMAN | Create outline with classifications | High | None |
| 5. REFINE_STRAWMAN | Iterative improvement | High | None |
| 6. **CONTENT_GENERATION** | **Generate visual content** | **Orchestration** | **Text v1.2, Layout** |

**Rationale**: Stage 6 is fundamentally different—it's **orchestration** not **generation**. Director routes to Text Service v1.2, which handles actual content generation using its dual architecture (element-based for content, single-call for heroes).

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Director Agent v3.4                          │
│                    (6-Stage State Machine)                      │
├─────────────────────────────────────────────────────────────────┤
│  Stages 1-5: Requirements → Strawman (Conversational AI)       │
│  Stage 6: Content Generation (Service Orchestration)           │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
     ┌───────────────┐
     │  User accepts │
     │   strawman    │
     └───────┬───────┘
             │
             ▼
┌────────────────────────────────────────────────────────────────┐
│              STAGE 6: CONTENT_GENERATION                       │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  For each slide in strawman:                                   │
│                                                                 │
│    1. Classify Slide Type                                      │
│       ├─ Hero? (title/section/closing)                         │
│       └─ Content? (matrix/grid/table/etc)                      │
│                                                                 │
│    2. Build Request (Service Router)                           │
│       ├─ Hero → hero_request_transformer.py                    │
│       └─ Content → build_content_request()                     │
│                                                                 │
│    3. Call Text Service v1.2                                   │
│       ├─ Hero → POST /v1.2/hero/{type}                         │
│       └─ Content → POST /v1.2/generate                         │
│                                                                 │
│    4. Transform Content (content_transformer.py)               │
│       ├─ Hero → L29 format (complete inline HTML)             │
│       └─ Content → L25 format (rich_content mapping)          │
│                                                                 │
│    5. Send to Layout Architect                                 │
│       └─ Render slide and return URL                           │
│                                                                 │
└────────────┬───────────────────────────────────────────────────┘
             │
             ▼
     ┌───────────────┐
     │  Presentation │
     │      URL      │
     └───────────────┘
```

---

## Stage 6: Content Generation Deep Dive

### Component Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Director Agent (Stage 6 Entry Point)                       │
│  src/agents/director.py → _handle_content_generation()      │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│  Service Router v1.2                                         │
│  src/utils/service_router_v1_2.py                           │
│                                                               │
│  route_slide_to_text_service(slide, context) →              │
│    ├─ Classify: Hero or Content?                            │
│    ├─ Build Request:                                         │
│    │   ├─ Hero → hero_request_transformer.transform()       │
│    │   └─ Content → build_content_request()                 │
│    ├─ Select Endpoint:                                       │
│    │   ├─ title_slide → POST /v1.2/hero/title              │
│    │   ├─ section_divider → POST /v1.2/hero/section        │
│    │   ├─ closing_slide → POST /v1.2/hero/closing          │
│    │   └─ content slides → POST /v1.2/generate             │
│    └─ Return: {"content": "HTML", "metadata": {...}}        │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│  Text Service v1.2 (Railway)                                 │
│  https://web-production-5daf.up.railway.app                  │
│                                                               │
│  Hero Endpoints:                                             │
│    ├─ /v1.2/hero/title → TitleSlideGenerator                │
│    ├─ /v1.2/hero/section → SectionDividerGenerator          │
│    └─ /v1.2/hero/closing → ClosingSlideGenerator            │
│                                                               │
│  Content Endpoint:                                           │
│    └─ /v1.2/generate → ElementBasedContentGenerator         │
│                                                               │
│  Returns: {"content": "HTML", "metadata": {...}}             │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│  Content Transformer                                         │
│  src/utils/content_transformer.py                           │
│                                                               │
│  map_content_to_layout_format(content, layout_id) →         │
│    ├─ L29 (Hero): _map_hero_slide()                         │
│    │   └─ {"hero_content": complete_inline_html}            │
│    └─ L25 (Content): _map_content_slide()                   │
│        └─ {"rich_content": html_string}                      │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
┌──────────────────────────────────────────────────────────────┐
│  Layout Architect                                            │
│  http://localhost:8504                                       │
│                                                               │
│  POST /render-slide                                          │
│    Input: layout_id, hero_content or rich_content           │
│    Output: rendered slide URL                                │
└────────────┬─────────────────────────────────────────────────┘
             │
             ▼
        Final Slide URL
```

---

## Key Components

### 1. Service Router v1.2 (`src/utils/service_router_v1_2.py`)

**Responsibility**: Route slides to appropriate Text Service v1.2 endpoints

**Classification Logic**:
```python
HERO_CLASSIFICATIONS = {"title_slide", "section_divider", "closing_slide"}

def is_hero_slide(classification: str) -> bool:
    return classification in HERO_CLASSIFICATIONS
```

**Endpoint Routing**:
```python
if is_hero_slide(classification):
    # Hero slides → /v1.2/hero/{type}
    hero_type = classification.replace("_slide", "").replace("_divider", "")
    endpoint = f"{TEXT_SERVICE_URL}/v1.2/hero/{hero_type}"
    payload = hero_request_transformer.transform_to_hero_request(slide, context)
else:
    # Content slides → /v1.2/generate
    endpoint = f"{TEXT_SERVICE_URL}/v1.2/generate"
    payload = build_content_request(slide, context)
```

**Response Packaging** (CRITICAL DESIGN):
```python
# FLAT STRUCTURE - consistent for hero and content
return {
    "slide_number": slide.slide_number,
    "slide_id": slide.slide_id,
    "content": response["content"],      # HTML string directly
    "metadata": response["metadata"]     # Top-level metadata
}
```

**Why Flat Structure?**: Early v3.4 bug: hero slides used nested `{"content": {"html": "...", "metadata": {}}}` while content slides used flat structure. This caused `content_transformer.py` to fail extracting hero HTML → blank slides. Fixed by making both flat.

---

### 2. Hero Request Transformer (`src/utils/hero_request_transformer.py`)

**Responsibility**: Build hero endpoint request payloads with rich context

**Transformation**:
```python
def transform_to_hero_request(slide: Slide, context: Dict) -> Dict:
    """Transform Director slide to hero endpoint format."""

    return {
        "slide_number": slide.slide_number,
        "slide_type": slide.classification,
        "narrative": slide.narrative or context.get("narrative", ""),
        "topics": slide.topics or context.get("topics", []),
        "context": {
            "theme": context.get("theme", "professional"),
            "audience": context.get("audience", "business stakeholders"),
            "presentation_title": context.get("presentation_title", ""),
            "contact_info": context.get("contact_info", "")  # For closing slides
        }
    }
```

**Context Enrichment**:
- **Narrative**: Core message or purpose of the slide (from strawman)
- **Topics**: Key topics to cover (from strawman or presentation context)
- **Theme**: Visual theme selection (professional/bold/warm/navy)
- **Audience**: Target audience for tone and language
- **Presentation Title**: Used in title slide generation
- **Contact Info**: Used in closing slide generation

**Why Rich Context?**: Hero slides need holistic understanding to generate compelling titles, transitions, and CTAs. Element-based generation would lose this cohesion.

---

### 3. Content Transformer (`src/utils/content_transformer.py`)

**Responsibility**: Map generated content to layout-specific formats

**Layout Format Mapping**:

#### L29 (Hero Slides)
```python
def _map_hero_slide(content: Any, layout_id: str) -> Dict:
    """Map hero slide content to L29 layout format."""

    # Extract complete inline-styled HTML
    if isinstance(content, str):
        html = content  # Direct HTML string
    elif isinstance(content, dict):
        # Legacy support for nested structures
        html = content.get("hero_content") or content.get("rich_content") or ""
    else:
        html = ""

    return {
        "layout_id": "L29",
        "hero_content": html,  # Complete inline HTML with gradients
        "metadata": {
            "layout_type": "hero",
            "generation_source": "text_service_v1.2"
        }
    }
```

**Key Insight**: Hero HTML is **self-contained** with all styling inline. No further processing needed. Pass directly to layout architect.

#### L25 (Content Slides)
```python
def _map_content_slide(content: Any, layout_id: str, variant_id: str) -> Dict:
    """Map content slide to L25 layout format."""

    # Extract HTML string
    if isinstance(content, str):
        html = content
    elif isinstance(content, dict):
        html = content.get("rich_content") or content.get("html") or ""
    else:
        html = ""

    return {
        "layout_id": "L25",
        "variant_id": variant_id,  # matrix_2x2, grid_3x2, etc.
        "rich_content": html,      # Assembled template HTML
        "metadata": {
            "layout_type": "content",
            "generation_source": "text_service_v1.2",
            "element_count": content.get("metadata", {}).get("element_count", 0)
        }
    }
```

**Key Insight**: Content HTML is **deterministically assembled** from templates. Director just passes it through with layout metadata.

---

## Data Flow: Slide Generation

### Hero Slide Generation Flow (Title Slide Example)

```
┌─────────────────────────────────────────────────────────────┐
│  Director: Slide Classification                             │
│  classification = "title_slide"                             │
│  layout_id = "L29"                                          │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Hero Request Transformer                                   │
│  {                                                           │
│    "slide_number": 1,                                       │
│    "slide_type": "title_slide",                             │
│    "narrative": "AI transforming healthcare diagnostics",   │
│    "topics": ["Machine Learning", "Patient Outcomes"],      │
│    "context": {                                             │
│      "theme": "professional",                               │
│      "audience": "healthcare professionals",                │
│      "presentation_title": "AI in Healthcare"               │
│    }                                                         │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Router → POST /v1.2/hero/title                     │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Text Service v1.2: TitleSlideGenerator                     │
│  1. Build rich v1.1-style prompt                            │
│  2. Single Flash LLM call                                   │
│  3. Generate complete inline HTML:                          │
│     <div style="background: linear-gradient(135deg,         │
│       #4facfe 0%, #00f2fe 100%); display: flex; ...">       │
│       <h1 style="font-size: 96px; color: white; ...">       │
│         AI in Healthcare: Transforming Diagnostics          │
│       </h1>                                                  │
│       <p style="font-size: 42px; ...">...</p>               │
│       <div style="font-size: 32px; ...">...</div>           │
│     </div>                                                   │
│  4. Validate inline styles (gradient, 96px fonts)           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Router Response                                    │
│  {                                                           │
│    "content": "<div style='background: linear-gradient...'>",│
│    "metadata": {                                            │
│      "slide_type": "title_slide",                           │
│      "validation": {"valid": true, ...}                     │
│    }                                                         │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Content Transformer → L29 Format                           │
│  {                                                           │
│    "layout_id": "L29",                                      │
│    "hero_content": "<div style='background: linear...'>",   │
│    "metadata": {"layout_type": "hero", ...}                 │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layout Architect → POST /render-slide                      │
│  Renders L29 hero layout with inline HTML                   │
│  Returns: {"slide_url": "http://..."}                       │
└─────────────────────────────────────────────────────────────┘
```

### Content Slide Generation Flow (Matrix 2×2 Example)

```
┌─────────────────────────────────────────────────────────────┐
│  Director: Slide Classification                             │
│  classification = "matrix_2x2"                              │
│  layout_id = "L25"                                          │
│  variant_id = "matrix_2x2"                                  │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Router → Build Content Request                     │
│  {                                                           │
│    "variant_id": "matrix_2x2",                              │
│    "slide_spec": {                                          │
│      "slide_title": "Four Pillars of AI Excellence",       │
│      "slide_purpose": "Present core AI capabilities",      │
│      "key_message": "Speed, accuracy, scale, insight"      │
│    },                                                        │
│    "presentation_spec": {                                   │
│      "presentation_title": "AI in Healthcare",             │
│      "current_slide_number": 2,                             │
│      "total_slides": 3                                      │
│    },                                                        │
│    "enable_parallel": true                                  │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Router → POST /v1.2/generate                       │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Text Service v1.2: ElementBasedContentGenerator            │
│  1. Load matrix_2x2.json variant spec                       │
│  2. Extract 4 text_box elements                             │
│  3. Build 4 element prompts with context                    │
│  4. Generate 4 elements in PARALLEL (Flash model)           │
│     ├─ box_1: {"title": "Speed", "description": "..."}     │
│     ├─ box_2: {"title": "Accuracy", "description": "..."}  │
│     ├─ box_3: {"title": "Scale", "description": "..."}     │
│     └─ box_4: {"title": "Insight", "description": "..."}   │
│  5. Load matrix_2x2.html template                           │
│  6. Assemble: replace placeholders with element content     │
│  7. Validate: character counts, structure                   │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Service Router Response                                    │
│  {                                                           │
│    "content": "<div class='matrix-layout'>...</div>",       │
│    "metadata": {                                            │
│      "variant_id": "matrix_2x2",                            │
│      "element_count": 4,                                    │
│      "generation_mode": "parallel"                          │
│    }                                                         │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Content Transformer → L25 Format                           │
│  {                                                           │
│    "layout_id": "L25",                                      │
│    "variant_id": "matrix_2x2",                              │
│    "rich_content": "<div class='matrix-layout'>...</div>",  │
│    "metadata": {"layout_type": "content", ...}              │
│  }                                                           │
└───────────────────┬─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────────────────────────┐
│  Layout Architect → POST /render-slide                      │
│  Renders L25 content layout with rich_content               │
│  Returns: {"slide_url": "http://..."}                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Points

### 1. Text Service v1.2 API Contract

**Base URL**: `https://web-production-5daf.up.railway.app`

#### Hero Endpoints

**POST `/v1.2/hero/title`**
```json
Request: {
  "slide_number": 1,
  "slide_type": "title_slide",
  "narrative": "Core message",
  "topics": ["Topic1", "Topic2"],
  "context": {
    "theme": "professional",
    "audience": "executives",
    "presentation_title": "Presentation Name"
  }
}

Response: {
  "content": "<div style='width: 100%; height: 100%; background: linear-gradient...'>...</div>",
  "metadata": {
    "slide_type": "title_slide",
    "validation": {"valid": true, "violations": [], "metrics": {...}},
    "generation_mode": "hero_slide_async"
  }
}
```

**POST `/v1.2/hero/section`**
```json
Request: {
  "slide_number": 5,
  "slide_type": "section_divider",
  "narrative": "Transitioning to implementation",
  "topics": ["Planning", "Deployment"],
  "context": {"theme": "professional"}
}

Response: {
  "content": "<div style='background: #1f2937; ...'>...</div>",
  "metadata": {...}
}
```

**POST `/v1.2/hero/closing`**
```json
Request: {
  "slide_number": 10,
  "slide_type": "closing_slide",
  "narrative": "Call to action",
  "topics": ["Next Steps", "Contact"],
  "context": {
    "theme": "professional",
    "contact_info": "email@company.com | www.company.com"
  }
}

Response: {
  "content": "<div style='background: linear-gradient...'>...</div>",
  "metadata": {...}
}
```

#### Content Endpoint

**POST `/v1.2/generate`**
```json
Request: {
  "variant_id": "matrix_2x2",
  "slide_spec": {
    "slide_title": "Our Core Values",
    "slide_purpose": "Communicate company values",
    "key_message": "Innovation, growth, success, empowerment"
  },
  "presentation_spec": {
    "presentation_title": "Q4 Business Review",
    "current_slide_number": 5,
    "total_slides": 20
  },
  "enable_parallel": true
}

Response: {
  "success": true,
  "html": "<div class='matrix-layout'>...</div>",
  "elements": [{element_id, generated_content, character_counts}, ...],
  "metadata": {
    "variant_id": "matrix_2x2",
    "element_count": 4,
    "generation_mode": "parallel"
  }
}
```

**Key Difference**: Content endpoint returns `{"html": "..."}` but service router extracts to `{"content": "..."}` for consistency.

---

### 2. Layout Architect API Contract

**Base URL**: `http://localhost:8504`

**POST `/render-slide`**

For L29 (Hero):
```json
Request: {
  "layout_id": "L29",
  "hero_content": "<div style='background: linear-gradient...'>...</div>",
  "metadata": {
    "layout_type": "hero",
    "generation_source": "text_service_v1.2"
  }
}

Response: {
  "slide_url": "http://localhost:8504/slides/abc123.html"
}
```

For L25 (Content):
```json
Request: {
  "layout_id": "L25",
  "variant_id": "matrix_2x2",
  "rich_content": "<div class='matrix-layout'>...</div>",
  "metadata": {
    "layout_type": "content",
    "generation_source": "text_service_v1.2"
  }
}

Response: {
  "slide_url": "http://localhost:8504/slides/def456.html"
}
```

---

## Error Handling & Resilience

### Service Failure Handling

**Text Service Unavailable**:
```python
try:
    response = await async_post(text_service_url, payload)
except httpx.RequestError as e:
    logger.error(f"Text Service unavailable: {e}")
    return {
        "status": "error",
        "slide_number": slide.slide_number,
        "error": "Text Service unavailable",
        "fallback": "Continue with remaining slides"
    }
```

**Layout Architect Unavailable**:
```python
try:
    response = await async_post(layout_architect_url, payload)
except httpx.RequestError as e:
    logger.error(f"Layout Architect unavailable: {e}")
    return {
        "status": "error",
        "slide_number": slide.slide_number,
        "error": "Layout Architect unavailable"
    }
```

**Partial Success Strategy**:
- Continue processing remaining slides if one fails
- Track successful_slides and failed_slides counts
- Return presentation URL even with partial failures
- Include error details in metadata

**Example Partial Result**:
```json
{
  "type": "presentation_url",
  "url": "http://localhost:8504/p/abc123",
  "slide_count": 5,
  "successful_slides": 4,
  "failed_slides": 1,
  "message": "Presentation ready with 4 of 5 slides"
}
```

---

### Validation Failure Handling

**Hero Slide Validation Failure**:
- Text Service returns content with `validation.valid = false`
- Director logs warning but uses content anyway
- Better imperfect HTML than no HTML

**Content Slide Validation Failure**:
- Element character count violations logged
- Generation continues (retry logic planned for future)
- Validation metadata included for debugging

---

## Performance Characteristics

### Stage 6 Benchmarks

**3-Slide Presentation** (title + matrix_2x2 + closing):
- Total time: ~9-12 seconds
- Breakdown:
  - Title slide (hero): ~1.2s (single Flash call)
  - Matrix 2×2 (content): ~1.5s (4 parallel Flash calls + assembly)
  - Closing slide (hero): ~1.2s (single Flash call)
  - Layout rendering: ~5-8s (3 slides rendered)

**Per-Slide Times**:
| Slide Type | Generation | Rendering | Total |
|------------|-----------|-----------|-------|
| Hero (title/closing) | ~1.2s | ~2s | ~3.2s |
| Content (matrix_2x2) | ~1.5s | ~2s | ~3.5s |
| Content (grid_3x2) | ~2.0s | ~2s | ~4.0s |
| Content (table_4col) | ~2.5s | ~2s | ~4.5s |

**Scalability**:
- **10-slide deck**: ~45-60 seconds
- **20-slide deck**: ~90-120 seconds
- Linear scaling with slide count (parallel generation within slides)

---

## Design Decisions & Rationale

### 1. Why Separate Hero and Content Routing?

**Decision**: Route hero slides to `/v1.2/hero/*` and content to `/v1.2/generate`

**Rationale**:
- Hero slides need holistic context (narrative, themes, full presentation title)
- Content slides need structured specs (variant_id, element-level context)
- Text Service uses different architectures (single-call vs element-based)
- Forcing both through same endpoint would require complex branching

**Outcome**: Clean separation of concerns, optimal generation for each type

### 2. Why Flat Response Structure?

**Decision**: Both hero and content return `{"content": "HTML", "metadata": {...}}`

**Rationale**:
- Early bug: hero used nested `{"content": {"html": "...", "metadata": {}}}` → blank slides
- Content transformer expected flat structure
- Inconsistency caused extraction failures
- Flattening fixed the issue

**Outcome**: Reliable content extraction regardless of slide type

### 3. Why Hero Request Transformer?

**Decision**: Create dedicated transformer for hero payloads

**Rationale**:
- Hero endpoints have different schema than content endpoint
- Need to extract narrative, topics from slide object
- Need to enrich with presentation-level context (theme, audience)
- Reusable logic across all 3 hero endpoints

**Outcome**: DRY code, consistent hero request formatting

### 4. Why Content Transformer?

**Decision**: Transform Text Service responses to layout-specific formats

**Rationale**:
- Layout Architect expects different schemas for L25 vs L29
- L29 needs `hero_content` key with complete HTML
- L25 needs `rich_content` key with assembled HTML
- Variant information needed for L25
- Abstraction layer if layout formats change

**Outcome**: Decoupling between Text Service and Layout Architect

### 5. Why Real-Time Progress Updates?

**Decision**: Send WebSocket messages for each slide generated

**Rationale**:
- Content generation takes 9-120+ seconds
- User needs feedback that work is happening
- Shows which slide is currently generating
- Builds anticipation and engagement

**Outcome**: Better UX, no "black box" waiting period

### 6. Why Parallel Slide Generation?

**Decision**: Use `asyncio.gather()` to generate all slides concurrently

**Rationale**:
- Slides are independent (can generate in any order)
- Text Service can handle concurrent requests
- 3-5x faster than sequential generation
- Layout rendering still sequential (could parallelize in future)

**Outcome**: Significantly faster presentation generation

---

## Future Enhancements

### Short-Term (Next 3 Months)

1. **Parallel Layout Rendering**
   - Currently sequential (slide 1 → slide 2 → slide 3)
   - Can parallelize if Layout Architect supports concurrent requests
   - Potential 2-3x speedup on rendering

2. **Slide Generation Retry Logic**
   - Auto-retry failed slides with exponential backoff
   - Max 2 retries per slide
   - Fallback to placeholder content if all retries fail

3. **Content Caching**
   - Cache generated content by (variant_id, context_hash)
   - Deduplicate similar slides in same presentation
   - Significant speedup for repetitive content

4. **Progress Granularity**
   - Show element-level progress for content slides
   - "Generating box 2 of 4 for slide 5..."
   - More engaging for users

### Long-Term (6-12 Months)

1. **Streaming Content Generation**
   - Stream partial HTML as it generates
   - Show slides filling in element-by-element
   - More engaging visual feedback

2. **A/B Testing Framework**
   - Generate multiple variants per slide
   - Let user choose preferred version
   - Learn preferences over time

3. **Smart Content Reuse**
   - Identify similar slides across presentations
   - Suggest reusing content with adjustments
   - "You've created 3 similar 'About Us' slides—reuse one?"

4. **Multi-Model Generation**
   - Use different LLMs for different slide types
   - GPT-4 for complex tables, Claude for creative heroes
   - Dynamic model selection based on content type

---

## Testing Strategy

### Unit Tests

**Component-Level Tests**:
- `service_router_v1_2.py`: Endpoint selection, payload building, response packaging
- `hero_request_transformer.py`: Context extraction, payload formatting
- `content_transformer.py`: L25/L29 format mapping, HTML extraction

### Integration Tests

**Stage 6 Full Workflow**:
```bash
python3 tests/stage6_only/test_content_generation.py
```

Tests:
- 3-slide presentation (title + matrix_2x2 + closing)
- Hero endpoint routing
- Content endpoint routing
- Layout Architect integration
- Presentation URL generation

### End-to-End Tests

**Complete 6-Stage Flow**:
1. Start Director WebSocket connection
2. Progress through stages 1-5 (greeting → strawman)
3. Accept strawman
4. Verify Stage 6 executes
5. Verify presentation URL returned
6. Verify slides render correctly

### Performance Tests

**Load Testing**:
```bash
# Generate 10 presentations concurrently
python3 tests/load/test_concurrent_generation.py --count 10
```

**Metrics Tracked**:
- P50, P95, P99 latency per slide type
- Total presentation generation time
- Text Service response times
- Layout Architect response times
- Error rates

---

## Monitoring & Observability

### Logging Strategy

**Stage 6 Entry**:
```python
logger.info(f"Stage 6: Starting content generation for {len(slides)} slides")
```

**Per-Slide Logging**:
```python
logger.info(f"Generating slide {slide_num}/{total}: {classification} ({layout_id})")
logger.info(f"Routing to: {endpoint}")
logger.info(f"Text Service response: {response.status_code}")
logger.info(f"Content length: {len(content)} chars")
```

**Error Logging**:
```python
logger.error(f"Slide {slide_num} generation failed: {error}")
logger.warning(f"Validation failures: {validation['violations']}")
```

### Metrics to Track

**Stage 6 Metrics**:
- Total presentations generated
- Average presentation generation time
- Slides per presentation (distribution)
- Success rate (% presentations with 0 failures)
- Partial success rate (% with 1+ failures but not all)

**Per-Slide Metrics**:
- Hero slide generation time (avg, p95, p99)
- Content slide generation time by variant
- Layout rendering time by layout_id
- Error rates by slide type

**Service Health Metrics**:
- Text Service availability (% uptime)
- Text Service response time (avg, p95, p99)
- Layout Architect availability
- Layout Architect response time

---

## Conclusion

Director Agent v3.4's Stage 6 (CONTENT_GENERATION) successfully orchestrates end-to-end presentation generation by:

✅ **Intelligent routing** to Text Service v1.2's dual architecture
✅ **Seamless integration** with hero and content endpoints
✅ **Format transformation** for L25/L29 layouts
✅ **Real-time feedback** via WebSocket progress updates
✅ **Error resilience** with partial success handling
✅ **Performance optimization** through parallel generation

The architecture is **production-ready**, **scalable**, and **maintainable**, providing users with complete, visually stunning presentations from a single conversational workflow.

---

**Document Version**: 1.0
**Last Updated**: December 2025
**Maintainer**: Deckster Engineering Team

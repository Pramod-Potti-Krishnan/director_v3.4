# Illustrator Service Integration Plan
**Director Agent v3.4 → Illustrator Service v1.0**

**Document Version**: 1.0
**Date**: January 15, 2025
**Status**: Planning Phase

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Analysis](#architecture-analysis)
3. [Integration Strategy](#integration-strategy)
4. [Component Design](#component-design)
5. [Implementation Phases](#implementation-phases)
6. [Testing Strategy](#testing-strategy)
7. [Future Extensibility](#future-extensibility)

---

## Executive Summary

### Objective

Integrate the **Illustrator Service v1.0** into Director Agent v3.4 to enable AI-powered pyramid diagram generation as a slide variant option.

### Key Requirements

1. **Stage 4 (GENERATE_STRAWMAN)**: Pyramid available as selectable slide type
2. **Stage 5 (REFINE_STRAWMAN)**: Users can refine pyramid configuration
3. **Stage 6 (CONTENT_GENERATION)**: Director calls Illustrator API to generate pyramid HTML
4. **Extensibility**: Architecture must support future visualizations (funnel, SWOT, BCG matrix, etc.)

### Success Criteria

- ✅ LLM can select "pyramid" as a slide type in Stage 4
- ✅ Director routes pyramid slides to Illustrator service in Stage 6
- ✅ Pyramid HTML embeds correctly in L25 layout
- ✅ Architecture supports adding new Illustrator endpoints without major refactoring

---

## Architecture Analysis

### Current Director Architecture

**Slide Type Taxonomy (13 types)**:

**Text Service Types (10)**:
- bilateral_comparison, matrix_2x2, sequential_3col, asymmetric_8_4
- hybrid_1_2x2, single_column, impact_quote, metrics_grid
- styled_table, grid_3x3

**Hero Types (3)**:
- title_slide, section_divider, closing_slide

**Service Routing (Stage 6)**:
- Hero slides → Text Service `/v1.2/hero/{type}`
- Content slides → Text Service `/v1.2/generate`

### Integration Challenges

| Challenge | Impact | Solution |
|-----------|--------|----------|
| **Variant Discovery** | How does LLM know pyramid exists? | Update Stage 4 prompts with pyramid description |
| **Service Routing** | How to route pyramid to Illustrator vs Text Service? | Service Registry pattern |
| **Extensibility** | How to add funnel, SWOT, BCG without refactoring? | Centralized service configuration |
| **Classification** | Where does pyramid fit in taxonomy? | New "Illustrator Types" category |
| **Data Transformation** | How to handle pyramid-specific config? | Extend slide schema with visualization_config |

---

## Integration Strategy

### Recommended Approach: Service-Based Taxonomy

**Create a new category of slide types managed by Illustrator service.**

#### Why This Approach?

1. **Clear Separation**: Text Service owns text-based layouts, Illustrator owns visualizations
2. **Scalability**: Adding funnel/SWOT/BCG is just adding to the list
3. **Service Routing**: Simple lookup: `slide_type → service → endpoint`
4. **Maintainability**: Each service owns its slide types

### Updated Slide Type Taxonomy

**Total: 14 types → expanding to 20+ types**

```
Text Service Types (10): bilateral_comparison, matrix_2x2, sequential_3col, ...
Illustrator Types (1+):  pyramid, [funnel], [swot], [bcg_matrix], [gantt], [org_chart]
Hero Types (3):          title_slide, section_divider, closing_slide
```

### Stage 4 Strawman Schema Extension

**Current Schema**:
```json
{
  "slide_number": 3,
  "slide_id": "slide-3",
  "title": "Market Analysis",
  "slide_type": "matrix_2x2",
  "narrative": "...",
  "key_points": [...],
  "layout_id": "L25"
}
```

**Extended Schema (with pyramid)**:
```json
{
  "slide_number": 3,
  "slide_id": "slide-3",
  "title": "Organizational Hierarchy",
  "slide_type": "pyramid",
  "narrative": "Showing clear hierarchy from execution to vision",
  "key_points": ["Execution", "Operations", "Strategy", "Vision"],
  "layout_id": "L25",
  "visualization_config": {
    "pyramid_levels": 4,
    "tone": "professional",
    "audience": "executives"
  }
}
```

**New Field**:
- `visualization_config`: Optional dictionary for visualization-specific parameters

### Service Routing Logic

**Stage 6 Content Generation Flow**:

```
For each slide in strawman:
    ↓
1. Extract slide_type
    ↓
2. Lookup service in Service Registry
    ↓
3. Route to appropriate service:
    - pyramid → Illustrator API
    - matrix_2x2 → Text Service API
    - title_slide → Hero API
    ↓
4. Transform response to Layout Builder format
    ↓
5. Send to Layout Builder
```

---

## Component Design

### 1. Service Registry (`src/utils/service_registry.py`)

**Purpose**: Central configuration for all content generation services

**Design**:

```python
"""
Service Registry for Director Agent v3.4
Maps slide types to content generation services and their endpoints.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel

class ServiceEndpoint(BaseModel):
    """Configuration for a service endpoint"""
    path: str
    method: str = "POST"
    timeout: int = 60

class ServiceConfig(BaseModel):
    """Configuration for a content generation service"""
    enabled: bool
    base_url: str
    slide_types: List[str]
    endpoints: Dict[str, ServiceEndpoint] = {}

# Service Registry
SERVICE_REGISTRY = {
    "text_service": ServiceConfig(
        enabled=True,
        base_url="https://web-production-5daf.up.railway.app",
        slide_types=[
            "bilateral_comparison",
            "matrix_2x2",
            "sequential_3col",
            "asymmetric_8_4",
            "hybrid_1_2x2",
            "single_column",
            "impact_quote",
            "metrics_grid",
            "styled_table",
            "grid_3x3"
        ]
    ),
    "illustrator_service": ServiceConfig(
        enabled=True,
        base_url="http://localhost:8000",  # From settings
        slide_types=[
            "pyramid",
            # Future: "funnel", "swot", "bcg_matrix", "gantt", "org_chart"
        ],
        endpoints={
            "pyramid": ServiceEndpoint(
                path="/v1.0/pyramid/generate",
                method="POST",
                timeout=60
            )
            # Future endpoints will be added here
        }
    ),
    "hero_service": ServiceConfig(
        enabled=True,
        base_url="https://web-production-5daf.up.railway.app",
        slide_types=[
            "title_slide",
            "section_divider",
            "closing_slide"
        ],
        endpoints={
            "title": ServiceEndpoint(path="/v1.2/hero/title"),
            "section": ServiceEndpoint(path="/v1.2/hero/section"),
            "closing": ServiceEndpoint(path="/v1.2/hero/closing")
        }
    )
}

def get_service_for_slide_type(slide_type: str) -> Optional[str]:
    """
    Get the service name that handles a given slide type.

    Args:
        slide_type: The slide type (e.g., "pyramid", "matrix_2x2")

    Returns:
        Service name (e.g., "illustrator_service") or None if not found
    """
    for service_name, config in SERVICE_REGISTRY.items():
        if slide_type in config.slide_types:
            return service_name
    return None

def get_endpoint_for_slide_type(slide_type: str) -> Optional[ServiceEndpoint]:
    """
    Get the endpoint configuration for a slide type.

    Args:
        slide_type: The slide type (e.g., "pyramid")

    Returns:
        ServiceEndpoint or None if not found
    """
    service_name = get_service_for_slide_type(slide_type)
    if not service_name:
        return None

    config = SERVICE_REGISTRY[service_name]

    # Check if specific endpoint defined
    if slide_type in config.endpoints:
        return config.endpoints[slide_type]

    # Default endpoint (for services like text_service)
    return None

def get_all_slide_types() -> List[str]:
    """Get all available slide types across all services."""
    all_types = []
    for config in SERVICE_REGISTRY.values():
        if config.enabled:
            all_types.extend(config.slide_types)
    return sorted(all_types)
```

### 2. Illustrator Client (`src/clients/illustrator_client.py`)

**Purpose**: HTTP client for calling Illustrator Service APIs

**Design**:

```python
"""
Illustrator Service Client for Director Agent v3.4
Handles communication with Illustrator Service v1.0 for visualization generation.
"""

import httpx
from typing import Dict, Any, Optional, List
from src.utils.logger import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)

class IllustratorClient:
    """Client for calling Illustrator Service v1.0 APIs"""

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize Illustrator client.

        Args:
            base_url: Base URL for Illustrator service (defaults to settings)
        """
        settings = get_settings()
        self.base_url = base_url or settings.ILLUSTRATOR_SERVICE_URL
        self.timeout = settings.ILLUSTRATOR_SERVICE_TIMEOUT
        logger.info(f"IllustratorClient initialized: {self.base_url}")

    async def generate_pyramid(
        self,
        num_levels: int,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        target_points: Optional[List[str]] = None,
        tone: str = "professional",
        audience: str = "general"
    ) -> Dict[str, Any]:
        """
        Generate a pyramid visualization.

        Args:
            num_levels: Number of pyramid levels (3-6)
            topic: Main topic/title for the pyramid
            context: Presentation context (presentation_title, industry, etc.)
            target_points: Specific points for each level
            tone: Content tone (professional, casual, technical, etc.)
            audience: Target audience (executives, employees, etc.)

        Returns:
            Dictionary with:
                - html: Complete pyramid HTML
                - metadata: Generation metadata
                - generated_content: Generated text content
                - validation: Character constraint validation results

        Raises:
            httpx.HTTPError: If API call fails
        """
        payload = {
            "num_levels": num_levels,
            "topic": topic,
            "context": context or {},
            "tone": tone,
            "audience": audience,
            "validate_constraints": True
        }

        if target_points:
            payload["target_points"] = target_points

        logger.info(
            f"Generating pyramid: {num_levels} levels, topic='{topic}', "
            f"tone={tone}, audience={audience}"
        )

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1.0/pyramid/generate",
                    json=payload
                )
                response.raise_for_status()

                result = response.json()

                # Log validation status
                if not result.get("validation", {}).get("valid", True):
                    logger.warning(
                        f"Pyramid validation warnings: "
                        f"{len(result['validation'].get('violations', []))} violations"
                    )

                logger.info(
                    f"Pyramid generated successfully: "
                    f"{result['metadata']['generation_time_ms']}ms, "
                    f"{result['metadata']['attempts']} attempts"
                )

                return result

            except httpx.HTTPError as e:
                logger.error(f"Failed to generate pyramid: {str(e)}")
                raise

    async def health_check(self) -> bool:
        """
        Check if Illustrator service is healthy.

        Returns:
            True if service is available and healthy
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Illustrator service health check failed: {str(e)}")
            return False
```

### 3. Settings Update (`config/settings.py`)

**Add Illustrator service configuration**:

```python
# Illustrator Service Integration (v3.4)
ILLUSTRATOR_SERVICE_ENABLED: bool = Field(True, env="ILLUSTRATOR_SERVICE_ENABLED")
ILLUSTRATOR_SERVICE_URL: str = Field(
    "http://localhost:8000",
    env="ILLUSTRATOR_SERVICE_URL"
)
ILLUSTRATOR_SERVICE_TIMEOUT: int = Field(60, env="ILLUSTRATOR_SERVICE_TIMEOUT")
```

### 4. Slide Type Classifier Update (`src/utils/slide_type_classifier.py`)

**Add pyramid detection logic**:

```python
# Add to SLIDE_TYPE_KEYWORDS dictionary
"pyramid": [
    "pyramid", "hierarchy", "hierarchical", "organizational structure",
    "levels", "tier", "tiers", "foundation to top", "base to peak",
    "maslow", "organizational hierarchy", "reporting structure"
]
```

### 5. Service Router Update (`src/utils/service_router_v1_2.py`)

**Add Illustrator routing logic**:

```python
from src.clients.illustrator_client import IllustratorClient
from src.utils.service_registry import get_service_for_slide_type

async def route_slide_to_service(slide: dict, context: dict) -> dict:
    """
    Route slide to appropriate content generation service.

    Args:
        slide: Slide specification from strawman
        context: Presentation context

    Returns:
        Generated content with HTML
    """
    slide_type = slide.get("slide_type")
    service_name = get_service_for_slide_type(slide_type)

    if service_name == "illustrator_service":
        return await route_to_illustrator(slide, context)
    elif service_name == "text_service":
        return await route_to_text_service(slide, context)
    elif service_name == "hero_service":
        return await route_to_hero_service(slide, context)
    else:
        raise ValueError(f"Unknown slide type: {slide_type}")

async def route_to_illustrator(slide: dict, context: dict) -> dict:
    """Route pyramid slides to Illustrator service"""
    slide_type = slide["slide_type"]

    if slide_type == "pyramid":
        illustrator = IllustratorClient()

        # Extract pyramid configuration
        viz_config = slide.get("visualization_config", {})
        num_levels = viz_config.get("pyramid_levels", len(slide.get("key_points", [])))
        num_levels = max(3, min(6, num_levels))  # Clamp to 3-6

        # Build context
        pyramid_context = {
            "presentation_title": context.get("presentation_title"),
            "slide_purpose": slide.get("narrative"),
            "industry": context.get("industry"),
            "company": context.get("company"),
            "prior_slides_summary": context.get("prior_slides_summary")
        }

        # Generate pyramid
        result = await illustrator.generate_pyramid(
            num_levels=num_levels,
            topic=slide["title"],
            context=pyramid_context,
            target_points=slide.get("key_points"),
            tone=viz_config.get("tone", "professional"),
            audience=context.get("audience", "general")
        )

        # Return in standard format
        return {
            "content": {
                "rich_content": result["html"]
            },
            "metadata": {
                "slide_type": slide_type,
                "service": "illustrator",
                "visualization": "pyramid",
                "model_used": result["metadata"]["model"],
                "generation_time_ms": result["metadata"]["generation_time_ms"],
                "validation_status": "valid" if result["validation"]["valid"] else "invalid"
            }
        }
```

### 6. Stage 4 Prompt Update

**File**: `config/prompts/modular/generate_strawman.md`

**Add pyramid to available slide types**:

```markdown
## Available Slide Types (14 types)

### Illustrator Service Types (Visualizations)

1. **pyramid** (3-6 levels)
   - **Use for**: Hierarchical structures, organizational charts, priority levels,
     skill development pathways, Maslow's hierarchy, strategic frameworks
   - **Best for**: Showing progression from foundation to peak, reporting structures,
     layered concepts
   - **Levels**: 3-6 levels (base to peak)
   - **Config**: Specify `pyramid_levels` in `visualization_config`
   - **Example**: "Organizational Structure" with 4 levels (Execution → Operations → Strategy → Vision)

### Text Service Types (Content Layouts)

2. **matrix_2x2** - Four-quadrant strategic frameworks (SWOT, Eisenhower, BCG)
3. **bilateral_comparison** - Side-by-side comparisons (before/after, pros/cons)
...
```

**Add guidance on when to use pyramid**:

```markdown
## Slide Type Selection Guidelines

### When to Use Pyramid

**Choose pyramid when presenting**:
- Hierarchical organizational structures (CEO → Directors → Managers → Staff)
- Priority frameworks (Critical → Important → Nice-to-have)
- Skill development pathways (Foundation → Intermediate → Advanced → Expert)
- Strategic layers (Vision → Strategy → Tactics → Execution)
- Maslow's hierarchy of needs
- Information architecture (High-level → Detailed)

**Pyramid Levels**:
- **3 levels**: Simple hierarchies (Top, Middle, Base)
- **4 levels**: Standard hierarchies (Vision, Strategy, Operations, Execution)
- **5 levels**: Detailed progressions (5-stage skill development)
- **6 levels**: Complex hierarchies (6-tier organizational structures)

**Key Points as Pyramid Levels**:
When you identify a pyramid slide, put level labels in `key_points` array (top to bottom).

Example:
```json
{
  "slide_type": "pyramid",
  "title": "Skills Development Pathway",
  "key_points": ["Expert Level", "Advanced Skills", "Core Competencies", "Foundation"],
  "visualization_config": {
    "pyramid_levels": 4
  }
}
```
```

---

## Implementation Phases

### Phase 1: Foundation (Service Registry & Client)

**Objective**: Build the infrastructure for multi-service routing

**Tasks**:
1. ✅ Create `src/clients/` directory
2. ✅ Implement `src/clients/illustrator_client.py`
3. ✅ Implement `src/utils/service_registry.py`
4. ✅ Update `config/settings.py` with Illustrator settings
5. ✅ Add `.env.example` entries for Illustrator service
6. ✅ Create unit tests for IllustratorClient

**Testing**:
```python
# Test IllustratorClient standalone
async def test_pyramid_generation():
    client = IllustratorClient("http://localhost:8000")

    result = await client.generate_pyramid(
        num_levels=4,
        topic="Product Strategy",
        context={"presentation_title": "Q4 Plan"},
        target_points=["Vision", "Strategy", "Operations", "Execution"],
        tone="professional",
        audience="executives"
    )

    assert result["success"]
    assert "html" in result
    assert result["validation"]["valid"]
    print(f"Generated {len(result['html'])} bytes of HTML")
```

**Deliverables**:
- ✅ Working Illustrator client
- ✅ Service registry configuration
- ✅ Unit tests passing

**Estimated Time**: 2-3 hours

---

### Phase 2: Stage 4 Integration (Strawman Generation)

**Objective**: Enable LLM to select pyramid as a slide type

**Tasks**:
1. ✅ Update `src/utils/slide_type_classifier.py` with pyramid keywords
2. ✅ Update `config/prompts/modular/generate_strawman.md` with pyramid description
3. ✅ Extend `src/models/agents.py` Slide model with `visualization_config` field
4. ✅ Test: Run Director Stage 4 and verify LLM can select pyramid
5. ✅ Test: Verify strawman JSON includes pyramid slides correctly

**Slide Model Update**:
```python
# src/models/agents.py
class Slide(BaseModel):
    slide_number: int
    slide_id: str
    title: str
    slide_type: str
    narrative: str
    key_points: List[str]
    layout_id: str
    visualization_config: Optional[Dict[str, Any]] = None  # NEW FIELD
```

**Testing**:
```python
# Test Stage 4 with pyramid scenario
async def test_stage4_pyramid_selection():
    # Create session with request for hierarchical structure
    user_request = "Create a presentation about our organizational structure"

    # Run Stage 4
    strawman = await director.generate_strawman(user_request)

    # Verify pyramid slide exists
    pyramid_slides = [s for s in strawman.slides if s.slide_type == "pyramid"]
    assert len(pyramid_slides) > 0

    # Verify configuration
    pyramid = pyramid_slides[0]
    assert pyramid.visualization_config is not None
    assert "pyramid_levels" in pyramid.visualization_config
    print(f"LLM selected pyramid with {pyramid.visualization_config['pyramid_levels']} levels")
```

**Deliverables**:
- ✅ LLM can select pyramid in strawman
- ✅ Strawman includes visualization_config
- ✅ Stage 4 tests passing

**Estimated Time**: 3-4 hours

---

### Phase 3: Stage 6 Integration (Content Generation)

**Objective**: Director calls Illustrator API and generates pyramid HTML

**Tasks**:
1. ✅ Update `src/utils/service_router_v1_2.py` with Illustrator routing
2. ✅ Update `src/utils/content_transformer.py` to handle pyramid HTML
3. ✅ Update `src/agents/director.py` Stage 6 logic to use service router
4. ✅ Test: Director routes pyramid to Illustrator
5. ✅ Test: Pyramid HTML embeds in L25 layout
6. ✅ Test: End-to-end: Strawman → Content Generation → Layout Builder

**Content Transformer Update**:
```python
# src/utils/content_transformer.py
def transform_illustrator_response(slide: dict, response: dict) -> dict:
    """
    Transform Illustrator service response to Layout Builder format.

    Args:
        slide: Slide specification from strawman
        response: Response from Illustrator API

    Returns:
        Layout Builder slide payload
    """
    return {
        "layout": "L25",
        "content": {
            "slide_title": slide["title"],
            "subtitle": slide.get("subtitle", ""),
            "rich_content": response["content"]["rich_content"],
            "presentation_name": slide.get("presentation_name", "")
        }
    }
```

**Testing**:
```python
# Test Stage 6 pyramid generation
async def test_stage6_pyramid_generation():
    # Create strawman with pyramid slide
    strawman = {
        "slides": [
            {
                "slide_number": 1,
                "title": "Organizational Hierarchy",
                "slide_type": "pyramid",
                "key_points": ["Vision", "Strategy", "Operations", "Execution"],
                "layout_id": "L25",
                "visualization_config": {
                    "pyramid_levels": 4
                }
            }
        ]
    }

    # Run Stage 6
    enriched = await director.generate_content(strawman)

    # Verify pyramid HTML generated
    slide = enriched["slides"][0]
    assert "rich_content" in slide["content"]
    assert "<div" in slide["content"]["rich_content"]  # HTML present
    assert "pyramid" in slide["content"]["rich_content"].lower()
    print(f"Generated {len(slide['content']['rich_content'])} bytes of pyramid HTML")
```

**Deliverables**:
- ✅ Director routes pyramid to Illustrator
- ✅ Pyramid HTML embeds correctly
- ✅ Stage 6 tests passing

**Estimated Time**: 4-5 hours

---

### Phase 4: End-to-End Testing

**Objective**: Validate complete workflow from Stage 4 → Stage 6 → Layout Builder

**Test Scenarios**:

#### Scenario 1: Simple 4-Level Pyramid
```python
async def test_e2e_simple_pyramid():
    """Test basic pyramid generation end-to-end"""

    # Stage 4: Generate strawman with pyramid
    user_request = "Show our product development hierarchy"
    strawman = await director.generate_strawman(user_request)

    # Verify pyramid selected
    pyramid_slides = [s for s in strawman.slides if s.slide_type == "pyramid"]
    assert len(pyramid_slides) == 1

    # Stage 6: Generate content
    enriched = await director.generate_content(strawman)

    # Verify HTML present
    pyramid_slide = enriched["slides"][pyramid_slides[0].slide_number - 1]
    assert "rich_content" in pyramid_slide["content"]

    # Send to Layout Builder
    presentation_id = await deck_builder.create_presentation(enriched)
    assert presentation_id is not None

    print(f"✅ Presentation created: /p/{presentation_id}")
```

#### Scenario 2: Mixed Slide Types
```python
async def test_e2e_mixed_slides():
    """Test presentation with pyramid + text service slides"""

    strawman = {
        "slides": [
            {"slide_type": "title_slide", ...},
            {"slide_type": "pyramid", "visualization_config": {"pyramid_levels": 4}},
            {"slide_type": "matrix_2x2", ...},
            {"slide_type": "pyramid", "visualization_config": {"pyramid_levels": 3}},
            {"slide_type": "closing_slide", ...}
        ]
    }

    # Stage 6: Generate all content
    enriched = await director.generate_content(strawman)

    # Verify all slides have content
    for slide in enriched["slides"]:
        assert "content" in slide
        if slide["slide_type"] == "pyramid":
            assert "rich_content" in slide["content"]
        elif slide["slide_type"] in ["title_slide", "closing_slide"]:
            assert "hero_content" in slide["content"]
        else:
            assert "rich_content" in slide["content"]

    print(f"✅ All {len(enriched['slides'])} slides generated successfully")
```

#### Scenario 3: Pyramid Constraint Validation
```python
async def test_pyramid_validation():
    """Test that pyramid character constraints are respected"""

    result = await illustrator_client.generate_pyramid(
        num_levels=4,
        topic="A very long topic that might cause validation issues",
        context={"presentation_title": "Test"}
    )

    # Check validation status
    if result["validation"]["valid"]:
        print("✅ All character constraints met")
    else:
        violations = result["validation"]["violations"]
        print(f"⚠️ {len(violations)} constraint violations:")
        for v in violations:
            print(f"  - {v['field']}: {v['actual_length']} chars ({v['status']})")

    # Content should still be usable
    assert result["html"] is not None
```

**Deliverables**:
- ✅ All test scenarios passing
- ✅ Documentation of edge cases
- ✅ Performance benchmarks

**Estimated Time**: 2-3 hours

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_illustrator_client.py`

```python
import pytest
from src.clients.illustrator_client import IllustratorClient

@pytest.mark.asyncio
async def test_pyramid_generation_success():
    """Test successful pyramid generation"""
    client = IllustratorClient("http://localhost:8000")

    result = await client.generate_pyramid(
        num_levels=4,
        topic="Test Pyramid",
        tone="professional",
        audience="general"
    )

    assert result["success"]
    assert "html" in result
    assert result["metadata"]["num_levels"] == 4

@pytest.mark.asyncio
async def test_pyramid_with_target_points():
    """Test pyramid generation with specific target points"""
    client = IllustratorClient()

    result = await client.generate_pyramid(
        num_levels=3,
        topic="Simple Hierarchy",
        target_points=["Top", "Middle", "Base"]
    )

    assert result["success"]
    assert "Top" in result["html"] or "top" in result["html"].lower()

@pytest.mark.asyncio
async def test_health_check():
    """Test Illustrator service health check"""
    client = IllustratorClient()

    is_healthy = await client.health_check()
    assert is_healthy
```

### Integration Tests

**File**: `tests/test_illustrator_integration.py`

```python
import pytest
from src.agents.director import DirectorAgent
from src.utils.service_router_v1_2 import route_slide_to_service

@pytest.mark.asyncio
async def test_pyramid_routing():
    """Test that pyramid slides route to Illustrator"""

    slide = {
        "slide_type": "pyramid",
        "title": "Test Pyramid",
        "key_points": ["A", "B", "C", "D"],
        "visualization_config": {"pyramid_levels": 4}
    }

    context = {"presentation_title": "Test Presentation"}

    result = await route_slide_to_service(slide, context)

    assert "content" in result
    assert "rich_content" in result["content"]
    assert result["metadata"]["service"] == "illustrator"

@pytest.mark.asyncio
async def test_stage6_with_pyramid():
    """Test Director Stage 6 with pyramid slide"""

    director = DirectorAgent()

    strawman = {
        "main_title": "Test Presentation",
        "slides": [
            {
                "slide_number": 1,
                "slide_type": "pyramid",
                "title": "Hierarchy",
                "key_points": ["Top", "Middle", "Base"],
                "layout_id": "L25",
                "visualization_config": {"pyramid_levels": 3}
            }
        ]
    }

    enriched = await director.handle_content_generation(strawman)

    assert len(enriched["slides"]) == 1
    assert "rich_content" in enriched["slides"][0]["content"]
```

### End-to-End Tests

**File**: `tests/test_e2e_pyramid.py`

```python
@pytest.mark.asyncio
async def test_full_pipeline_with_pyramid():
    """Test complete pipeline: Stage 4 → Stage 6 → Layout Builder"""

    # Simulate user request
    user_request = "Create a presentation showing our organizational structure"

    # Stage 4: Generate strawman
    director = DirectorAgent()
    strawman = await director.generate_strawman(user_request)

    # Verify pyramid selected
    has_pyramid = any(s.slide_type == "pyramid" for s in strawman.slides)
    assert has_pyramid, "LLM should select pyramid for organizational structure"

    # Stage 6: Generate content
    enriched = await director.generate_content(strawman)

    # Verify pyramid HTML generated
    pyramid_slides = [s for s in enriched.slides if s.slide_type == "pyramid"]
    for slide in pyramid_slides:
        assert slide.content.rich_content is not None
        assert len(slide.content.rich_content) > 1000  # Substantial HTML

    # Send to Layout Builder (if available)
    if director.deck_builder_enabled:
        presentation_id = await director.deck_builder_client.create_presentation(enriched)
        assert presentation_id is not None
        print(f"✅ Presentation created: /p/{presentation_id}")
```

---

## Future Extensibility

### Adding New Illustrator Endpoints

**Example: Adding Funnel Diagram**

#### Step 1: Update Service Registry
```python
# src/utils/service_registry.py
"illustrator_service": ServiceConfig(
    slide_types=[
        "pyramid",
        "funnel",  # NEW
    ],
    endpoints={
        "pyramid": ServiceEndpoint(path="/v1.0/pyramid/generate"),
        "funnel": ServiceEndpoint(path="/v1.0/funnel/generate"),  # NEW
    }
)
```

#### Step 2: Add Client Method
```python
# src/clients/illustrator_client.py
async def generate_funnel(
    self,
    num_stages: int,
    topic: str,
    context: Optional[Dict[str, Any]] = None,
    stage_labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate a funnel visualization."""
    payload = {
        "num_stages": num_stages,
        "topic": topic,
        "context": context or {},
        "validate_constraints": True
    }

    if stage_labels:
        payload["stage_labels"] = stage_labels

    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            f"{self.base_url}/v1.0/funnel/generate",
            json=payload
        )
        return response.json()
```

#### Step 3: Add Routing Logic
```python
# src/utils/service_router_v1_2.py
async def route_to_illustrator(slide: dict, context: dict) -> dict:
    slide_type = slide["slide_type"]

    if slide_type == "pyramid":
        return await generate_pyramid_content(slide, context)
    elif slide_type == "funnel":  # NEW
        return await generate_funnel_content(slide, context)  # NEW
```

#### Step 4: Update Stage 4 Prompt
```markdown
### Illustrator Service Types

1. **pyramid** - Hierarchical structures (3-6 levels)
2. **funnel** - Conversion funnels, sales pipelines (3-7 stages)  # NEW
```

**Total effort per new visualization**: ~2-3 hours

### Planned Future Visualizations

| Visualization | Endpoint | Use Cases | Priority |
|---------------|----------|-----------|----------|
| **Funnel** | `/v1.0/funnel/generate` | Sales pipelines, conversion funnels, customer journeys | High |
| **SWOT** | `/v1.0/swot/generate` | Strategic planning, competitive analysis | High |
| **BCG Matrix** | `/v1.0/bcg/generate` | Portfolio analysis, product positioning | Medium |
| **Gantt Chart** | `/v1.0/gantt/generate` | Project timelines, roadmaps | Medium |
| **Org Chart** | `/v1.0/orgchart/generate` | Organizational structures, team hierarchies | Low |
| **Value Chain** | `/v1.0/valuechain/generate` | Business process analysis | Low |

---

## Risk Mitigation

### Risk 1: Illustrator Service Unavailable

**Mitigation**:
```python
async def route_to_illustrator(slide: dict, context: dict) -> dict:
    """Route with fallback to placeholder content"""

    try:
        # Attempt Illustrator call
        return await call_illustrator_api(slide, context)
    except Exception as e:
        logger.error(f"Illustrator service failed: {e}")

        # Fallback: Generate placeholder HTML
        return {
            "content": {
                "rich_content": generate_pyramid_placeholder(slide)
            },
            "metadata": {
                "service": "fallback",
                "error": str(e)
            }
        }

def generate_pyramid_placeholder(slide: dict) -> str:
    """Generate simple text-based pyramid fallback"""
    levels = slide.get("key_points", [])

    html = "<div style='text-align: center;'>"
    html += f"<h2>{slide['title']}</h2>"
    html += "<div style='margin: 20px;'>"

    for i, level in enumerate(reversed(levels)):
        size = 16 + (i * 4)
        html += f"<div style='font-size: {size}px; margin: 10px;'>{level}</div>"

    html += "</div></div>"

    return html
```

### Risk 2: Character Constraint Validation Failures

**Mitigation**:
- Illustrator already retries up to 3 times
- If still invalid, content is returned with warnings
- Director logs warnings but uses content anyway
- Manual editing can fix if needed

### Risk 3: LLM Not Selecting Pyramid

**Mitigation**:
- Strong prompt guidance with examples
- Keyword matching in user requests
- A/B testing prompts
- Monitor pyramid selection rate in production

---

## Success Metrics

### Phase 1 Success
- [ ] IllustratorClient instantiates without errors
- [ ] Health check returns true
- [ ] Test pyramid generation completes in <5 seconds
- [ ] Service registry correctly maps "pyramid" → "illustrator_service"

### Phase 2 Success
- [ ] LLM selects pyramid for hierarchical scenarios >50% of the time
- [ ] Strawman JSON includes valid visualization_config
- [ ] Slide classifier detects pyramid keywords correctly

### Phase 3 Success
- [ ] Director routes pyramid to Illustrator (not Text Service)
- [ ] Pyramid HTML embeds in L25 layout without errors
- [ ] Character constraints validated with <5% failures
- [ ] End-to-end generation <10 seconds per pyramid

### Production Success (30 days post-launch)
- [ ] 100+ pyramid slides generated successfully
- [ ] <2% Illustrator API failures
- [ ] Average generation time <4 seconds
- [ ] User feedback: pyramid quality >4.0/5.0

---

## Timeline

| Phase | Duration | Start | End |
|-------|----------|-------|-----|
| **Phase 1**: Foundation | 2-3 hours | Day 1 | Day 1 |
| **Phase 2**: Stage 4 Integration | 3-4 hours | Day 1 | Day 2 |
| **Phase 3**: Stage 6 Integration | 4-5 hours | Day 2 | Day 3 |
| **Phase 4**: E2E Testing | 2-3 hours | Day 3 | Day 3 |
| **Total** | **11-15 hours** | - | **3 days** |

---

## Appendix

### File Checklist

**New Files**:
- [ ] `src/clients/__init__.py`
- [ ] `src/clients/illustrator_client.py`
- [ ] `src/utils/service_registry.py`
- [ ] `tests/test_illustrator_client.py`
- [ ] `tests/test_illustrator_integration.py`
- [ ] `tests/test_e2e_pyramid.py`

**Modified Files**:
- [ ] `config/settings.py` (Add Illustrator settings)
- [ ] `.env.example` (Add Illustrator env vars)
- [ ] `src/utils/slide_type_classifier.py` (Add pyramid keywords)
- [ ] `config/prompts/modular/generate_strawman.md` (Add pyramid description)
- [ ] `src/models/agents.py` (Add visualization_config field)
- [ ] `src/utils/service_router_v1_2.py` (Add Illustrator routing)
- [ ] `src/utils/content_transformer.py` (Handle pyramid HTML)
- [ ] `src/agents/director.py` (Use service router in Stage 6)

### Environment Variables

```bash
# .env additions
ILLUSTRATOR_SERVICE_ENABLED=true
ILLUSTRATOR_SERVICE_URL=http://localhost:8000
ILLUSTRATOR_SERVICE_TIMEOUT=60
```

---

## Next Steps

1. **Review this plan** and provide feedback
2. **Start Phase 1** implementation
3. **Test Illustrator service** is running and healthy
4. **Proceed through phases** sequentially
5. **Deploy to production** after all tests pass

---

**Document Status**: ✅ Complete - Ready for Implementation

**Last Updated**: January 15, 2025

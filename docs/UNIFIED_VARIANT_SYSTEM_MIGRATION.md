# Unified Variant System Migration Guide

**Version**: 2.0.0
**Date**: 2025-11-29
**Status**: Ready for gradual rollout

## Overview

The Unified Variant Registration System replaces hardcoded slide classification and service routing with a registry-driven approach. This allows adding new content variants by editing a JSON file instead of modifying Python code.

## Benefits

### Before (Existing System)
- ❌ Hardcoded keywords in `SlideTypeClassifier`
- ❌ Hardcoded service logic in `ServiceRouterV1_2`
- ❌ Adding new variant requires editing 5+ Python files
- ❌ ~2.5 hours integration time per variant
- ❌ Risk of introducing bugs in working code

### After (Unified System)
- ✅ All keywords in `unified_variant_registry.json`
- ✅ Registry-driven routing via adapters
- ✅ Adding new variant = edit 1 JSON file
- ✅ ~5 minutes integration time per variant
- ✅ Zero code changes for new variants

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Director Agent                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  DirectorIntegrationLayer (New)                  │  │
│  │  - classify_slide()                              │  │
│  │  - generate_slide_content()                      │  │
│  │  - generate_presentation_content()               │  │
│  └──────────────────┬───────────────────────────────┘  │
└────────────────────┼────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
┌───────▼────────┐          ┌───────▼────────┐
│ UnifiedSlide   │          │ UnifiedService │
│ Classifier     │          │ Router         │
│ (Registry-     │          │ (Adapter-      │
│  driven)       │          │  driven)       │
└───────┬────────┘          └───────┬────────┘
        │                           │
        │    ┌──────────────────────┘
        │    │
┌───────▼────▼───────┐
│ RegistryLoader     │
│ (Singleton)        │
└───────┬────────────┘
        │
┌───────▼────────────┐
│ unified_variant_   │
│ registry.json      │
│ (56+ variants)     │
└────────────────────┘
```

## Configuration

### Environment Variables

Add to `.env`:

```bash
# Unified Variant System (Phase 3.5)
UNIFIED_VARIANT_SYSTEM_ENABLED=false    # Master switch
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=0     # Rollout percentage (0-100)
VARIANT_REGISTRY_PATH=                  # Optional: custom registry path
```

### Rollout Stages

#### Stage 0: Disabled (Default)
```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=false
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=0
```
- **Effect**: All sessions use existing system
- **Use**: Current production state

#### Stage 1: Testing (Internal Only)
```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=true
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=1    # 1% of sessions
```
- **Effect**: 1% of sessions use unified system
- **Use**: Initial testing with real traffic
- **Monitor**: Error rates, classification accuracy, performance

#### Stage 2: Limited Rollout
```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=true
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=10   # 10% of sessions
```
- **Effect**: 10% of sessions use unified system
- **Use**: Wider testing, gather metrics
- **Monitor**: Compare results between systems

#### Stage 3: Gradual Increase
```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=true
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=25   # 25%
# Then 50%, 75%, etc.
```
- **Effect**: Progressively more sessions
- **Use**: Gradual migration
- **Monitor**: Continued monitoring, ready to roll back

#### Stage 4: Full Rollout
```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=true
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=100  # 100%
```
- **Effect**: All sessions use unified system
- **Use**: Complete migration
- **Next**: Remove old code after stabilization period

## Code Integration

### Option 1: Automatic (Recommended)

The system uses feature flags automatically - no Director code changes needed.

**Director Agent** (future enhancement):
```python
from src.utils.unified_system_rollout import should_use_unified_system
from src.services.director_integration import DirectorIntegrationLayer

class DirectorAgent:
    def __init__(self):
        # Existing initialization...

        # Add unified system support
        self.use_unified_system = should_use_unified_system()
        if self.use_unified_system:
            self.integration = DirectorIntegrationLayer()

    async def process_stage_4_generate_strawman(self, ...):
        if self.use_unified_system:
            # Use new system
            for slide in strawman.slides:
                enriched = self.integration.classify_and_enrich_slide(slide)
        else:
            # Use existing system
            classifier = SlideTypeClassifier()
            for slide in strawman.slides:
                slide.slide_type_classification = classifier.classify(...)

    async def process_stage_6_content_generation(self, ...):
        if self.use_unified_system:
            # Use new system
            result = await self.integration.generate_presentation_content(
                strawman=strawman,
                session_id=session_id
            )
        else:
            # Use existing system
            router = ServiceRouterV1_2(...)
            result = await router.route_presentation(...)
```

### Option 2: Gradual Migration Per Stage

Migrate one stage at a time:

**Stage 4 Only**:
```python
# Stage 4: Always use unified for classification
if True:  # Or check feature flag
    integration = DirectorIntegrationLayer()
    for slide in strawman.slides:
        enriched = integration.classify_and_enrich_slide(slide)

# Stage 6: Still use existing routing
router = ServiceRouterV1_2(...)
result = await router.route_presentation(...)
```

**Both Stages**:
```python
# Initialize once
integration = DirectorIntegrationLayer()

# Stage 4: Classification
for slide in strawman.slides:
    enriched = integration.classify_and_enrich_slide(slide)

# Stage 6: Content generation
result = await integration.generate_presentation_content(
    strawman=strawman,
    session_id=session_id
)
```

## Adding New Variants

### Old Method (Existing System)

Requires editing 5+ files:

1. Add keywords to `slide_type_classifier.py` (~50 lines)
2. Add routing logic to `service_router_v1_2.py` (~100 lines)
3. Add endpoint handling (~50 lines)
4. Update variant catalog (~30 lines)
5. Add tests (~200 lines)

**Total**: ~2.5 hours, 400+ lines changed

### New Method (Unified System)

Edit 1 file: `config/unified_variant_registry.json`

**Example: Adding "SWOT Matrix" variant**

```json
{
  "services": {
    "illustrator_service_v1.0": {
      "variants": {
        "swot_matrix": {
          "variant_id": "swot_matrix",
          "display_name": "SWOT Matrix",
          "description": "Four-quadrant SWOT analysis matrix",
          "status": "production",
          "endpoint": "/v1.0/swot/generate",
          "layout_id": "L25",

          "classification": {
            "priority": 7,
            "keywords": [
              "swot", "swot analysis", "swot matrix",
              "strengths", "weaknesses", "opportunities", "threats",
              "internal factors", "external factors",
              "strategic planning", "strategic framework",
              "competitive analysis", "business analysis"
            ]
          },

          "llm_guidance": {
            "use_cases": [
              "Strategic planning sessions",
              "Business analysis frameworks",
              "Competitive positioning"
            ],
            "best_for": "Comprehensive strategic analysis",
            "avoid_when": "Need more than 4 quadrants"
          },

          "parameters": {
            "required_fields": ["topic"]
          }
        }
      }
    }
  }
}
```

**Total**: ~5 minutes, 1 file changed

## Monitoring

### Metrics to Track

1. **Adoption Rate**
   - `unified_system_percentage` usage
   - Sessions using new vs. old system

2. **Classification Accuracy**
   - Variant selection rates
   - Confidence scores
   - Misclassification rates

3. **Performance**
   - Classification latency
   - Content generation latency
   - Error rates

4. **Service Health**
   - Success/failure rates per service
   - Timeout rates
   - Error types

### Logging

The system logs all key decisions:

```python
# Classification decisions
logger.info(
    "Slide classified",
    extra={
        "variant_id": "pie_chart",
        "confidence": "0.85",
        "service_name": "analytics_service_v3"
    }
)

# Rollout decisions
logger.info(
    "System selection for CONTENT_GENERATION",
    extra={
        "session_id": "session_123",
        "system": "unified",
        "rollout_percentage": 50
    }
)

# Content generation results
logger.info(
    "Content generated successfully",
    extra={
        "variant_id": "pie_chart",
        "service_name": "analytics_service_v3"
    }
)
```

## Testing

### Unit Tests

All components have comprehensive test coverage:

- **Registry Loader**: 21 tests ✅
- **Slide Classifier**: 32 tests ✅
- **Service Router**: Tested via integration layer
- **Director Integration**: 16 tests ✅
- **Rollout Helper**: 20 tests ✅

**Total**: 89 tests, 100% passing

### Integration Testing

Test with real registry:

```python
from src.services.director_integration import DirectorIntegrationLayer

integration = DirectorIntegrationLayer()

# Test classification
result = integration.classify_slide(
    title="Market Share Distribution",
    key_points=["Product A: 45%", "Product B: 30%"]
)
assert result["variant_id"] == "pie_chart"

# Test content generation
result = await integration.generate_slide_content(
    variant_id="pie_chart",
    service_name="analytics_service_v3",
    parameters={"data": [{"label": "A", "value": 45}]}
)
assert result["success"] is True
```

### End-to-End Testing

Test full Director workflow with unified system enabled:

```bash
# Enable unified system for testing
export UNIFIED_VARIANT_SYSTEM_ENABLED=true
export UNIFIED_VARIANT_SYSTEM_PERCENTAGE=100

# Run Director end-to-end tests
pytest tests/test_director_e2e.py -v
```

## Rollback Plan

If issues occur during rollout:

### Immediate Rollback (Emergency)

```bash
# Disable unified system
UNIFIED_VARIANT_SYSTEM_ENABLED=false
```

Effect: All sessions immediately use existing system

### Gradual Rollback

```bash
# Reduce percentage
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=25  # From 50% to 25%
# Then 10%, then 5%, then 0%
```

### Complete Rollback

```bash
UNIFIED_VARIANT_SYSTEM_ENABLED=false
UNIFIED_VARIANT_SYSTEM_PERCENTAGE=0
```

All sessions use existing system. No code changes needed.

## Timeline

### Week 1: Internal Testing
- Enable at 1% for internal QA
- Monitor logs and metrics
- Fix any issues

### Week 2-3: Limited Rollout
- Increase to 10%, then 25%
- Compare results with existing system
- Gather user feedback

### Week 4-5: Gradual Increase
- Increase to 50%, then 75%
- Continue monitoring
- Address any edge cases

### Week 6: Full Rollout
- Enable at 100%
- Monitor stability
- Begin planning removal of old code

### Week 8+: Cleanup
- Remove old classification code
- Remove old routing code
- Update documentation

## FAQ

### Q: Will this affect existing presentations?
**A**: No. The system only affects new content generation. Existing presentations are unchanged.

### Q: Can we roll back if there are issues?
**A**: Yes. Set `UNIFIED_VARIANT_SYSTEM_ENABLED=false` for immediate rollback.

### Q: How do we add a new variant?
**A**: Edit `config/unified_variant_registry.json`, add variant definition. Takes ~5 minutes.

### Q: What happens if the registry file is missing?
**A**: The system will fall back to the existing implementation and log an error.

### Q: Can we use both systems simultaneously?
**A**: Yes. The percentage rollout allows gradual migration.

### Q: How do we know which system was used?
**A**: Check logs for "system: unified" or "system: existing" entries.

### Q: What if a service goes down?
**A**: The router returns error responses with detailed error types. Director can handle gracefully.

## Support

For issues or questions:
1. Check logs in Logfire/CloudWatch
2. Review error rates in monitoring
3. Check registry file syntax
4. Verify feature flag settings
5. Contact development team

## References

- Design Document: `docs/UNIFIED_VARIANT_REGISTRY_DESIGN.md`
- JSON Schema: `config/schemas/unified_registry_schema.json`
- Registry File: `config/unified_variant_registry.json`
- Integration Layer: `src/services/director_integration.py`
- Rollout Helper: `src/utils/unified_system_rollout.py`

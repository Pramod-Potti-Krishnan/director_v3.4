# Service Integration Guide for Unified Variant System

**Version**: 1.0.0
**Date**: 2025-11-29
**Audience**: Content Generation Service Developers

## Overview

This guide shows how content generation services (Analytics, Illustrator, Text) can integrate with the unified variant registration system by exporting their metadata and validating their configurations.

## Quick Start

### 1. Install Dependencies

```python
from src.utils.service_metadata_exporter import ServiceMetadataExporter
from src.utils.variant_validator import validate_variant, validate_service
```

### 2. Define Your Service Metadata

```python
# Create exporter for your service
exporter = ServiceMetadataExporter(
    service_name="analytics_service_v3",
    service_version="3.0.0",
    service_type="data_visualization",
    base_url="https://analytics-v30-production.up.railway.app",
    supports_batch=True,
    supports_streaming=False,
    authentication_required=False,
    maintainer="analytics-team@example.com",
    documentation_url="https://docs.example.com/analytics-v3"
)
```

### 3. Add Your Variants

```python
# Add each variant your service provides
exporter.add_variant(
    variant_id="pie_chart",
    display_name="Pie Chart",
    description="Circular chart showing proportional data with segments",
    endpoint="/v3/charts/pie",
    keywords=[
        "pie", "donut", "chart", "circular", "proportion",
        "percentage", "share", "distribution", "breakdown"
    ],
    priority=2,
    layout_id="L01",
    status="production",
    use_cases=[
        "Market share analysis",
        "Budget breakdown",
        "Revenue distribution"
    ],
    best_for="Showing parts of a whole (3-7 segments)",
    avoid_when="More than 7 categories or comparing trends over time",
    required_fields=["data", "title"],
    optional_fields=["colors", "show_legend", "show_percentages"],
    output_format="html"
)

exporter.add_variant(
    variant_id="bar_chart",
    display_name="Bar Chart",
    description="Vertical or horizontal bar chart for comparing discrete categories",
    endpoint="/v3/charts/bar",
    keywords=[
        "bar", "column", "chart", "comparison", "vertical",
        "horizontal", "categorical", "discrete", "ranking"
    ],
    priority=2,
    layout_id="L02",
    status="production",
    use_cases=[
        "Sales comparison across regions",
        "Year-over-year analysis",
        "Product performance ranking"
    ],
    best_for="Comparing discrete categories (up to 15 items)",
    avoid_when="Continuous data or showing parts of a whole",
    required_fields=["data", "title"],
    optional_fields=["orientation", "colors", "show_values"],
    output_format="html"
)
```

### 4. Validate Your Configuration

```python
# Export to registry format
registry_data = exporter.export_to_registry_format()

# Validate the entire service
result = validate_service(registry_data["analytics_service_v3"])

if result.valid:
    print("✅ Service configuration is valid!")
    print(f"Variants: {exporter.get_variant_count()}")
    print(f"Keywords: {exporter.get_keyword_count()}")
else:
    print("❌ Validation failed:")
    print(result.get_summary())
```

### 5. Export to File

```python
# Export to JSON file for Director integration
exporter.export_to_file("analytics_service_metadata.json")
```

---

## Complete Example: Analytics Service v3

Here's a complete example showing how the Analytics Service would export all its variants:

```python
from src.utils.service_metadata_exporter import ServiceMetadataExporter
from src.utils.variant_validator import validate_service

# Initialize exporter
exporter = ServiceMetadataExporter(
    service_name="analytics_service_v3",
    service_version="3.0.0",
    service_type="data_visualization",
    base_url="https://analytics-v30-production.up.railway.app",
    supports_batch=True,
    supports_streaming=False,
    authentication_required=False,
    maintainer="analytics-team@example.com",
    documentation_url="https://docs.example.com/analytics-v3"
)

# Add all chart variants
exporter.add_variant(
    variant_id="pie_chart",
    display_name="Pie Chart",
    description="Circular chart showing proportional data",
    endpoint="/v3/charts/pie",
    keywords=["pie", "donut", "chart", "circular", "proportion", "percentage", "share"],
    priority=2,
    layout_id="L01",
    use_cases=["Market share", "Budget breakdown"],
    best_for="Parts of a whole (3-7 segments)",
    avoid_when="More than 7 categories",
    required_fields=["data", "title"],
    optional_fields=["colors", "show_legend"]
).add_variant(
    variant_id="bar_chart",
    display_name="Bar Chart",
    description="Bar chart for comparing discrete categories",
    endpoint="/v3/charts/bar",
    keywords=["bar", "column", "chart", "comparison", "vertical", "horizontal", "categorical"],
    priority=2,
    layout_id="L02",
    use_cases=["Sales comparison", "Ranking", "Year-over-year"],
    best_for="Comparing categories (up to 15)",
    avoid_when="Continuous data",
    required_fields=["data", "title"],
    optional_fields=["orientation", "colors"]
).add_variant(
    variant_id="line_chart",
    display_name="Line Chart",
    description="Line chart showing trends over time",
    endpoint="/v3/charts/line",
    keywords=["line", "trend", "time series", "temporal", "growth", "evolution", "progression"],
    priority=2,
    layout_id="L03",
    use_cases=["Revenue trends", "User growth", "Performance over time"],
    best_for="Continuous data and time series",
    avoid_when="Comparing discrete categories",
    required_fields=["data", "title"],
    optional_fields=["show_points", "colors"]
).add_variant(
    variant_id="scatter_plot",
    display_name="Scatter Plot",
    description="Scatter plot showing correlation between two variables",
    endpoint="/v3/charts/scatter",
    keywords=["scatter", "correlation", "relationship", "two variables", "distribution", "cluster"],
    priority=3,
    layout_id="L04",
    use_cases=["Price vs. sales", "Age vs. income", "Correlation analysis"],
    best_for="Showing relationships and correlations",
    avoid_when="Categorical data or simple comparisons",
    required_fields=["data", "title"],
    optional_fields=["show_trendline", "colors"]
).add_variant(
    variant_id="area_chart",
    display_name="Area Chart",
    description="Area chart showing cumulative trends over time",
    endpoint="/v3/charts/area",
    keywords=["area", "filled", "cumulative", "stacked", "time series", "volume", "magnitude"],
    priority=3,
    layout_id="L05",
    use_cases=["Cumulative sales", "Stacked revenues", "Volume over time"],
    best_for="Cumulative values and stacked comparisons",
    avoid_when="Simple trends (use line chart instead)",
    required_fields=["data", "title"],
    optional_fields=["stacked", "colors"]
)

# Get statistics
stats = exporter.get_stats()
print(f"Service: {stats['service_name']}")
print(f"Variants: {stats['variant_count']}")
print(f"Total keywords: {stats['total_keywords']}")
print(f"Avg keywords/variant: {stats['avg_keywords_per_variant']:.1f}")

# Validate
registry_data = exporter.export_to_registry_format()
result = validate_service(registry_data["analytics_service_v3"])

if result.valid:
    print("\n✅ All variants valid!")
    # Export to file
    exporter.export_to_file("analytics_service_metadata.json")
    print("📄 Exported to analytics_service_metadata.json")
else:
    print("\n❌ Validation errors found:")
    print(result.get_summary())
```

---

## Validation Best Practices

### 1. Run Validation During Development

```python
# Validate individual variants as you add them
variant_data = {
    "variant_id": "bubble_chart",
    "display_name": "Bubble Chart",
    "description": "Three-dimensional data visualization",
    "endpoint": "/v3/charts/bubble",
    "classification": {
        "keywords": ["bubble", "three dimensional", "size", "comparison", "scatter"]
    }
}

result = validate_variant(variant_data)
if not result.valid:
    print(result.get_summary())
```

### 2. Use Strict Mode for CI/CD

```python
# In production CI/CD pipeline, use strict mode
result = validate_service(service_data, strict=True)

if not result.valid:
    # Fail the build
    sys.exit(1)
```

### 3. Check for Common Issues

The validator checks for:

**Errors** (will fail validation):
- Missing required fields (variant_id, display_name, description, endpoint)
- Invalid variant_id format (must be snake_case)
- Insufficient keywords (minimum 5 required)
- Invalid priority (must be 1-10)
- Invalid status (must be production, beta, deprecated, experimental)
- Invalid endpoint (must start with /)
- Invalid base URL (must start with http:// or https://)

**Warnings** (won't fail validation):
- Very short description (< 10 characters)
- Many keywords (> 50)
- Duplicate keywords within a variant
- Duplicate keywords across variants
- Non-standard output formats

**Suggestions** (for improvement):
- Missing LLM guidance (best_for, avoid_when)
- Missing use cases
- Could add more descriptive information

---

## Keyword Guidelines

### How Many Keywords?

- **Minimum**: 5 keywords (enforced)
- **Recommended**: 7-15 keywords
- **Maximum**: 50 keywords (warning if exceeded)

### Keyword Quality

**Good keywords**:
```python
keywords = [
    "pie",              # Core term
    "donut",            # Alternative term
    "chart",            # Category
    "circular",         # Descriptive
    "proportion",       # Use case
    "percentage",       # Related concept
    "share",            # Business context
    "distribution",     # Mathematical term
    "breakdown"         # Action/purpose
]
```

**Avoid**:
```python
keywords = [
    "PieChart",         # ❌ CamelCase
    "pie_chart",        # ❌ Underscores (use spaces)
    "pie chart!",       # ❌ Special characters
    "pie",              # ❌ Too short (< 2 chars)
    "the pie chart visualization tool"  # ❌ Too long (> 50 chars)
]
```

### Keyword Organization Strategy

1. **Core Terms** (2-3): Primary identifiers
   - "pie", "donut", "chart"

2. **Descriptive Terms** (2-3): Visual characteristics
   - "circular", "segmented", "radial"

3. **Use Case Terms** (2-3): When to use
   - "proportion", "percentage", "share"

4. **Business Terms** (2-3): Domain language
   - "market share", "distribution", "breakdown"

5. **Alternative Terms** (2-3): Synonyms and variants
   - "pie chart", "donut chart", "circular graph"

---

## Priority Guidelines

Priority determines classification order when multiple variants match:

- **Priority 1** (Highest): Highly specific, unique variants
  - Example: SWOT matrix, BCG matrix
  - Use when: Very distinctive keywords unlikely to match others

- **Priority 2** (High): Common chart types with clear keywords
  - Example: Pie chart, bar chart, line chart
  - Use when: Standard visualizations with well-defined use cases

- **Priority 3** (Medium): Specialized variants with some overlap
  - Example: Scatter plot, bubble chart, radar chart
  - Use when: Keywords might overlap with other variants

- **Priority 5** (Default): General-purpose variants
  - Example: Generic layouts, multipurpose templates
  - Use when: Catch-all or flexible variants

- **Priority 8-10** (Low): Fallback or experimental variants
  - Example: Beta features, deprecated variants
  - Use when: Should only match if no better options

---

## Integration with Director

Once you've validated and exported your metadata:

### 1. Provide Export Endpoint (Optional)

```python
# FastAPI example
from fastapi import FastAPI
from src.utils.service_metadata_exporter import ServiceMetadataExporter

app = FastAPI()

@app.get("/api/metadata")
def get_service_metadata():
    """Export service metadata for Director integration"""
    exporter = create_analytics_exporter()  # Your service-specific function
    return exporter.export_to_registry_format()

@app.get("/api/metadata/validate")
def validate_metadata():
    """Validate service metadata"""
    exporter = create_analytics_exporter()
    registry = exporter.export_to_registry_format()
    result = validate_service(registry["analytics_service_v3"])

    return {
        "valid": result.valid,
        "errors": result.errors,
        "warnings": result.warnings,
        "stats": exporter.get_stats()
    }
```

### 2. Director Consumes Metadata

Director can then:
- Load your metadata from the registry
- Classify slides using your keywords
- Route requests to your endpoints
- Validate requests using your schemas

---

## Testing Your Integration

### Unit Test Example

```python
import pytest
from src.utils.service_metadata_exporter import ServiceMetadataExporter
from src.utils.variant_validator import validate_service

def test_analytics_service_metadata():
    """Test Analytics Service metadata export and validation"""
    exporter = ServiceMetadataExporter(
        service_name="analytics_service_v3",
        service_version="3.0.0",
        service_type="data_visualization",
        base_url="https://analytics.example.com"
    )

    # Add variants
    exporter.add_variant(
        variant_id="pie_chart",
        display_name="Pie Chart",
        description="Circular chart",
        endpoint="/v3/charts/pie",
        keywords=["pie", "donut", "chart", "circular", "proportion"]
    )

    # Validate
    registry = exporter.export_to_registry_format()
    result = validate_service(registry["analytics_service_v3"])

    assert result.valid, result.get_summary()
    assert exporter.get_variant_count() == 1
    assert exporter.get_keyword_count() >= 5
```

---

## FAQ

### Q: How often should I update my metadata?

**A**: Update metadata when:
- Adding new variants
- Changing keywords or priority
- Updating endpoints or schemas
- Changing service URLs or versions

### Q: Can I have the same keyword in multiple variants?

**A**: Yes, but you'll get warnings. The priority system handles overlaps.

### Q: What if my variant has specific input schemas?

**A**: Use `required_fields` and `optional_fields` to document them. Full JSON schema support coming in Phase 4.4.

### Q: How do I test my integration before Director adopts it?

**A**:
1. Export your metadata
2. Validate with `validate_service()`
3. Test classification manually using Director's `UnifiedSlideClassifier`
4. Verify routing using `UnifiedServiceRouter`

### Q: Can I use this for non-chart services?

**A**: Yes! Works for:
- LLM-generated content (Text Service)
- Diagram generation (Illustrator Service)
- Template-based rendering
- Any content generation service

---

## Support

For questions or issues:
1. Check validation output (`result.get_summary()`)
2. Review keyword and priority guidelines
3. Test with Director's unified classifier
4. Contact Director team for integration support

---

**Next**: See Phase 4.3 (Service Health Checks) and Phase 4.4 (Schema Export) for additional integration capabilities.

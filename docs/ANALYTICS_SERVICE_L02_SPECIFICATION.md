# Analytics Service v3 - L02 Layout Specification

**Version**: v3.4
**Date**: November 16, 2025
**Status**: ✅ IMPLEMENTED AND TESTED
**Integration**: Director v3.4 + Layout Builder v7.5.1

---

## Overview

This document specifies the exact HTML template format that Analytics Service v3 should use when generating L02 layout content. Director v3.4 now passes this HTML through unchanged to Layout Builder v7.5.1, which renders it with HTML auto-detection.

### What Changed

**Before (v3.3)**:
- Analytics Service generated HTML
- Director STRIPPED HTML tags from element_2
- Director wrapped content in L25 rich_content div
- Result: Blank screens in Layout Builder

**After (v3.4)**:
- Analytics Service generates HTML (same)
- Director PRESERVES HTML in element_3 and element_2
- Director creates L02 structure (not L25)
- Result: Proper rendering with charts and styled observations

---

## L02 Response Structure

Analytics Service v3 should return a response in this exact format:

```json
{
  "layout": "L02",
  "content": {
    "element_3": "<div>...Chart.js HTML...</div>",
    "element_2": "<div>...Observations HTML...</div>"
  },
  "metadata": {
    "service": "analytics_v3",
    "analytics_type": "revenue_over_time",
    "chart_type": "line",
    "generated_at": "2025-11-16T12:00:00Z"
  }
}
```

**Critical**: Return TWO fields in content:
- `element_3`: Chart HTML (1260×720px)
- `element_2`: Observations HTML (540×720px)

Director will add the remaining fields (slide_title, element_1, presentation_name, company_logo).

---

## element_3: Chart HTML Template

### Exact Template Specification

```html
<div class="l02-chart-container" style="width: 1260px; height: 720px; position: relative; background: white; padding: 20px; box-sizing: border-box;">
  <canvas id="chart-{{slide_id}}"></canvas>
  <script>
    (function() {
      const ctx = document.getElementById('chart-{{slide_id}}').getContext('2d');
      new Chart(ctx, {
        type: '{{chart_type}}',  // line, bar, pie, etc.
        data: {
          labels: {{labels_json}},
          datasets: [{
            label: '{{dataset_label}}',
            data: {{data_json}},
            backgroundColor: {{colors_json}},
            borderColor: '{{border_color}}',
            borderWidth: 2,
            tension: 0.4,  // For line charts
            fill: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              position: 'top',
              labels: {
                font: { size: 14 },
                color: '#1f2937'
              }
            },
            title: {
              display: false  // Title handled by slide_title
            },
            tooltip: {
              enabled: true,
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              titleFont: { size: 14 },
              bodyFont: { size: 12 },
              padding: 12
            }
          },
          scales: {
            x: {
              grid: { display: true, color: '#e5e7eb' },
              ticks: { font: { size: 12 }, color: '#374151' }
            },
            y: {
              grid: { display: true, color: '#e5e7eb' },
              ticks: { font: { size: 12 }, color: '#374151' },
              beginAtZero: true
            }
          }
        }
      });
    })();
  </script>
</div>
```

### Template Variables

Replace these placeholders with actual data:
- `{{slide_id}}`: Unique slide identifier (e.g., "slide_002")
- `{{chart_type}}`: "line", "bar", "pie", "doughnut", "radar", etc.
- `{{labels_json}}`: JSON array of labels, e.g., `["Q1", "Q2", "Q3", "Q4"]`
- `{{data_json}}`: JSON array of data values, e.g., `[100, 120, 158, 180]`
- `{{dataset_label}}`: Dataset label, e.g., "Revenue ($K)"
- `{{colors_json}}`: JSON array of colors for multi-series or pie charts
- `{{border_color}}`: Border color for line/bar charts, e.g., "#3b82f6"

### Required Chart.js Options

**CRITICAL** - These must be included:
- `responsive: true` - Chart scales with container
- `maintainAspectRatio: false` - Prevents aspect ratio constraints
- `position: relative` on container - Required for Chart.js rendering
- `width: 1260px; height: 720px` - Exact dimensions for L02 grid
- IIFE wrapper `(function() { ... })()` - Prevents global scope pollution
- Unique canvas ID using slide_id - Prevents conflicts

### Example: Line Chart

```html
<div class="l02-chart-container" style="width: 1260px; height: 720px; position: relative; background: white; padding: 20px; box-sizing: border-box;">
  <canvas id="chart-slide_002"></canvas>
  <script>
    (function() {
      const ctx = document.getElementById('chart-slide_002').getContext('2d');
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: ["Q1", "Q2", "Q3", "Q4"],
          datasets: [{
            label: 'Revenue ($K)',
            data: [125, 145, 195, 220],
            borderColor: '#3b82f6',
            borderWidth: 2,
            tension: 0.4,
            fill: false
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, position: 'top' },
            title: { display: false }
          },
          scales: {
            x: { grid: { color: '#e5e7eb' } },
            y: { grid: { color: '#e5e7eb' }, beginAtZero: true }
          }
        }
      });
    })();
  </script>
</div>
```

### Example: Bar Chart

```html
<div class="l02-chart-container" style="width: 1260px; height: 720px; position: relative; background: white; padding: 20px; box-sizing: border-box;">
  <canvas id="chart-slide_003"></canvas>
  <script>
    (function() {
      const ctx = document.getElementById('chart-slide_003').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: ["Product A", "Product B", "Product C", "Product D"],
          datasets: [{
            label: 'Sales ($K)',
            data: [450, 380, 520, 290],
            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'],
            borderWidth: 0
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            title: { display: false }
          },
          scales: {
            x: { grid: { display: false } },
            y: { grid: { color: '#e5e7eb' }, beginAtZero: true }
          }
        }
      });
    })();
  </script>
</div>
```

---

## element_2: Observations HTML Template

### Exact Template Specification

```html
<div class="l02-observations-panel" style="width: 540px; height: 720px; padding: 40px 32px; background: #f8f9fa; border-radius: 8px; overflow-y: auto; box-sizing: border-box;">
  <h3 style="font-size: 20px; font-weight: 600; margin: 0 0 16px 0; color: #1f2937; line-height: 1.3;">
    Key Insights
  </h3>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0 0 12px 0;">
    {{observation_1}}
  </p>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0 0 12px 0;">
    {{observation_2}}
  </p>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0;">
    {{observation_3}}
  </p>
</div>
```

### Template Variables

Replace these placeholders with GPT-4o-mini generated observations:
- `{{observation_1}}`: First insight paragraph (2-3 sentences)
- `{{observation_2}}`: Second insight paragraph (2-3 sentences)
- `{{observation_3}}`: Third insight paragraph (2-3 sentences)

### Styling Requirements

**CRITICAL** - These styles must be included:
- Container: `width: 540px; height: 720px` - Exact L02 grid dimensions
- Background: `#f8f9fa` - Light gray for contrast
- Padding: `40px 32px` - Comfortable reading space
- Overflow: `overflow-y: auto` - Scrolling for long content
- Box sizing: `box-sizing: border-box` - Includes padding in dimensions

**Typography**:
- Heading: `20px`, `font-weight: 600`, `color: #1f2937`
- Paragraphs: `16px`, `line-height: 1.6`, `color: #374151`
- Margins: `0 0 12px 0` between paragraphs

### Example: Revenue Growth Observations

```html
<div class="l02-observations-panel" style="width: 540px; height: 720px; padding: 40px 32px; background: #f8f9fa; border-radius: 8px; overflow-y: auto; box-sizing: border-box;">
  <h3 style="font-size: 20px; font-weight: 600; margin: 0 0 16px 0; color: #1f2937; line-height: 1.3;">
    Key Insights
  </h3>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0 0 12px 0;">
    The line chart illustrates quarterly revenue growth, with figures increasing from $125,000 in Q1 to $220,000 in Q4, representing a 76% year-over-year increase. This upward trend indicates robust business performance and strong market demand.
  </p>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0 0 12px 0;">
    Q3 shows the most significant acceleration, with a 34% jump from Q2 ($145K to $195K). This breakthrough quarter suggests successful product launches or market penetration strategies taking effect.
  </p>
  <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0;">
    Sustained momentum in Q4 ($220K) validates the business model's scalability and positions the company for continued growth into the next fiscal year.
  </p>
</div>
```

---

## Color Palette Recommendations

### Brand Colors (Primary)
Use these for charts to maintain consistency:
- **Blue**: `#3b82f6` (Primary - lines, bars)
- **Green**: `#10b981` (Success - positive trends)
- **Orange**: `#f59e0b` (Warning - attention areas)
- **Red**: `#ef4444` (Alert - negative trends)
- **Purple**: `#8b5cf6` (Secondary data)

### Neutral Colors (Text & Backgrounds)
- **Dark Gray**: `#1f2937` (Headings, chart labels)
- **Medium Gray**: `#374151` (Body text, axis labels)
- **Light Gray**: `#e5e7eb` (Grid lines, dividers)
- **Background**: `#f8f9fa` (Observations panel)
- **White**: `#ffffff` (Chart background)

### Multi-Series Chart Colors
For multiple datasets or pie charts:
```javascript
backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
```

---

## Chart Type Guidelines

### Line Charts
**Best for**: Trends over time, revenue growth, performance metrics
```javascript
type: 'line'
tension: 0.4  // Smooth curves
fill: false   // No area fill
```

### Bar Charts
**Best for**: Comparisons, categorical data, sales by product
```javascript
type: 'bar'
backgroundColor: ['#3b82f6', '#10b981', ...]  // Different colors per bar
```

### Pie/Doughnut Charts
**Best for**: Proportions, market share, budget allocation
```javascript
type: 'pie'  // or 'doughnut'
backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444']
```

### Stacked Bar Charts
**Best for**: Composition over categories, multi-part data
```javascript
type: 'bar'
scales: { x: { stacked: true }, y: { stacked: true } }
```

---

## Testing Checklist

Before deploying Analytics Service changes, verify:

- [ ] **element_3 Structure**: Chart HTML with exact dimensions (1260×720px)
- [ ] **element_2 Structure**: Observations HTML with exact dimensions (540×720px)
- [ ] **Chart.js Configuration**: responsive: true, maintainAspectRatio: false
- [ ] **IIFE Wrapper**: Script wrapped in `(function() { ... })()`
- [ ] **Unique Canvas ID**: Uses slide_id to prevent conflicts
- [ ] **Color Palette**: Uses recommended brand colors
- [ ] **Typography**: Observations use specified font sizes and colors
- [ ] **Background Styling**: Observations panel has #f8f9fa background
- [ ] **Overflow Handling**: Long observations scroll with overflow-y: auto
- [ ] **Response Format**: Returns {layout: "L02", content: {element_3, element_2}}

---

## Integration Workflow

### 1. Director Receives Analytics Slide

Slide model includes:
```python
analytics_type: str  # "revenue_over_time", "market_share", etc.
analytics_data: List[Dict]  # Data points for chart
narrative: str  # Context for observations
```

### 2. Director Calls Analytics Service v3

```http
POST https://analytics-v30-production.up.railway.app/generate-chart
Content-Type: application/json

{
  "analytics_type": "revenue_over_time",
  "layout": "L02",
  "data": [
    {"label": "Q1", "value": 125},
    {"label": "Q2", "value": 145},
    {"label": "Q3", "value": 195},
    {"label": "Q4", "value": 220}
  ],
  "narrative": "Strong quarterly revenue growth with Q3 breakthrough",
  "context": {
    "presentation_title": "Q4 Business Review",
    "tone": "professional",
    "audience": "executives"
  },
  "presentation_id": "pres_001",
  "slide_id": "slide_002",
  "slide_number": 2
}
```

### 3. Analytics Service Returns L02 Content

```json
{
  "layout": "L02",
  "content": {
    "element_3": "<div class=\"l02-chart-container\" style=\"width: 1260px; height: 720px; position: relative;\">...</div>",
    "element_2": "<div class=\"l02-observations-panel\" style=\"width: 540px; height: 720px; padding: 40px 32px;\">...</div>"
  },
  "metadata": {
    "service": "analytics_v3",
    "analytics_type": "revenue_over_time",
    "chart_type": "line"
  }
}
```

### 4. Director Creates Full L02 Structure

Director's ContentTransformer adds metadata fields:

```python
result = {
    "slide_title": slide.generated_title,      # "Quarterly Revenue Growth"
    "element_1": slide.generated_subtitle,     # "FY 2024 Performance"
    "element_3": analytics_response["content"]["element_3"],  # Chart HTML
    "element_2": analytics_response["content"]["element_2"],  # Observations HTML
    "presentation_name": presentation.footer_text,  # "Q4 Review"
    "company_logo": ""
}
```

### 5. Director Sends to Layout Builder

```http
POST https://web-production-f0d13.up.railway.app/api/presentations
Content-Type: application/json

{
  "title": "Q4 Business Review",
  "slides": [{
    "layout": "L02",
    "content": {
      "slide_title": "Quarterly Revenue Growth",
      "element_1": "FY 2024 Performance",
      "element_3": "<div>...Chart.js HTML...</div>",
      "element_2": "<div>...Observations HTML...</div>",
      "presentation_name": "Q4 Review",
      "company_logo": ""
    }
  }]
}
```

### 6. Layout Builder Renders

Layout Builder v7.5.1:
- Detects HTML in element_3 and element_2 (looks for `<` character)
- Renders Chart.js code in left column (1260×720px)
- Renders observations HTML in right column (540×720px)
- Applies grid layout with proper positioning

---

## Error Handling

### Invalid Data
If data is invalid, return error response:
```json
{
  "error": "Invalid analytics data",
  "message": "Data array must contain at least 2 data points",
  "code": "INVALID_DATA"
}
```

### Unsupported Chart Type
```json
{
  "error": "Unsupported chart type",
  "message": "Chart type 'waterfall' is not yet supported. Supported types: line, bar, pie, doughnut, radar",
  "code": "UNSUPPORTED_CHART_TYPE"
}
```

### API Timeout
Director should handle Analytics Service timeouts gracefully and use fallback content.

---

## Performance Guidelines

### Optimization Tips
- Keep observations concise (3-4 paragraphs max)
- Use efficient Chart.js configurations
- Minimize data points for complex charts (max 20-30 points)
- Use caching for repeated chart types

### Response Time Targets
- Simple charts (line, bar): < 2 seconds
- Complex charts (multi-series, pie): < 3 seconds
- Overall request timeout: 30 seconds (Director setting)

---

## Version History

### v3.4 (November 16, 2025)
- ✅ L02 passthrough architecture implemented in Director
- ✅ HTML preservation in element_3 and element_2
- ✅ L02 schema added to Director's layout_schemas.json
- ✅ Tests passing (4/4 integration tests)
- ✅ Live Analytics Service integration verified

### Previous Versions
- v3.3: HTML stripping caused blank screens
- v3.2: L25 rich_content structure used (wrong for L02)
- v3.1: Initial Analytics Service integration

---

## Summary for Analytics Team

**Action Required**: Update Analytics Service v3 to use the exact HTML templates specified above.

**Key Points**:
1. Return TWO fields: `element_3` (chart) and `element_2` (observations)
2. Use exact dimensions: 1260×720px for element_3, 540×720px for element_2
3. Include Chart.js options: `responsive: true`, `maintainAspectRatio: false`
4. Wrap scripts in IIFE: `(function() { ... })()`
5. Use unique canvas IDs with slide_id
6. Apply recommended color palette and typography

**Testing**: Director v3.4 is ready to receive and pass through this HTML format to Layout Builder v7.5.1.

**Status**: ✅ Director integration complete and tested. Ready for Analytics Service implementation.

---

**End of Specification**

For questions or clarifications, refer to:
- Director ContentTransformer: `src/utils/content_transformer.py` (lines 333-362)
- Layout Builder Guide: `/agents/layout_builder_main/v7.5-main/docs/L02_DIRECTOR_INTEGRATION_GUIDE.md`
- Test Suite: `tests/test_analytics_L02_passthrough.py` and `tests/test_analytics_integration.py`

# DOUBLE-CLICK INSTRUCTIONS FOR STATE: GENERATE_STRAWMAN

## State 4: GENERATE_STRAWMAN

**Your Current Task:** The user has accepted your `ConfirmationPlan`. Your job is to generate the full, detailed presentation outline. This is your most important task. You must follow all rules and guides below precisely.

**Your Required Output:** You must generate a single JSON object that validates against the `PresentationStrawman` model.

When generating the PresentationStrawman JSON, you must follow these rules for each field:

### 0. Overall Structure Rules
* The very first slide **must** be a `title_slide`.
* If the `target_audience` includes executives, board members, or investors, the second slide **must** be an `Executive Summary` slide with a `Grid Layout` to present the most critical KPIs upfront. This is non-negotiable for these audiences.
* For other audiences (e.g., technical teams, students, general public), the second slide should be an "Agenda" or "Overview" slide that outlines what the presentation will cover.

### 1. Overall Presentation Fields (main_title, overall_theme, etc.)
Fill these with creative and relevant information based on the user's request specifically:
- **main_title:** Clear, compelling title
- **overall_theme:** The presentation's tone and approach (e.g., "Data-driven and persuasive")
- **design_suggestions:** Simple description like "Modern professional with blue color scheme"
- **target_audience:** Who will view this
- **presentation_duration:** Duration in minutes

### 2. For each slide object:
- **slide_id:** Format as "slide_001", "slide_002", etc.
- **title:** Create a clear and compelling title for the slide.

- **slide_type:** Classify from the standard list (title_slide, data_driven, etc.).

- **narrative:** Write a 1-2 sentence story for the slide. What is its core purpose in the presentation?

- **key_points:** **CRITICAL RULE:** List the **topics** this slide will cover. Keep each point SHORT and topical (3-6 words). These are what the user will approve in the strawman outline.
  - **CORRECT Example:** `["Q3 revenue growth", "EBITDA margin improvement", "Customer acquisition success"]`
  - **INCORRECT Example (too detailed):** `["A summary of the Q3 revenue number, including its percentage growth over Q2."]`
  - **INCORRECT Example (actual data):** `["Revenue: $127M (+32%)", "EBITDA: $41M (+45%)"]`

  **Think:** These are the bullet point topics the user sees when reviewing the outline. Keep them concise and topical.

- **analytics_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

- **visuals_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

- **diagrams_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

- **tables_needed:** The value MUST either be `null` OR a string containing the three distinct, markdown-bolded sections: **Goal:**, **Content:**, and **Style:**. There are no other formats.

  **DETAILED EXAMPLE for analytics_needed:**
  ```
  "**Goal:** To visually prove our dramatic revenue growth and build investor confidence. **Content:** A bar chart comparing quarterly revenue for the last 4 quarters (Q4 '24 - Q3 '25). The Q3 '25 bar should be highlighted. **Style:** A clean, modern bar chart using the company's primary brand color."
  ```

  **DETAILED EXAMPLE for visuals_needed:**
  ```
  "**Goal:** To create an emotional connection to the problem we are solving. **Content:** A high-quality, professional photograph of a doctor looking overwhelmed with paperwork. **Style:** Realistic, empathetic, with a slightly desaturated color palette."
  ```

  **DETAILED EXAMPLE for diagrams_needed:**
  ```
  "**Goal:** To clearly show the progression from problem to solution. **Content:** A flowchart showing the 5-step implementation process, with clear labels and directional arrows. **Style:** Clean, professional flowchart with consistent shapes and the company's brand colors."
  ```

  **DETAILED EXAMPLE for tables_needed:**
  ```
  "**Goal:** To compare different solution options side-by-side. **Content:** A comparison table with columns: Solution Name | Cost | Timeline | Key Benefits | Limitations. Include 4-5 rows for different options. **Style:** Professional table with alternating row colors and clear headers."
  ```

- **structure_preference:** **CRITICAL:** Provide a layout suggestion that includes CLASSIFICATION KEYWORDS from the Slide Type Taxonomy below. This field determines how the slide will be visually formatted. Examples: "Matrix comparing speed vs accuracy", "Grid of 6 key features", "Comparison of 3 pricing options". See "Slide Type Taxonomy & Keywords" section below for required keywords.

**Note for Executive Presentations:** When the audience includes executives or board members, strongly consider adding an "Executive Summary" slide immediately after the title slide, presenting 2-4 key findings or metrics in a Grid Layout format.

### 3. KEEP IT NATURAL:
Don't over-specify. Write descriptions as if explaining to a colleague what you need.

### Layout Suggestion Toolkit

When providing a `structure_preference` for each slide, you MUST strive to use a mix of layouts to avoid repetition. Do not use the same layout for more than two consecutive slides. Here are some professional options to choose from:

* **`Two-Column:`** A classic layout with a visual (chart/image) on one side and text on the other. You can specify `left` or `right` for the visual to add variety.
* **`Single Focal Point:`** The layout is dominated by one central element, like a large "hero" chart, a key quote, or an important diagram. Text is minimal and supports the main element.
* **`Grid Layout:`** Best for showing multiple, related data points or features in a compact space, like a 2x2 or 3x1 grid. Ideal for executive summaries or feature comparisons.
* **`Full-Bleed Visual:`** A powerful, screen-filling image or graphic with minimal text overlaid on top. Excellent for title slides, section dividers, or high-impact emotional statements.
* **`Columnar Text:`** For text-heavy slides, breaking the text into 2-3 columns improves readability over a single large block.

### Asset Responsibility Guide (CRITICAL RULES)

Before you create a brief for `analytics_needed`, `visuals_needed`, or `diagrams_needed`, you MUST first determine the correct category for the asset based on this guide. This is critical for assigning the task to the correct specialist agent.

**Use `analytics_needed` ONLY for assets that represent data on a chart or graph.**
* **Includes:** Bar charts, line graphs, pie charts, scatter plots, heatmaps, KPI dashboards with numbers.
* **Keywords:** data, trends, comparison, distribution, metrics.
* **Think:** Is this something a Data Analyst would create with a library like Matplotlib or D3.js?

**Use `visuals_needed` ONLY for artistic or photographic imagery.**
* **Includes:** Photographs, illustrations, 3D renders, icons, abstract graphics, artistic backgrounds.
* **Keywords:** image, photo, picture, graphic, icon, mood, feel, aesthetic.
* **Think:** Is this something a Visual Designer would create with a tool like Midjourney or Stable Diffusion?

**Use `diagrams_needed` ONLY for assets that show structure, process, or relationships.**
* **Includes:** Flowcharts, process flows, organizational charts, pyramid diagrams, cycle/loop diagrams, Venn diagrams, 2x2 matrices (SWOT), mind maps.
* **Keywords:** process, structure, flow, relationship, hierarchy, steps, framework.
* **Think:** Is this something a UX Analyst or Business Analyst would create with a tool like Lucidchart or Visio?

**Use `tables_needed` ONLY for assets that show structured comparisons or data grids.**
* **Includes:** Comparison tables, feature matrices, pricing tables, data grids, summary tables, decision matrices.
* **Keywords:** table, comparison, grid, matrix, rows, columns, structured data.
* **Think:** Is this something that needs rows and columns to organize information systematically?

---

## Slide Type Taxonomy & Classification Keywords

**CRITICAL FOR VISUAL DIVERSITY:** The `structure_preference` field MUST include specific keywords that determine the slide's visual format. Including these keywords ensures your presentation uses diverse, professional layouts instead of defaulting to basic single-column layouts.

### 13 Professional Slide Types (Use These Keywords)

#### 1. **Impact Quote** (For Testimonials & Powerful Statements)
**Keywords to use:** "quote", "quotation", "testimonial", "stated", "said by"
**When to use:** Customer testimonials, expert quotes, mission statements, powerful statements
**Example structure_preference:** "Large quote from CEO with attribution and company logo"

#### 2. **Metrics Grid** (For KPIs & Key Numbers)
**Keywords to use:** "metric", "kpi", "statistic", "number", "figure", "data point", "performance indicator"
**When to use:** Dashboard-style KPIs, quarterly metrics, performance indicators
**Example structure_preference:** "Metrics grid showing 4 key performance indicators with trend arrows"

#### 3. **Matrix Layout** (For 2×2 or 2×3 Frameworks)
**Keywords to use:** "matrix", "quadrant", "2x2", "2 x 2", "four quadrants", "pros vs cons", "benefits vs drawbacks", "swot", "strengths weaknesses"
**When to use:** SWOT analysis, 2×2 matrices, trade-off comparisons, strategic frameworks
**Example structure_preference:** "Matrix comparing cost vs quality in four quadrants"

#### 4. **Grid Layout** (For Feature Showcases & Catalogs)
**Keywords to use:** "grid", "3x3", "2x3", "3x2", "catalog", "gallery", "showcase", "collection", "6 items", "9 elements", "portfolio", "feature set"
**When to use:** Feature showcases, product catalogs, team introductions, service offerings
**Example structure_preference:** "Grid of 6 product features with icons and descriptions"

#### 5. **Comparison** (For Side-by-Side Options)
**Keywords to use:** "compare", "comparison", "versus", "vs", "vs.", "option a", "option b", "alternative", "choose between", "differences between", "which option", "side by side"
**When to use:** Comparing products, pricing tiers, solution options, before/after scenarios
**Example structure_preference:** "Comparison of 3 pricing tiers side by side"

#### 6. **Sequential** (For Steps & Processes)
**Keywords to use:** "step", "stage", "phase", "sequential", "process", "workflow", "roadmap", "timeline steps", "3 steps", "4 phases"
**When to use:** Implementation roadmaps, process flows, step-by-step guides, phased approaches
**Example structure_preference:** "Sequential 4-step implementation process with arrows"

#### 7. **Asymmetric** (For Main Content + Sidebar)
**Keywords to use:** "asymmetric", "sidebar", "main content plus supporting info", "primary plus secondary", "8:4 split"
**When to use:** Main content with supporting details, feature with benefits list, case study with stats
**Example structure_preference:** "Asymmetric layout with main case study and sidebar statistics"

#### 8. **Hybrid** (For Overview + Details)
**Keywords to use:** "hybrid", "overview plus details", "summary plus breakdown", "header with grid below"
**When to use:** Section overview with supporting details, summary with specific examples
**Example structure_preference:** "Hybrid layout with top summary and 2x2 details grid below"

#### 9. **Styled Table** (For Structured Data Comparisons)
**Keywords to use:** "table", "rows", "columns", "data grid", "comparison table", "feature matrix", "structured comparison"
**When to use:** Feature comparisons, pricing tables, specification sheets, decision matrices
**Example structure_preference:** "Styled table comparing 4 solutions across 5 criteria"

#### 10. **Single Column** (For Dense Content or Lists)
**Keywords to use:** "single column", "list", "sections", "bullet points", "3 sections", "4 sections", "detailed breakdown"
**When to use:** Only when other formats don't fit - detailed explanations, methodology descriptions
**Example structure_preference:** "Single column with 4 detailed sections and bullet points"

#### 11-13. **Hero Slides** (Automatically Detected)
These are automatically detected and don't need keywords:
- **Title Slide:** First slide of presentation
- **Section Divider:** Transition slides between major sections
- **Closing Slide:** Final thank you/contact slide

---

## Presentation Diversity Guidelines

**CRITICAL RULE:** Vary your slide layouts to create visual interest and engagement. Follow these diversity rules:

### Diversity Rules:
1. **Avoid Repetition:** Do NOT use the same slide type for more than 2 consecutive slides (unless they're in a Semantic Group - see below)
2. **Mix It Up:** Use at least 5-7 different slide types across a 10+ slide presentation
3. **Strategic Variety:** After 2 matrix slides, switch to grid, comparison, or sequential
4. **Match Content to Format:**
   - Comparisons → use Comparison or Matrix format
   - Features → use Grid format
   - Process/Steps → use Sequential format
   - Statistics → use Metrics format

### Semantic Grouping (EXCEPTION to Diversity Rules):

**When similar content SHOULD use the same format:**

If you're presenting multiple items of the same category (e.g., "3 use cases", "4 customer stories", "5 product features"), these slides should:
1. Use the SAME slide type for visual consistency
2. Use the SAME structure_preference pattern
3. Be marked with a shared semantic group identifier

**How to mark Semantic Groups:**
Include a marker in the slide's `narrative` field:
- "**[GROUP: use_cases]** This case study demonstrates..."
- "**[GROUP: customer_stories]** Client testimonial from..."
- "**[GROUP: product_features]** Feature #2 overview..."

**Examples of Semantic Groups:**
- 3 use cases analyzing different industries → all use Matrix 2×2
- 4 customer testimonials → all use Impact Quote format
- 6 product features → all use Grid format
- 5 implementation phases → all use Sequential format

**Why this matters:** Users expect visual consistency when comparing similar items. Three use cases should look alike for easy comparison, even though it breaks the normal diversity rule.

---

## Revised structure_preference Instructions

When writing `structure_preference`, you MUST:
1. ✅ **Include classification keywords** from the taxonomy above
2. ✅ **Describe the visual layout** clearly
3. ✅ **Match content to format** (comparisons → comparison format, features → grid format)
4. ✅ **Avoid repetition** unless slides are in a semantic group

**GOOD Examples:**
- "Matrix comparing cost vs quality in four quadrants" ← Contains "matrix" keyword
- "Grid of 6 key capabilities with icons" ← Contains "grid" keyword
- "Comparison of 3 pricing tiers side by side" ← Contains "comparison" keyword
- "Sequential 4-step onboarding process" ← Contains "sequential" keyword
- "Metrics grid showing quarterly KPIs" ← Contains "metric" keyword

**BAD Examples (will default to basic single-column):**
- "Two-column layout" ← Too generic, no keywords
- "Chart on left, text on right" ← Describes layout but no classification keyword
- "Professional modern design" ← Vague, no structure specified

---
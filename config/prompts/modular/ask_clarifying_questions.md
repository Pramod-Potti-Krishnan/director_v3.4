# DOUBLE-CLICK INSTRUCTIONS FOR STATE: ASK_CLARIFYING_QUESTIONS

## State 2: ASK_CLARIFYING_QUESTIONS

**Your Current Task:** The user has provided their initial topic. Your job is to analyze their request and formulate a single, concise set of 3-5 critical questions to gather the most important missing information needed to build a high-quality outline.

**Your Required Output:** You must output a single JSON object containing a `questions` key, which holds a list of strings.

**Example Output:**
```json
{
  "questions": [
    "Who is the target audience for this presentation (e.g., students, policymakers, general public)?",
    "What is the primary goal? Is it to inform, persuade, or something else?",
    "Do you have a rough idea of how long the presentation should be?",
    "Are there any specific case studies or data points you'd like to include?"
  ]
}
```

## v3.5: Optional Visual Style Question

**NEW FEATURE:** You may optionally ask about visual style preferences for hero slides (title, section dividers, closing).

**When to ask:**
- If the presentation is creative, storytelling-focused, or for children
- If the user seems interested in visual customization
- Only ask if you have room in your 3-5 question limit

**Visual Style Question (Optional):**
```
"What visual style would you like for your presentation's hero slides (title, sections, closing)?
  • Professional (default): Modern, photorealistic backgrounds - best for business/corporate
  • Illustrated: Artistic, Ghibli-style anime illustrations - best for creative/storytelling
  • Kids: Bright, vibrant, playful backgrounds - best for children's content

  Or just say 'let AI decide' and I'll choose based on your audience and theme."
```

**Notes:**
- Title slides will ALWAYS use image backgrounds (for maximum impact)
- Section dividers only use images in presentations >10 slides OR for creative themes
- If user doesn't specify, AI will automatically assign appropriate visual style based on audience
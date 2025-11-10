"""
Slide Type Classifier for Director v3.4
========================================

Classifies slides into 13 taxonomy types for routing to specialized generators.

Classification Strategy:
1. L29 Hero Classification (position-based)
2. L25 Content Classification (10-priority heuristics)
"""

import re
from typing import Optional, Dict, Any, List
from src.models.agents import Slide
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class SlideTypeClassifier:
    """
    Classifies slides into 13 taxonomy types.

    L29 Hero Types (3):
    - title_slide: First slide
    - section_divider: Middle divider slides
    - closing_slide: Last slide

    L25 Content Types (10):
    - impact_quote: Quote-focused slides
    - metrics_grid: Metric/statistic cards
    - matrix_2x2: 4-quadrant matrix
    - grid_3x3: 9-cell grid
    - styled_table: Tabular data
    - bilateral_comparison: Two-column comparison
    - sequential_3col: 3-step process
    - hybrid_1_2x2: Overview + 2x2 grid
    - asymmetric_8_4: Main + sidebar
    - single_column: Dense single-column (default)
    """

    # Keywords for classification (v3.4-diversity: Expanded keyword sets)
    # Aligned with generate_strawman.md taxonomy

    QUOTE_KEYWORDS = {
        "quote", "quotation", "testimonial", "said", "stated",
        "said by", "according to", "states that", "believes that",
        "mission statement", "vision statement", "powerful statement"
    }

    METRICS_KEYWORDS = {
        "metric", "kpi", "statistic", "number", "figure", "data point",
        "performance indicator", "key metric", "dashboard", "scorecard",
        "trend arrow", "growth", "improvement", "quarterly metric"
    }

    MATRIX_KEYWORDS = {
        "matrix", "quadrant", "2x2", "2 x 2", "four quadrants",
        "pros vs cons", "pros and cons", "benefits vs drawbacks",
        "trade-offs", "trade offs", "strengths weaknesses",
        "swot", "swot analysis", "strategic framework",
        "comparing", "comparison matrix"
    }

    GRID_KEYWORDS = {
        "grid", "3x3", "2x3", "3x2", "2x2 grid", "nine",
        "catalog", "gallery", "showcase", "collection",
        "6 items", "9 elements", "6 features", "9 features",
        "portfolio", "feature set", "capabilities", "offerings"
    }

    TABLE_KEYWORDS = {
        "table", "rows", "columns", "data grid", "comparison table",
        "feature matrix", "pricing table", "specification",
        "structured comparison", "decision matrix", "summary table"
    }

    COMPARISON_KEYWORDS = {
        "compare", "comparison", "versus", "vs", "vs.", "v.s.",
        "option a", "option b", "option c", "alternative",
        "choose between", "differences between", "which option",
        "side by side", "side-by-side", "compare and contrast",
        "tier 1", "tier 2", "tier 3", "plan comparison"
    }

    SEQUENTIAL_KEYWORDS = {
        "step", "stage", "phase", "sequential", "process",
        "workflow", "roadmap", "timeline steps",
        "3 steps", "4 steps", "5 steps", "three steps", "four steps",
        "4 phases", "5 phases", "implementation", "onboarding",
        "journey", "pathway", "progression"
    }

    HYBRID_KEYWORDS = {
        "hybrid", "overview + details", "overview plus details",
        "summary + breakdown", "summary plus breakdown",
        "header with grid", "top summary", "overview with"
    }

    ASYMMETRIC_KEYWORDS = {
        "asymmetric", "sidebar", "main + supporting",
        "main content plus supporting", "primary plus secondary",
        "8:4 split", "main and sidebar", "case study with stats"
    }

    # v3.4-diversity: Single column keywords (for explicit detection)
    SINGLE_COLUMN_KEYWORDS = {
        "single column", "list", "sections", "bullet points",
        "3 sections", "4 sections", "5 sections",
        "detailed breakdown", "comprehensive list"
    }

    @classmethod
    def classify(cls, slide: Slide, position: int, total_slides: int) -> str:
        """
        Classify a slide into one of 13 taxonomy types.

        Args:
            slide: Slide object to classify
            position: Slide position (1-indexed)
            total_slides: Total number of slides

        Returns:
            slide_type: One of 13 taxonomy types
        """
        logger.info(f"Classifying slide {position}/{total_slides}: {slide.title}")

        # Step 1: Check for L29 Hero types (position-based)
        hero_type = cls._classify_hero(slide, position, total_slides)
        if hero_type:
            logger.info(f"  → Classified as hero: {hero_type}")
            return hero_type

        # Step 2: Classify as L25 Content type (heuristic-based)
        content_type = cls._classify_content(slide)
        logger.info(f"  → Classified as content: {content_type}")
        return content_type

    @classmethod
    def _classify_hero(cls, slide: Slide, position: int, total_slides: int) -> Optional[str]:
        """
        Classify as L29 hero slide based on position and indicators.

        Args:
            slide: Slide object
            position: Slide position (1-indexed)
            total_slides: Total slides in presentation

        Returns:
            Hero type or None if not hero
        """
        # First slide → title_slide
        if position == 1:
            return "title_slide"

        # Last slide → closing_slide
        if position == total_slides:
            return "closing_slide"

        # Middle slides: check for section divider indicators
        title_lower = slide.title.lower()
        narrative_lower = slide.narrative.lower()

        divider_indicators = {
            "section", "part", "chapter", "agenda", "overview",
            "introduction to", "moving to", "next:"
        }

        # Check if title or narrative contains divider indicators
        combined_text = f"{title_lower} {narrative_lower}"
        for indicator in divider_indicators:
            if indicator in combined_text:
                # Additional check: slide should be relatively simple (few key points)
                if len(slide.key_points) <= 3:
                    return "section_divider"

        # Not a hero slide
        return None

    @classmethod
    def _classify_content(cls, slide: Slide) -> str:
        """
        Classify as L25 content type using 10-priority heuristics.

        Priority Order:
        1. Quote → impact_quote
        2. Metrics → metrics_grid
        3. Matrix → matrix_2x2
        4. Grid → grid_3x3
        5. Table → styled_table
        6. Comparison → bilateral_comparison
        7. Sequential → sequential_3col
        8. Hybrid → hybrid_1_2x2
        9. Asymmetric → asymmetric_8_4
        10. Default → single_column

        Args:
            slide: Slide object

        Returns:
            L25 content type (one of 10 types)
        """
        # Combine all text for analysis
        text_corpus = cls._build_text_corpus(slide)

        # Priority 1: Quote detection
        if cls._contains_keywords(text_corpus, cls.QUOTE_KEYWORDS):
            return "impact_quote"

        # Priority 2: Metrics detection
        if cls._contains_keywords(text_corpus, cls.METRICS_KEYWORDS):
            # Check for 3-card pattern (common for metrics)
            if "3" in text_corpus or "three" in text_corpus:
                return "metrics_grid"

        # Priority 3: Matrix detection
        if cls._contains_keywords(text_corpus, cls.MATRIX_KEYWORDS):
            return "matrix_2x2"

        # Priority 4: Grid detection
        if cls._contains_keywords(text_corpus, cls.GRID_KEYWORDS):
            return "grid_3x3"

        # Priority 5: Table detection
        if slide.tables_needed or cls._contains_keywords(text_corpus, cls.TABLE_KEYWORDS):
            return "styled_table"

        # Priority 6: Comparison detection
        if cls._contains_keywords(text_corpus, cls.COMPARISON_KEYWORDS):
            return "bilateral_comparison"

        # Priority 7: Sequential detection
        if cls._contains_keywords(text_corpus, cls.SEQUENTIAL_KEYWORDS):
            return "sequential_3col"

        # Priority 8: Hybrid detection
        if cls._contains_keywords(text_corpus, cls.HYBRID_KEYWORDS):
            return "hybrid_1_2x2"

        # Priority 9: Asymmetric detection
        if cls._contains_keywords(text_corpus, cls.ASYMMETRIC_KEYWORDS):
            return "asymmetric_8_4"

        # Priority 10: Default to single_column
        # Used for dense, detailed content that doesn't fit other patterns
        return "single_column"

    @classmethod
    def _build_text_corpus(cls, slide: Slide) -> str:
        """
        Build combined text corpus from slide for analysis.

        Args:
            slide: Slide object

        Returns:
            Lowercase combined text
        """
        parts = [
            slide.title,
            slide.narrative,
            " ".join(slide.key_points),
            slide.structure_preference or "",
            slide.analytics_needed or "",
            slide.diagrams_needed or "",
            slide.tables_needed or ""
        ]

        return " ".join(parts).lower()

    @classmethod
    def _contains_keywords(cls, text: str, keywords: set) -> bool:
        """
        Check if text contains any of the keywords.

        Args:
            text: Text to search (already lowercase)
            keywords: Set of keywords to match

        Returns:
            True if any keyword found
        """
        for keyword in keywords:
            if keyword in text:
                return True
        return False

    @classmethod
    def detect_semantic_group(cls, slide: Slide) -> Optional[str]:
        """
        Detect if slide is part of a semantic group (v3.4-diversity feature).

        Looks for markers like **[GROUP: use_cases]** in the narrative field.

        Args:
            slide: Slide object

        Returns:
            Group identifier (e.g., "use_cases") or None if not in a group
        """
        narrative = slide.narrative or ""

        # Pattern: **[GROUP: group_name]**
        import re
        pattern = r'\*\*\[GROUP:\s*([a-z_]+)\]\*\*'
        match = re.search(pattern, narrative, re.IGNORECASE)

        if match:
            group_name = match.group(1).lower()
            logger.debug(f"Detected semantic group: '{group_name}' in slide '{slide.title}'")
            return group_name

        return None

    @classmethod
    def classify_batch(cls, slides: List[Slide]) -> List[str]:
        """
        Classify multiple slides in batch.

        Args:
            slides: List of Slide objects

        Returns:
            List of slide types (same order as input)
        """
        total_slides = len(slides)
        slide_types = []

        for position, slide in enumerate(slides, start=1):
            slide_type = cls.classify(slide, position, total_slides)
            slide_types.append(slide_type)

        return slide_types

    @classmethod
    def get_classification_reasoning(cls, slide: Slide, position: int, total_slides: int) -> Dict[str, Any]:
        """
        Get detailed classification reasoning for debugging.

        Args:
            slide: Slide object
            position: Slide position
            total_slides: Total slides

        Returns:
            Dict with classification details and reasoning
        """
        slide_type = cls.classify(slide, position, total_slides)
        text_corpus = cls._build_text_corpus(slide)

        reasoning = {
            "slide_type": slide_type,
            "position": position,
            "total_slides": total_slides,
            "is_first": position == 1,
            "is_last": position == total_slides,
            "matched_keywords": [],
            "classification_path": []
        }

        # Determine classification path
        if position == 1:
            reasoning["classification_path"].append("Position-based: First slide → title_slide")
        elif position == total_slides:
            reasoning["classification_path"].append("Position-based: Last slide → closing_slide")
        else:
            # Check content-based classification
            if cls._contains_keywords(text_corpus, cls.QUOTE_KEYWORDS):
                reasoning["matched_keywords"].extend(list(cls.QUOTE_KEYWORDS & set(text_corpus.split())))
                reasoning["classification_path"].append("Priority 1: Quote keywords → impact_quote")

            elif cls._contains_keywords(text_corpus, cls.METRICS_KEYWORDS):
                reasoning["matched_keywords"].extend(list(cls.METRICS_KEYWORDS & set(text_corpus.split())))
                reasoning["classification_path"].append("Priority 2: Metrics keywords → metrics_grid")

            # ... similar for other priorities

            if not reasoning["matched_keywords"]:
                reasoning["classification_path"].append("Priority 10: Default → single_column")

        return reasoning


# Convenience function

def classify_slide(slide: Slide, position: int, total_slides: int) -> str:
    """
    Classify a slide (convenience function).

    Args:
        slide: Slide object
        position: Slide position (1-indexed)
        total_slides: Total slides in presentation

    Returns:
        Classified slide type
    """
    return SlideTypeClassifier.classify(slide, position, total_slides)


# Example usage
if __name__ == "__main__":
    print("Slide Type Classifier")
    print("=" * 70)
    print("\nClassification Strategy:")
    print("  L29 Hero Types (3):")
    print("    • title_slide: First slide (position-based)")
    print("    • section_divider: Middle divider slides (keyword-based)")
    print("    • closing_slide: Last slide (position-based)")
    print("\n  L25 Content Types (10):")
    print("    Priority 1: impact_quote (quote keywords)")
    print("    Priority 2: metrics_grid (metric keywords)")
    print("    Priority 3: matrix_2x2 (matrix keywords)")
    print("    Priority 4: grid_3x3 (grid keywords)")
    print("    Priority 5: styled_table (table keywords)")
    print("    Priority 6: bilateral_comparison (comparison keywords)")
    print("    Priority 7: sequential_3col (sequential keywords)")
    print("    Priority 8: hybrid_1_2x2 (hybrid keywords)")
    print("    Priority 9: asymmetric_8_4 (asymmetric keywords)")
    print("    Priority 10: single_column (default)")
    print("\n" + "=" * 70)

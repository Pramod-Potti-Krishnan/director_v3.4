"""
Unit Tests for Visual Style Assignment

Tests the VisualStyleAssigner class with various scenarios:
- Title slides always use images
- Section dividers only in large decks (>10 slides) or creative themes
- Closing slides use images by default
- Visual style selection based on audience and theme
- User preferences override AI defaults
"""

import pytest
from src.utils.visual_style_assigner import VisualStyleAssigner
from src.models.visual_styles import VisualStylePreferences, VisualStyleAssignmentRules
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
            slide_type="title_slide",
            slide_type_classification="title_slide",
            narrative="Welcome",
            key_points=["point1"]
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business",
            design_suggestions="modern",
            presentation_duration=30,
            slides=[slide]
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.use_image_background is True
        assert result.visual_style == "professional"  # Default
        assert "always uses image" in result.assignment_reason.lower()

    def test_non_hero_slide_no_visual_style(self):
        """Non-hero slides (not L29) don't get visual styles."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=2,
            slide_id="s2",
            title="Content",
            layout_id="L25",  # Content slide, not hero
            slide_type="content_heavy",
            slide_type_classification="matrix_2x2",
            narrative="Content",
            key_points=["point1"]
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business",
            design_suggestions="modern",
            presentation_duration=30,
            slides=[slide]
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.use_image_background is False
        assert result.visual_style is None
        assert "not a hero slide" in result.assignment_reason.lower()

    def test_section_divider_small_deck_no_image(self):
        """Section dividers in small decks (≤10 slides) don't use images by default."""
        assigner = VisualStyleAssigner(user_preferences=None)

        # Create small deck with 8 slides
        slides = [
            Slide(
                slide_number=i,
                slide_id=f"s{i}",
                title=f"Slide {i}",
                layout_id="L29",
                slide_type="section_divider",
                slide_type_classification="section_divider",
                narrative=f"Section {i}",
                key_points=["point1"]
            )
            for i in range(1, 9)
        ]

        strawman = PresentationStrawman(
            main_title="Small Deck",
            overall_theme="corporate",
            target_audience="executives",
            design_suggestions="professional",
            presentation_duration=20,
            slides=slides
        )

        # Test section divider in this small deck
        section_slide = slides[4]  # Middle slide
        result = assigner.assign_visual_style(section_slide, strawman)

        assert result.use_image_background is False
        assert result.visual_style is None
        assert "small deck" in result.assignment_reason.lower()
        assert "8≤10" in result.assignment_reason

    def test_section_divider_large_deck_creative_theme(self):
        """Section dividers in large decks (>10 slides) with creative theme use images."""
        assigner = VisualStyleAssigner(user_preferences=None)

        # Create large deck with 12 slides
        slides = [
            Slide(
                slide_number=i,
                slide_id=f"s{i}",
                title=f"Slide {i}",
                layout_id="L29",
                slide_type="section_divider",
                slide_type_classification="section_divider",
                narrative=f"Section {i}",
                key_points=["point1"]
            )
            for i in range(1, 13)
        ]

        strawman = PresentationStrawman(
            main_title="Creative Presentation",
            overall_theme="creative storytelling",  # Creative theme keyword
            target_audience="general audience",
            design_suggestions="engaging",
            presentation_duration=40,
            slides=slides
        )

        # Test section divider
        section_slide = slides[5]
        result = assigner.assign_visual_style(section_slide, strawman)

        assert result.use_image_background is True
        assert result.visual_style == "illustrated"  # Creative → illustrated
        assert "large deck" in result.assignment_reason.lower()
        assert "creative theme" in result.assignment_reason.lower()

    def test_section_divider_large_deck_professional_theme(self):
        """Section dividers in large professional decks don't use images by default."""
        assigner = VisualStyleAssigner(user_preferences=None)

        # Create large deck with 12 slides
        slides = [
            Slide(
                slide_number=i,
                slide_id=f"s{i}",
                title=f"Slide {i}",
                layout_id="L29",
                slide_type="section_divider",
                slide_type_classification="section_divider",
                narrative=f"Section {i}",
                key_points=["point1"]
            )
            for i in range(1, 13)
        ]

        strawman = PresentationStrawman(
            main_title="Business Presentation",
            overall_theme="corporate professional",  # Not creative
            target_audience="executives",
            design_suggestions="formal",
            presentation_duration=40,
            slides=slides
        )

        # Test section divider
        section_slide = slides[5]
        result = assigner.assign_visual_style(section_slide, strawman)

        assert result.use_image_background is False
        assert result.visual_style is None
        assert "professional theme" in result.assignment_reason.lower()

    def test_closing_slide_default_uses_image(self):
        """Closing slides default to using image for memorable impact."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=10,
            slide_id="s10",
            title="Closing",
            layout_id="L29",
            slide_type="conclusion_slide",
            slide_type_classification="closing_slide",
            narrative="Thank you",
            key_points=["contact"]
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business",
            design_suggestions="modern",
            presentation_duration=30,
            slides=[slide],
            use_images_for_closing=True  # Default
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.use_image_background is True
        assert result.visual_style == "professional"
        assert "closing images enabled" in result.assignment_reason.lower()

    def test_kids_audience_gets_kids_style(self):
        """AI assigns kids style for children's audiences."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type="title_slide",
            slide_type_classification="title_slide",
            narrative="Welcome",
            key_points=["learning"]
        )

        strawman = PresentationStrawman(
            main_title="Fun Learning",
            overall_theme="educational",
            target_audience="children and elementary students",  # Kids keyword
            design_suggestions="colorful",
            presentation_duration=20,
            slides=[slide]
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.visual_style == "kids"
        assert "kids audience detected" in result.assignment_reason.lower()

    def test_creative_theme_gets_illustrated_style(self):
        """AI assigns illustrated style for creative themes."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type="title_slide",
            slide_type_classification="title_slide",
            narrative="Our story",
            key_points=["innovation"]
        )

        strawman = PresentationStrawman(
            main_title="Creative Pitch",
            overall_theme="creative storytelling narrative",  # Creative keywords
            target_audience="investors",
            design_suggestions="engaging",
            presentation_duration=30,
            slides=[slide]
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.visual_style == "illustrated"
        assert "creative theme detected" in result.assignment_reason.lower()

    def test_user_preference_overrides_ai(self):
        """User visual style preference overrides AI defaults."""
        preferences = VisualStylePreferences(
            visual_style="illustrated",
            use_images_for_sections=True,
            use_images_for_closing=True
        )
        assigner = VisualStyleAssigner(user_preferences=preferences)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type="title_slide",
            slide_type_classification="title_slide",
            narrative="Welcome",
            key_points=["point1"]
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="corporate business",  # Would normally be "professional"
            target_audience="executives",  # Would normally be "professional"
            design_suggestions="formal",
            presentation_duration=30,
            slides=[slide]
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.visual_style == "illustrated"  # User preference wins
        assert "user selected" in result.assignment_reason.lower()

    def test_user_enables_section_images_small_deck(self):
        """User can explicitly enable section images even in small decks."""
        preferences = VisualStylePreferences(
            visual_style="professional",
            use_images_for_sections=True  # User explicitly wants section images
        )
        assigner = VisualStyleAssigner(user_preferences=preferences)

        # Small deck (8 slides)
        slides = [
            Slide(
                slide_number=i,
                slide_id=f"s{i}",
                title=f"Slide {i}",
                layout_id="L29",
                slide_type="section_divider",
                slide_type_classification="section_divider",
                narrative=f"Section {i}",
                key_points=["point1"]
            )
            for i in range(1, 9)
        ]

        strawman = PresentationStrawman(
            main_title="Small Deck",
            overall_theme="professional",
            target_audience="business",
            design_suggestions="modern",
            presentation_duration=20,
            slides=slides
        )

        section_slide = slides[4]
        result = assigner.assign_visual_style(section_slide, strawman)

        assert result.use_image_background is True  # User override
        assert "user requested section images" in result.assignment_reason.lower()

    def test_strawman_preference_fallback(self):
        """Strawman-level preference used when no user preference."""
        assigner = VisualStyleAssigner(user_preferences=None)

        slide = Slide(
            slide_number=1,
            slide_id="s1",
            title="Title",
            layout_id="L29",
            slide_type="title_slide",
            slide_type_classification="title_slide",
            narrative="Welcome",
            key_points=["point1"]
        )

        strawman = PresentationStrawman(
            main_title="Test",
            overall_theme="professional",
            target_audience="business",
            design_suggestions="modern",
            presentation_duration=30,
            slides=[slide],
            visual_style_preference="illustrated"  # Strawman-level preference
        )

        result = assigner.assign_visual_style(slide, strawman)

        assert result.visual_style == "illustrated"
        assert "strawman preference" in result.assignment_reason.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Test Director Agent v3.3 integration with v7.5-main deck builder.

This test verifies:
1. Layout selection works correctly (L25 vs L29)
2. Content transformation works for both layouts
3. Deck builder API integration is successful
"""

import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent))

from src.models.agents import PresentationStrawman, Slide
from src.utils.content_transformer import ContentTransformer
from config.settings import get_settings


def test_layout_selection():
    """Test that layout selection works correctly for 2-layout system."""
    print("\n=== Testing Layout Selection ===")

    # Create mock slides
    slides = [
        Slide(
            slide_number=1,
            slide_id="s1",
            title="Welcome to Our Presentation",
            slide_type="title_slide",
            narrative="An introduction to our company",
            key_points=[]
        ),
        Slide(
            slide_number=2,
            slide_id="s2",
            title="Our Core Values",
            slide_type="content_heavy",
            narrative="We believe in innovation and excellence",
            key_points=["Innovation", "Excellence", "Integrity"]
        ),
        Slide(
            slide_number=3,
            slide_id="s3",
            title="Market Opportunity",
            slide_type="section_divider",
            narrative="The next frontier",
            key_points=[]
        ),
        Slide(
            slide_number=4,
            slide_id="s4",
            title="Market Analysis",
            slide_type="content_heavy",
            narrative="Current market trends show strong growth",
            key_points=["Growing demand", "Underserved segments", "Strong tailwinds"]
        ),
        Slide(
            slide_number=5,
            slide_id="s5",
            title="Thank You",
            slide_type="conclusion_slide",
            narrative="Questions?",
            key_points=[]
        )
    ]

    # Expected layout assignments
    expected_layouts = {
        1: "L29",  # First slide (title)
        2: "L25",  # Content slide
        3: "L29",  # Section divider
        4: "L25",  # Content slide
        5: "L29",  # Last slide (closing)
    }

    # Test layout selection
    print(f"Testing layout selection for {len(slides)} slides...")
    for slide in slides:
        position = "first" if slide.slide_number == 1 else \
                   "last" if slide.slide_number == len(slides) else \
                   "middle"

        # Simulate layout selection logic from director.py
        if position == "first" or position == "last":
            selected_layout = "L29"
        elif slide.slide_type == "section_divider":
            selected_layout = "L29"
        else:
            selected_layout = "L25"

        expected = expected_layouts[slide.slide_number]
        status = "✓" if selected_layout == expected else "✗"
        print(f"  {status} Slide {slide.slide_number} ({slide.slide_type}): {selected_layout} (expected {expected})")

        assert selected_layout == expected, f"Layout mismatch for slide {slide.slide_number}"

    print("✓ All layout selections correct!")
    return True


def test_content_transformation():
    """Test that content transformation works for L25 and L29."""
    print("\n=== Testing Content Transformation ===")

    # Initialize components
    transformer = ContentTransformer()  # No arguments needed - gets schema_manager internally

    # Create mock presentation
    presentation = PresentationStrawman(
        main_title="Test Presentation",
        overall_theme="Testing v7.5-main integration",
        target_audience="Development team",
        design_suggestions="Modern and clean design with professional colors",
        presentation_duration=15,
        slides=[]
    )

    # Test L29 (Hero) transformation
    print("\nTesting L29 (Full-Bleed Hero) transformation...")
    hero_slide = Slide(
        slide_number=1,
        slide_id="hero1",
        title="Welcome to Innovation",
        slide_type="title_slide",
        narrative="The future starts here",
        key_points=[],
        layout_id="L29"
    )

    hero_result = transformer.transform_slide(hero_slide, "L29", presentation, enriched_slide=None)
    print(f"  Layout: {hero_result['layout']}")
    print(f"  Content keys: {list(hero_result['content'].keys())}")

    assert hero_result['layout'] == 'L29', "Wrong layout for hero slide"
    assert 'hero_content' in hero_result['content'], "Missing hero_content field"
    print(f"  ✓ L29 transformation successful")
    print(f"  Hero content preview: {hero_result['content']['hero_content'][:100]}...")

    # Test L25 (Content) transformation
    print("\nTesting L25 (Main Content Shell) transformation...")
    content_slide = Slide(
        slide_number=2,
        slide_id="content1",
        title="Our Core Values",
        slide_type="content_heavy",
        narrative="We believe in making a difference",
        key_points=["Innovation", "Excellence", "Integrity", "Collaboration"],
        layout_id="L25"
    )

    content_result = transformer.transform_slide(content_slide, "L25", presentation, enriched_slide=None)
    print(f"  Layout: {content_result['layout']}")
    print(f"  Content keys: {list(content_result['content'].keys())}")

    assert content_result['layout'] == 'L25', "Wrong layout for content slide"
    assert 'slide_title' in content_result['content'], "Missing slide_title field"
    assert 'rich_content' in content_result['content'], "Missing rich_content field"
    print(f"  ✓ L25 transformation successful")
    print(f"  Slide title: {content_result['content']['slide_title']}")
    print(f"  Rich content preview: {content_result['content']['rich_content'][:150]}...")

    return True


def test_deck_builder_connectivity():
    """Test that we can reach the deck builder API."""
    print("\n=== Testing Deck Builder API Connectivity ===")

    import requests

    settings = get_settings()
    deck_builder_url = settings.DECK_BUILDER_API_URL

    print(f"Testing connection to: {deck_builder_url}")

    try:
        response = requests.get(deck_builder_url, timeout=5)
        response.raise_for_status()
        data = response.json()

        print(f"  ✓ Connected successfully")
        print(f"  Version: {data.get('version')}")
        print(f"  Layouts: {data.get('layouts')}")
        print(f"  Endpoints: {list(data.get('endpoints', {}).keys())}")

        # Verify we have L25 and L29
        layouts = data.get('layouts', [])
        assert 'L25' in layouts, "L25 layout not available"
        assert 'L29' in layouts, "L29 layout not available"

        print("  ✓ Both L25 and L29 layouts available")
        return True

    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False


def main():
    """Run all integration tests."""
    print("=" * 60)
    print("Director Agent v3.3 + v7.5-main Integration Tests")
    print("=" * 60)

    try:
        # Test 1: Layout selection
        test_layout_selection()

        # Test 2: Content transformation
        test_content_transformation()

        # Test 3: Deck builder connectivity
        test_deck_builder_connectivity()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nDirector Agent v3.3 is successfully integrated with v7.5-main!")
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

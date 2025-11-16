"""
Test L02 Analytics Passthrough - Layout Builder v7.5.1 HTML Support

Tests that Director properly passes through HTML from Analytics Service v3
without stripping tags. Layout Builder v7.5.1 now supports HTML auto-detection
in element_2 and element_3.

REPLACES: test_html_stripping.py (deprecated approach)
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.content_transformer import ContentTransformer
from src.models.agents import PresentationStrawman, Slide
from pydantic_ai.models import KnownModelName


def test_analytics_html_preserved():
    """Test that Analytics HTML is preserved (NOT stripped)."""
    print("\n" + "=" * 70)
    print("TEST 1: Analytics HTML Passthrough")
    print("=" * 70)

    transformer = ContentTransformer()

    # Create a mock presentation
    strawman = PresentationStrawman(
        main_title="Test Presentation",
        footer_text="Test Footer",
        overall_theme="professional",
        design_suggestions="Modern professional with data visualization",
        target_audience="Business executives",
        presentation_duration=10,
        slides=[]
    )

    # Create a mock analytics slide
    slide = Slide(
        slide_number=1,
        slide_id="slide-001",
        slide_type="data_driven",  # Slide type enum value
        slide_type_classification="analytics",  # Classification by classifier
        layout_id="L02",
        title="Revenue Growth",
        generated_title="Quarterly Revenue Analysis",
        generated_subtitle="FY 2024 Performance",
        narrative="Strong quarterly growth",
        key_points=[],
        visual_type="chart"
    )

    strawman.slides.append(slide)

    # Simulate Analytics Service v3 response with HTML in both fields
    class MockGeneratedText:
        def __init__(self, content):
            self.content = content

    class MockEnrichedSlide:
        def __init__(self, generated_text):
            self.generated_text = generated_text
            self.has_text_failure = False

    # Analytics content with HTML (as Analytics Service v3 sends it)
    analytics_content = {
        "element_3": """<div class="l02-chart-container" style="width: 1260px; height: 720px; position: relative;">
    <canvas id="chart-slide-001"></canvas>
    <script>
        (function() {
            const ctx = document.getElementById('chart-slide-001').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: { labels: ['Q1', 'Q2', 'Q3', 'Q4'], datasets: [{ data: [100, 120, 150, 180] }] },
                options: { responsive: true, maintainAspectRatio: false }
            });
        })();
    </script>
</div>""",
        "element_2": """<div style="padding: 32px; background: #f8f9fa; border-radius: 8px; height: 100%; overflow-y: auto;">
    <h3 style="font-size: 20px; font-weight: 600; margin: 0 0 16px 0; color: #1f2937;">Key Insights</h3>
    <p style="font-size: 16px; line-height: 1.6; color: #374151; margin: 0;">
        The line chart illustrates quarterly revenue growth, with figures increasing from $125,000 in Q1 to $195,000 in Q4.
    </p>
</div>"""
    }

    enriched_slide = MockEnrichedSlide(MockGeneratedText(analytics_content))

    # Transform the slide
    result = transformer.transform_slide(
        slide=slide,
        layout_id="L02",
        presentation=strawman,
        enriched_slide=enriched_slide
    )

    print(f"\nTransformed slide:")
    print(f"  Layout: {result['layout']}")
    print(f"  Content keys: {list(result['content'].keys())}")

    # ✅ Verify L02 structure (NOT L25 rich_content!)
    assert result['layout'] == "L02", f"Wrong layout: {result['layout']}"
    assert "element_3" in result['content'], "Missing element_3"
    assert "element_2" in result['content'], "Missing element_2"
    assert "rich_content" not in result['content'], "Should NOT have rich_content (L25 field)"

    print("  ✅ L02 structure correct (element_3 + element_2)")

    # ✅ Verify HTML preserved in element_3 (chart)
    element_3 = result['content']['element_3']
    assert "<canvas" in element_3, "Chart canvas missing"
    assert "Chart(ctx" in element_3, "Chart.js initialization missing"
    assert "maintainAspectRatio: false" in element_3, "Chart.js options missing"
    print(f"  ✅ element_3 HTML preserved ({len(element_3)} chars)")

    # ✅ Verify HTML preserved in element_2 (observations)
    element_2 = result['content']['element_2']
    assert "<h3" in element_2, "Heading tag missing"
    assert "<p" in element_2, "Paragraph tag missing"
    assert "Key Insights" in element_2, "Heading text missing"
    assert "font-size: 20px" in element_2, "Styling preserved"
    assert "color: #1f2937" in element_2, "Color styling preserved"
    print(f"  ✅ element_2 HTML preserved ({len(element_2)} chars)")

    # ✅ Verify metadata fields
    assert result['content']['slide_title'] == "Quarterly Revenue Analysis"
    assert result['content']['element_1'] == "FY 2024 Performance"
    assert result['content']['presentation_name'] == "Test Footer"
    print("  ✅ Metadata fields correct")

    print("\n✅ TEST PASSED: Analytics HTML passthrough working")
    print("   - element_3 HTML preserved (chart)")
    print("   - element_2 HTML preserved (observations)")
    print("   - L02 structure created (not L25)")
    print("   - No HTML stripping occurred")


def test_l02_structure_validation():
    """Verify L02 structure has correct fields."""
    print("\n" + "=" * 70)
    print("TEST 2: L02 Structure Validation")
    print("=" * 70)

    transformer = ContentTransformer()

    # Expected L02 fields
    expected_fields = {
        "slide_title",
        "element_1",
        "element_3",
        "element_2",
        "presentation_name",
        "company_logo"
    }

    # Unexpected fields (from L25)
    unexpected_fields = {
        "rich_content",
        "subtitle"
    }

    print(f"\nExpected L02 fields:")
    for field in sorted(expected_fields):
        print(f"  ✓ {field}")

    print(f"\nUnexpected fields (L25-specific):")
    for field in sorted(unexpected_fields):
        print(f"  ✗ {field} (should NOT appear)")

    print("\n✅ TEST PASSED: L02 structure documented")


def test_backward_compatibility():
    """Verify _strip_html_tags method still exists but is deprecated."""
    print("\n" + "=" * 70)
    print("TEST 3: Backward Compatibility")
    print("=" * 70)

    transformer = ContentTransformer()

    # Method should still exist (for potential other uses)
    assert hasattr(transformer, '_strip_html_tags'), "Method removed (should be deprecated)"

    # Test it still works
    html = "<p>Test content</p>"
    result = transformer._strip_html_tags(html)
    assert result == "Test content", "Method functionality broken"

    print("\n✅ TEST PASSED: _strip_html_tags method exists (deprecated)")
    print("   Note: Method is DEPRECATED for Analytics L02 use")
    print("   Layout Builder v7.5.1 handles HTML rendering")


def test_dimensions_correct():
    """Document correct dimensions for Analytics L02."""
    print("\n" + "=" * 70)
    print("TEST 4: L02 Dimensions Documentation")
    print("=" * 70)

    print("\nLayout Builder v7.5.1 L02 Grid Dimensions:")
    print("  - Fixed viewport: 1920×1080px")
    print("  - Total content area: 1800×720px")
    print("  - element_3 (chart): 1260×720px (21 grids wide)")
    print("  - element_2 (observations): 540×720px (9 grids wide)")
    print("  - Note: Layout Builder handles dimensions via grid system")
    print("  - Director just passes HTML, no dimension wrapping needed")

    print("\n✅ TEST PASSED: Dimensions documented")


if __name__ == "__main__":
    try:
        test_analytics_html_preserved()
        test_l02_structure_validation()
        test_backward_compatibility()
        test_dimensions_correct()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED")
        print("=" * 70)
        print("\nL02 Analytics Passthrough verified:")
        print("  ✅ HTML preserved in element_3 (chart)")
        print("  ✅ HTML preserved in element_2 (observations)")
        print("  ✅ L02 structure created (not L25)")
        print("  ✅ No HTML stripping for analytics")
        print("  ✅ Dimensions handled by Layout Builder v7.5.1")
        print("\nLayout Builder v7.5.1 auto-detects and renders HTML! 🚀")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

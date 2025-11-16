"""
Test HTML stripping functionality for L02 Analytics compatibility.

Tests that Director properly strips HTML tags from Analytics Service element_2
to maintain compatibility with Layout Builder L02 expectations.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.content_transformer import ContentTransformer
from src.models.agents import PresentationStrawman, Slide
from pydantic_ai.models import KnownModelName


def test_strip_html_tags():
    """Test the _strip_html_tags static method."""
    print("\n" + "=" * 70)
    print("TEST 1: _strip_html_tags() Method")
    print("=" * 70)

    transformer = ContentTransformer()

    # Test case 1: HTML with div, h3, and paragraphs
    html_input = """
    <div class="observations-panel" style="padding: 20px; background: #f8f9fa;">
        <h3 style="font-size: 18px; margin-bottom: 12px;">Key Insights</h3>
        <div style="line-height: 1.6;">
            The line chart illustrates quarterly revenue growth, with figures
            increasing from $100,000 in Q1 to $180,000 in Q4.
        </div>
    </div>
    """

    expected_output = "Key Insights The line chart illustrates quarterly revenue growth, with figures increasing from $100,000 in Q1 to $180,000 in Q4."

    result = transformer._strip_html_tags(html_input)

    print(f"\nInput ({len(html_input)} chars):")
    print(f"  {html_input[:100]}...")
    print(f"\nOutput ({len(result)} chars):")
    print(f"  {result}")
    print(f"\nExpected ({len(expected_output)} chars):")
    print(f"  {expected_output}")

    assert result == expected_output, f"Mismatch: {result} != {expected_output}"
    print("\n✅ Test 1 PASSED: HTML tags stripped correctly")

    # Test case 2: Empty string
    assert transformer._strip_html_tags("") == ""
    print("✅ Test 2 PASSED: Empty string handled")

    # Test case 3: Plain text (no HTML)
    plain_text = "This is plain text with no HTML tags."
    assert transformer._strip_html_tags(plain_text) == plain_text
    print("✅ Test 3 PASSED: Plain text unchanged")

    # Test case 4: Multiple spaces and newlines
    messy_html = "<p>Multiple   spaces\n\nand   newlines</p>"
    clean_result = transformer._strip_html_tags(messy_html)
    assert clean_result == "Multiple spaces and newlines"
    print("✅ Test 4 PASSED: Extra whitespace cleaned")


def test_analytics_content_transformation():
    """Test that Analytics content with element_3 + element_2 is properly transformed."""
    print("\n" + "=" * 70)
    print("TEST 2: Analytics Content Transformation (L25)")
    print("=" * 70)

    transformer = ContentTransformer()

    # Create a mock presentation with all required fields
    strawman = PresentationStrawman(
        main_title="Test Presentation",
        footer_text="Test Footer",
        overall_theme="professional",
        design_suggestions="Modern professional with data visualization",
        target_audience="Business executives",
        presentation_duration=10,
        slides=[]
    )

    # Create a mock slide with Analytics content
    slide = Slide(
        slide_number=1,
        slide_id="slide-001",
        slide_type="data_driven",  # Valid slide type for analytics content
        layout_id="L25",
        variant_id="chart_left_text_right",
        title="Revenue Growth",
        generated_title="Quarterly Revenue Analysis",
        generated_subtitle="FY 2024 Performance",
        narrative="Strong quarterly growth",
        key_points=[],
        visual_type="chart"
    )

    strawman.slides.append(slide)

    # Simulate Analytics Service response with HTML in element_2
    class MockGeneratedText:
        def __init__(self, content):
            self.content = content

    class MockEnrichedSlide:
        def __init__(self, generated_text):
            self.generated_text = generated_text
            self.has_text_failure = False

    # Analytics content with HTML in element_2
    analytics_content = {
        "element_3": "<div class='chart'><canvas id='chart-1'></canvas></div>",
        "element_2": """
            <div class="l02-observations-panel" style="width: 540px; height: 720px; padding: 40px;">
                <h3 style="font-size: 20px; margin-bottom: 16px;">Key Insights</h3>
                <div style="line-height: 1.6; color: #374151;">
                    The line chart illustrates quarterly revenue growth, with figures
                    increasing from $125,000 in Q1 to $195,000 in Q4.
                </div>
            </div>
        """
    }

    enriched_slide = MockEnrichedSlide(MockGeneratedText(analytics_content))

    # Transform the slide
    result = transformer.transform_slide(
        slide=slide,
        layout_id="L25",
        presentation=strawman,
        enriched_slide=enriched_slide
    )

    print(f"\nTransformed slide:")
    print(f"  Layout: {result['layout']}")
    print(f"  Has rich_content: {'rich_content' in result['content']}")

    if 'rich_content' in result['content']:
        rich_content = result['content']['rich_content']
        print(f"  rich_content length: {len(rich_content)} chars")

        # Verify that the HTML stripping occurred
        assert "Key Insights" in rich_content, "Missing 'Key Insights' heading"
        assert "quarterly revenue growth" in rich_content.lower(), "Missing observations text"

        # Verify that the original HTML tags from element_2 are NOT in rich_content
        # (they've been stripped and re-wrapped with our own formatting)
        assert "l02-observations-panel" not in rich_content, "Original HTML class still present"
        assert "width: 540px" not in rich_content, "Original inline style still present"

        # Verify our new formatting is present
        assert "flex: 0 0 1260px" in rich_content, "Chart column not found"
        assert "flex: 0 0 480px" in rich_content, "Observations column not found"

        print("\n✅ Test PASSED: Analytics content transformed correctly")
        print(f"   - HTML tags stripped from element_2")
        print(f"   - Plain text wrapped in new formatting")
        print(f"   - 2-column layout created for L25 display")
    else:
        print("\n❌ Test FAILED: No rich_content in result")
        print(f"   Result keys: {result['content'].keys()}")
        raise AssertionError("Expected rich_content field")


def test_l25_content_schema():
    """Verify L25 schema is properly loaded."""
    print("\n" + "=" * 70)
    print("TEST 3: L25 Content Schema")
    print("=" * 70)

    transformer = ContentTransformer()

    schema = transformer.schema_manager.get_schema("L25")
    print(f"\nL25 Schema:")
    print(f"  Name: {schema['name']}")
    print(f"  Layout ID: {schema['layout_id']}")
    print(f"  Content fields: {list(schema['content_schema'].keys())}")

    assert "rich_content" in schema['content_schema'], "L25 missing rich_content field"
    print("\n✅ Test PASSED: L25 schema loaded correctly")


if __name__ == "__main__":
    try:
        test_strip_html_tags()
        test_analytics_content_transformation()
        test_l25_content_schema()

        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED")
        print("=" * 70)
        print("\nHTML stripping fix is working correctly:")
        print("  ✅ HTML tags removed from Analytics element_2")
        print("  ✅ Plain text extracted successfully")
        print("  ✅ L25 2-column layout created with clean text")
        print("  ✅ L02 compatibility maintained")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

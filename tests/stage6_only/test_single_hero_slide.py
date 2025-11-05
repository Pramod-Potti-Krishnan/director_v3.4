"""
Test Single Hero Slide Generation

Tests hero slide generation using Director v3.4's actual logic.
This isolates hero slide functionality to debug issues.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import asyncio
import json
from datetime import datetime

from src.models.agents import Slide, PresentationStrawman, ContentGuidance
from src.utils.service_router_v1_2 import ServiceRouterV1_2
from src.utils.text_service_client_v1_2 import TextServiceClientV1_2

# Text Service URL
TEXT_SERVICE_URL = "https://web-production-5daf.up.railway.app"


async def test_single_title_slide():
    """Test title slide generation through Director's logic."""
    print("\n" + "="*80)
    print("Testing Single Title Slide Generation")
    print("="*80)

    # Create a minimal strawman with just a title slide
    strawman = PresentationStrawman(
        main_title="AI in Healthcare: Transforming Diagnostics",
        overall_theme="Professional and data-driven",
        slides=[],
        design_suggestions="Modern professional design",
        target_audience="Healthcare executives",
        presentation_duration=10,
        footer_text="AI Healthcare 2025"
    )

    # Create title slide
    title_slide = Slide(
        slide_number=1,
        slide_id="slide_001",
        title="AI in Healthcare",
        slide_type="title_slide",
        slide_type_classification="title_slide",
        layout_id="L29",
        variant_id="hero_centered",
        generated_title="AI in Healthcare: Transforming Patient Outcomes",
        generated_subtitle="Revolutionizing diagnostic accuracy through advanced machine learning",
        narrative="Introduction to AI applications in healthcare diagnostics",
        key_points=[
            "AI-powered diagnostics improving accuracy by 40%",
            "Real-time patient monitoring",
            "Case studies from leading institutions"
        ]
    )

    strawman.slides = [title_slide]

    print(f"\n📄 Test Slide:")
    print(f"   Type: {title_slide.slide_type_classification}")
    print(f"   Title: {title_slide.generated_title}")
    print(f"   Subtitle: {title_slide.generated_subtitle}")
    print(f"   Layout: {title_slide.layout_id}")
    print(f"   Variant: {title_slide.variant_id}")

    # Initialize Director's service router
    print(f"\n🚀 Initializing Director's Service Router...")
    client = TextServiceClientV1_2(TEXT_SERVICE_URL)
    router = ServiceRouterV1_2(client)

    # Route the presentation (uses Director's actual logic)
    print(f"\n⏳ Routing through Director's logic...")
    start = datetime.utcnow()

    try:
        result = await router.route_presentation(
            strawman=strawman,
            session_id="test_hero_single"
        )

        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Routing completed in {duration:.2f}s")
        print(f"\n📊 Results:")
        print(f"   Successful: {result['metadata']['successful_count']}")
        print(f"   Failed: {result['metadata']['failed_count']}")
        print(f"   Skipped: {result['metadata']['skipped_count']}")

        if result['generated_slides']:
            slide_result = result['generated_slides'][0]
            print(f"\n✅ Generated Slide:")
            print(f"   Slide #: {slide_result['slide_number']}")
            print(f"   Type: {slide_result.get('slide_type', 'N/A')}")
            print(f"   Endpoint: {slide_result.get('endpoint_used', 'N/A')}")

            content = slide_result.get('content', {})
            if isinstance(content, dict):
                html = content.get('html', '')
            else:
                html = content

            print(f"   HTML Length: {len(html)} chars")
            print(f"\n   HTML Preview:")
            print(f"   {html[:300]}...")

            return True
        else:
            print(f"\n❌ No slides generated!")
            if result['failed_slides']:
                print(f"\n Failed slides:")
                for failed in result['failed_slides']:
                    print(f"   - Slide {failed['slide_number']}: {failed.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_single_closing_slide():
    """Test closing slide generation through Director's logic."""
    print("\n" + "="*80)
    print("Testing Single Closing Slide Generation")
    print("="*80)

    # Create a minimal strawman with just a closing slide
    strawman = PresentationStrawman(
        main_title="AI in Healthcare: Transforming Diagnostics",
        overall_theme="Professional and data-driven",
        slides=[],
        design_suggestions="Modern professional design",
        target_audience="Healthcare executives",
        presentation_duration=10,
        footer_text="AI Healthcare 2025"
    )

    # Create closing slide
    closing_slide = Slide(
        slide_number=1,
        slide_id="slide_003",
        title="Next Steps",
        slide_type="conclusion_slide",
        slide_type_classification="closing_slide",
        layout_id="L29",
        variant_id="hero_centered",
        generated_title="Implementing AI in Your Practice",
        generated_subtitle="Practical steps to adopt AI-powered diagnostics",
        narrative="Call to action for implementing AI diagnostic tools",
        key_points=[
            "Start with pilot programs",
            "Validate AI recommendations",
            "Scale successful implementations",
            "Continuous improvement"
        ]
    )

    strawman.slides = [closing_slide]

    print(f"\n📄 Test Slide:")
    print(f"   Type: {closing_slide.slide_type_classification}")
    print(f"   Title: {closing_slide.generated_title}")
    print(f"   Subtitle: {closing_slide.generated_subtitle}")

    # Initialize Director's service router
    print(f"\n🚀 Initializing Director's Service Router...")
    client = TextServiceClientV1_2(TEXT_SERVICE_URL)
    router = ServiceRouterV1_2(client)

    # Route the presentation
    print(f"\n⏳ Routing through Director's logic...")
    start = datetime.utcnow()

    try:
        result = await router.route_presentation(
            strawman=strawman,
            session_id="test_closing_single"
        )

        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Routing completed in {duration:.2f}s")
        print(f"\n📊 Results:")
        print(f"   Successful: {result['metadata']['successful_count']}")
        print(f"   Failed: {result['metadata']['failed_count']}")
        print(f"   Skipped: {result['metadata']['skipped_count']}")

        if result['generated_slides']:
            slide_result = result['generated_slides'][0]
            print(f"\n✅ Generated Slide:")
            print(f"   Slide #: {slide_result['slide_number']}")
            print(f"   Type: {slide_result.get('slide_type', 'N/A')}")
            print(f"   Endpoint: {slide_result.get('endpoint_used', 'N/A')}")

            content = slide_result.get('content', {})
            if isinstance(content, dict):
                html = content.get('html', '')
            else:
                html = content

            print(f"   HTML Length: {len(html)} chars")
            print(f"\n   HTML Preview:")
            print(f"   {html[:300]}...")

            return True
        else:
            print(f"\n❌ No slides generated!")
            if result['failed_slides']:
                print(f"\nFailed slides:")
                for failed in result['failed_slides']:
                    print(f"   - Slide {failed['slide_number']}: {failed.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run both single slide tests."""
    print("\n" + "="*80)
    print("SINGLE HERO SLIDE TESTS")
    print("Using Director v3.4 Logic")
    print("="*80)
    print(f"Text Service: {TEXT_SERVICE_URL}")
    print("="*80)

    results = {
        "title_slide": await test_single_title_slide(),
        "closing_slide": await test_single_closing_slide()
    }

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.ljust(20)}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL HERO SLIDE TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

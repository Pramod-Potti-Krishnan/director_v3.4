"""
Test Single Content Slide Generation

Tests content slide generation using Director v3.4's actual logic.
This isolates content slide functionality to debug issues.
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


async def test_single_matrix_slide():
    """Test matrix_2x2 content slide generation through Director's logic."""
    print("\n" + "="*80)
    print("Testing Single Matrix Content Slide Generation")
    print("="*80)

    # Create a minimal strawman with just a matrix slide
    strawman = PresentationStrawman(
        main_title="AI in Healthcare: Transforming Diagnostics",
        overall_theme="Professional and data-driven",
        slides=[],
        design_suggestions="Modern professional design",
        target_audience="Healthcare executives",
        presentation_duration=10,
        footer_text="AI Healthcare 2025"
    )

    # Create matrix slide
    matrix_slide = Slide(
        slide_number=1,
        slide_id="slide_002",
        title="AI Diagnostic Applications",
        slide_type="content_heavy",
        slide_type_classification="matrix_2x2",
        layout_id="L25",
        variant_id="matrix_2x2",
        generated_title="Four Pillars of AI Diagnostic Excellence",
        generated_subtitle="Critical applications transforming patient care",
        narrative="Four key areas where AI is revolutionizing healthcare diagnostics",
        key_points=[
            "Medical Imaging Analysis - 95% accuracy in tumor detection",
            "Predictive Analytics - Early disease detection",
            "Treatment Optimization - Personalized medicine",
            "Clinical Decision Support - Real-time recommendations"
        ],
        content_guidance=ContentGuidance(
            content_type="framework",
            visual_complexity="moderate",
            content_density="balanced",
            tone_indicator="professional",
            generation_instructions="Create balanced 2x2 matrix showing equal importance",
            pattern_rationale="Matrix pattern shows interconnected pillars"
        )
    )

    strawman.slides = [matrix_slide]

    print(f"\n📄 Test Slide:")
    print(f"   Type: {matrix_slide.slide_type_classification}")
    print(f"   Title: {matrix_slide.generated_title}")
    print(f"   Subtitle: {matrix_slide.generated_subtitle}")
    print(f"   Layout: {matrix_slide.layout_id}")
    print(f"   Variant: {matrix_slide.variant_id}")
    print(f"   Key Points: {len(matrix_slide.key_points)}")

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
            session_id="test_matrix_single"
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
            print(f"   Variant: {slide_result.get('variant_id', 'N/A')}")

            content_data = slide_result.get('content', '')
            if isinstance(content_data, str):
                html = content_data
            elif isinstance(content_data, dict):
                html = content_data.get('html', content_data)
            else:
                html = str(content_data)

            print(f"   HTML Length: {len(html)} chars")
            print(f"\n   HTML Preview:")
            print(f"   {html[:400]}...")

            # Check metadata
            metadata = slide_result.get('metadata', {})
            print(f"\n   Metadata:")
            print(f"   - Generation time: {slide_result.get('generation_time_seconds', 'N/A')}s")
            if 'validation' in metadata:
                print(f"   - Validation: {metadata['validation'].get('valid', 'N/A')}")

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


async def test_single_grid_slide():
    """Test grid content slide generation through Director's logic."""
    print("\n" + "="*80)
    print("Testing Single Grid Content Slide Generation")
    print("="*80)

    # Create a minimal strawman with just a grid slide
    strawman = PresentationStrawman(
        main_title="AI in Healthcare: Transforming Diagnostics",
        overall_theme="Professional and data-driven",
        slides=[],
        design_suggestions="Modern professional design",
        target_audience="Healthcare executives",
        presentation_duration=10,
        footer_text="AI Healthcare 2025"
    )

    # Create grid slide
    grid_slide = Slide(
        slide_number=1,
        slide_id="slide_grid",
        title="Implementation Benefits",
        slide_type="content_heavy",
        slide_type_classification="grid_2x3",
        layout_id="L25",
        variant_id="grid_2x3",
        generated_title="Three Key Benefits of AI Implementation",
        generated_subtitle="Measurable improvements in clinical outcomes",
        narrative="Three major benefits healthcare institutions experience",
        key_points=[
            "40% improvement in diagnostic accuracy",
            "50% reduction in time to diagnosis",
            "30% decrease in false positives",
            "25% cost reduction",
            "60% faster turnaround",
            "95% patient satisfaction"
        ],
        content_guidance=ContentGuidance(
            content_type="benefits",
            visual_complexity="simple",
            content_density="balanced",
            tone_indicator="professional",
            generation_instructions="Highlight quantifiable benefits clearly",
            pattern_rationale="Grid shows parallel benefits"
        )
    )

    strawman.slides = [grid_slide]

    print(f"\n📄 Test Slide:")
    print(f"   Type: {grid_slide.slide_type_classification}")
    print(f"   Title: {grid_slide.generated_title}")
    print(f"   Variant: {grid_slide.variant_id}")
    print(f"   Key Points: {len(grid_slide.key_points)}")

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
            session_id="test_grid_single"
        )

        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Routing completed in {duration:.2f}s")
        print(f"\n📊 Results:")
        print(f"   Successful: {result['metadata']['successful_count']}")
        print(f"   Failed: {result['metadata']['failed_count']}")

        if result['generated_slides']:
            slide_result = result['generated_slides'][0]
            print(f"\n✅ Generated Slide:")
            print(f"   Slide #: {slide_result['slide_number']}")
            print(f"   Variant: {slide_result.get('variant_id', 'N/A')}")

            content_data = slide_result.get('content', '')
            if isinstance(content_data, str):
                html = content_data
            elif isinstance(content_data, dict):
                html = content_data.get('html', content_data)
            else:
                html = str(content_data)

            print(f"   HTML Length: {len(html)} chars")
            print(f"\n   HTML Preview:")
            print(f"   {html[:400]}...")

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
    """Run both single content slide tests."""
    print("\n" + "="*80)
    print("SINGLE CONTENT SLIDE TESTS")
    print("Using Director v3.4 Logic")
    print("="*80)
    print(f"Text Service: {TEXT_SERVICE_URL}")
    print("="*80)

    results = {
        "matrix_2x2": await test_single_matrix_slide(),
        "grid_2x3": await test_single_grid_slide()
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
        print("\n🎉 ALL CONTENT SLIDE TESTS PASSED!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

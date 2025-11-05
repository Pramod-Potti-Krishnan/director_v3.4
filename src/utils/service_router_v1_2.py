"""
Service Router v1.2 for Director v3.4
======================================

Routes slides to Text Service v1.2 endpoints:
- Hero slides (L29) → /v1.2/hero/title, /section, /closing endpoints
- Content slides (L25) → /v1.2/generate endpoint

Key features:
- Hero slide support (v3.4): Routes title/section/closing slides to specialized hero endpoints
- Content slide support: Uses unified /v1.2/generate endpoint for 10 content variants
- Simplified routing logic with automatic error handling
- Prior slides context for narrative flow
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
from src.models.agents import Slide, PresentationStrawman
from src.utils.logger import setup_logger
from src.utils.text_service_client_v1_2 import TextServiceClientV1_2
from src.utils.v1_2_transformer import V1_2_Transformer
from src.utils.hero_request_transformer import HeroRequestTransformer

logger = setup_logger(__name__)


class ServiceRouterV1_2:
    """
    Routes slides to Text Service v1.2 unified endpoint.

    Features:
    - Sequential processing (calls /v1.2/generate per slide)
    - Automatic error handling and reporting
    - Prior slides context for narrative flow
    - Processing statistics and metadata
    """

    def __init__(self, text_service_client: TextServiceClientV1_2):
        """
        Initialize service router for v1.2.

        Args:
            text_service_client: TextServiceClientV1_2 instance
        """
        self.client = text_service_client
        self.hero_transformer = HeroRequestTransformer()
        logger.info("ServiceRouterV1_2 initialized with hero slide support")

    async def route_presentation(
        self,
        strawman: PresentationStrawman,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Route all slides in presentation to Text Service v1.2.

        Args:
            strawman: PresentationStrawman with variant_id and generated titles
            session_id: Session identifier for tracking

        Returns:
            Routing result dict with:
            - generated_slides: List of successfully generated slide content
            - failed_slides: List of failed slides with error details
            - metadata: Processing statistics

        Raises:
            ValueError: If slides are missing variant_id or generated_title
        """
        start_time = datetime.utcnow()
        slides = strawman.slides

        logger.info(f"Starting v1.2 presentation routing: {len(slides)} slides")

        # Validate all slides have required v1.2 fields
        self._validate_slides(slides)

        # Process slides sequentially
        result = await self._route_sequential(slides, strawman, session_id)

        # Calculate total processing time
        total_time = (datetime.utcnow() - start_time).total_seconds()
        result["metadata"]["total_processing_time_seconds"] = round(total_time, 2)

        logger.info(
            f"✅ v1.2 routing complete: "
            f"{result['metadata']['successful_count']}/{len(slides)} successful "
            f"in {total_time:.2f}s"
        )

        return result

    def _validate_slides(self, slides: List[Slide]):
        """
        Validate slides have required v1.2 fields.

        Args:
            slides: List of slides to validate

        Raises:
            ValueError: If validation fails
        """
        errors = []

        for slide in slides:
            if not slide.variant_id:
                errors.append(
                    f"Slide {slide.slide_id} missing variant_id (required for v1.2)"
                )

            if not slide.generated_title:
                errors.append(
                    f"Slide {slide.slide_id} missing generated_title (required for v1.2)"
                )

        if errors:
            error_msg = "Slide validation failed:\n" + "\n".join(errors)
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.info("✅ All slides validated for v1.2 (variant_id + generated_title present)")

    async def _route_sequential(
        self,
        slides: List[Slide],
        strawman: PresentationStrawman,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Route slides sequentially to v1.2 endpoint.

        Args:
            slides: List of slides
            strawman: Full presentation context
            session_id: Session identifier

        Returns:
            Sequential routing result
        """
        logger.info(f"Using sequential mode for {len(slides)} slides")

        generated_slides = []
        failed_slides = []
        skipped_slides = []
        total_generation_time = 0

        for idx, slide in enumerate(slides):
            slide_number = idx + 1

            try:
                # Check if this is a hero slide
                is_hero = self._is_hero_slide(slide)

                if is_hero:
                    # NEW v3.4: Generate hero slides using hero endpoints
                    logger.info(
                        f"🎬 Generating hero slide {slide_number}/{len(slides)}: "
                        f"{slide.slide_id} (type: {slide.slide_type_classification})"
                    )

                    try:
                        # Transform to hero request
                        hero_request_data = self.hero_transformer.transform_to_hero_request(
                            slide, strawman
                        )

                        # Call hero endpoint
                        start = datetime.utcnow()
                        hero_response = await self.client.call_hero_endpoint(
                            endpoint=hero_request_data["endpoint"],
                            payload=hero_request_data["payload"]
                        )
                        duration = (datetime.utcnow() - start).total_seconds()
                        total_generation_time += duration

                        # Build successful result
                        slide_result = {
                            "slide_number": slide_number,
                            "slide_id": slide.slide_id,
                            "content": {
                                "html": hero_response["content"],
                                "metadata": hero_response["metadata"]
                            },
                            "generation_time_ms": int(duration * 1000),
                            "endpoint_used": hero_request_data["endpoint"],
                            "slide_type": "hero"
                        }

                        successful_slides.append(slide_result)
                        logger.info(
                            f"✅ Hero slide {slide_number} generated successfully "
                            f"({duration:.2f}s)"
                        )

                    except Exception as hero_error:
                        logger.error(f"Hero slide generation failed: {hero_error}")
                        failed_slides.append({
                            "slide_number": slide_number,
                            "slide_id": slide.slide_id,
                            "slide_type": slide.slide_type_classification,
                            "error": str(hero_error),
                            "endpoint": hero_request_data.get("endpoint", "unknown")
                        })

                    continue  # Skip content slide processing

                logger.info(
                    f"Generating slide {slide_number}/{len(slides)}: "
                    f"{slide.slide_id} (variant: {slide.variant_id})"
                )

                # Build v1.2 request
                request = self._build_slide_request(
                    slide=slide,
                    strawman=strawman,
                    slide_number=slide_number,
                    slides=slides,
                    current_index=idx
                )

                # Call v1.2 generate endpoint
                start = datetime.utcnow()
                generated = await self.client.generate(request)
                duration = (datetime.utcnow() - start).total_seconds()

                total_generation_time += duration

                # Build result entry
                slide_result = {
                    "slide_number": slide_number,
                    "slide_id": slide.slide_id,
                    "variant_id": slide.variant_id,
                    "content": generated.content,  # HTML string
                    "metadata": generated.metadata,
                    "generation_time_seconds": round(duration, 2)
                }

                generated_slides.append(slide_result)
                logger.info(f"✅ Slide {slide_number} generated successfully ({duration:.2f}s)")

            except Exception as e:
                logger.error(f"❌ Slide {slide_number} generation failed: {e}")
                failed_slides.append({
                    "slide_number": slide_number,
                    "slide_id": slide.slide_id,
                    "variant_id": slide.variant_id,
                    "error": str(e)
                })

        metadata = {
            "processing_mode": "sequential",
            "successful_count": len(generated_slides),
            "failed_count": len(failed_slides),
            "skipped_count": len(skipped_slides),
            "sequential_time_seconds": round(total_generation_time, 2),
            "avg_time_per_slide_seconds": (
                round(total_generation_time / len(generated_slides), 2)
                if generated_slides else 0
            )
        }

        return {
            "generated_slides": generated_slides,
            "failed_slides": failed_slides,
            "skipped_slides": skipped_slides,
            "metadata": metadata
        }

    def _is_hero_slide(self, slide: Slide) -> bool:
        """
        Check if slide is a hero slide (title, section divider, or closing).

        Hero slides only need generated_title and generated_subtitle,
        not rich HTML content generation.

        Args:
            slide: Slide to check

        Returns:
            True if hero slide, False otherwise
        """
        hero_types = {'title_slide', 'section_divider', 'closing_slide'}
        return slide.slide_type_classification in hero_types

    def _build_slide_request(
        self,
        slide: Slide,
        strawman: PresentationStrawman,
        slide_number: int,
        slides: List[Slide],
        current_index: int
    ) -> Dict[str, Any]:
        """
        Build v1.2 generation request for a slide.

        Args:
            slide: Slide to build request for
            strawman: Full presentation for context
            slide_number: Slide position (1-indexed)
            slides: All slides (for prior context)
            current_index: Current slide index (0-indexed)

        Returns:
            V1_2_GenerationRequest dict
        """
        # Build prior slides summary for narrative flow
        prior_summary = V1_2_Transformer.build_prior_slides_summary(
            slides=slides,
            current_index=current_index
        )

        # Transform using V1_2_Transformer
        request = V1_2_Transformer.transform_slide_to_v1_2_request(
            slide=slide,
            strawman=strawman,
            slide_number=slide_number,
            prior_slides_summary=prior_summary
        )

        return request


# Convenience function
async def route_presentation_to_v1_2(
    strawman: PresentationStrawman,
    text_service_url: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Route presentation slides to Text Service v1.2 (convenience function).

    Args:
        strawman: PresentationStrawman with variant_id and generated titles
        text_service_url: Text Service v1.2 base URL
        session_id: Session identifier

    Returns:
        Routing result dict
    """
    # Create v1.2 client
    client = TextServiceClientV1_2(text_service_url)

    # Create router
    router = ServiceRouterV1_2(client)

    # Route presentation
    result = await router.route_presentation(strawman, session_id)

    return result


# Example usage
if __name__ == "__main__":
    from src.models.agents import Slide, PresentationStrawman, ContentGuidance

    async def test_router():
        print("Service Router v1.2 Test")
        print("=" * 70)

        # Create sample presentation
        strawman = PresentationStrawman(
            main_title="Q4 Business Review",
            overall_theme="Informative and data-driven",
            slides=[],
            design_suggestions="Modern professional",
            target_audience="Executive team",
            presentation_duration=30,
            footer_text="Q4 2024"
        )

        # Create sample slides
        slides = [
            Slide(
                slide_number=1,
                slide_id="slide_001",
                title="Opening Slide",
                slide_type="title_slide",
                slide_type_classification="title_slide",
                layout_id="L29",
                variant_id="hero_opening_centered",  # v1.2 hero variant
                generated_title="Q4 Business Review",
                generated_subtitle="Strategic Overview",
                narrative="Welcome to our quarterly review",
                key_points=["Review", "Results", "Next Steps"]
            ),
            Slide(
                slide_number=2,
                slide_id="slide_002",
                title="Strategic Pillars",
                slide_type="content_heavy",
                slide_type_classification="matrix_2x2",
                layout_id="L25",
                variant_id="matrix_2x3",  # Random v1.2 variant
                generated_title="Our Strategic Pillars",
                generated_subtitle="Building blocks for success",
                narrative="Four key pillars drive our strategy",
                key_points=["Customer", "Innovation", "Excellence", "Growth"],
                content_guidance=ContentGuidance(
                    content_type="framework",
                    visual_complexity="moderate",
                    content_density="balanced",
                    tone_indicator="professional",
                    generation_instructions="Emphasize strategic importance",
                    pattern_rationale="Matrix shows equal weight"
                )
            )
        ]

        strawman.slides = slides

        # Create client and router
        print("\nInitializing v1.2 client and router...")
        client = TextServiceClientV1_2()
        router = ServiceRouterV1_2(client)

        # Test health check
        print("\nHealth check:")
        healthy = await client.health_check()
        print(f"  Service healthy: {healthy}")

        if healthy:
            # Test routing (this will make real API calls if service is up)
            print("\nRouting presentation (this will call v1.2 API):")
            try:
                result = await router.route_presentation(strawman, "test_session_123")

                print(f"\n✅ Routing complete:")
                print(f"  Successful: {result['metadata']['successful_count']}")
                print(f"  Failed: {result['metadata']['failed_count']}")
                print(f"  Total time: {result['metadata']['total_processing_time_seconds']}s")

                for slide_result in result['generated_slides']:
                    print(f"\n  Slide {slide_result['slide_number']} ({slide_result['variant_id']}):")
                    print(f"    Content length: {len(slide_result['content'])} chars")
                    print(f"    Generation time: {slide_result['generation_time_seconds']}s")

            except Exception as e:
                print(f"  ❌ Routing failed: {e}")
        else:
            print("  ⚠️  Service not healthy, skipping routing test")

        print("\n" + "=" * 70)
        print("Test complete!")

    asyncio.run(test_router())

#!/usr/bin/env python3
"""
Direct test of matrix_2x2 slide generation using Text Service v1.2

This test isolates the content slide generation to diagnose why it's failing.
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.models.agents import Slide, PresentationStrawman, ContentGuidance
from src.utils.text_service_client_v1_2 import TextServiceClientV1_2
from src.utils.v1_2_transformer import V1_2_Transformer

# Colors for terminal output
class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


async def main():
    print(f"\n{Colors.BOLD}Direct Matrix_2x2 Generation Test{Colors.ENDC}\n")
    print("=" * 70)

    # Load test strawman
    strawman_path = Path(__file__).parent / "test_strawman.json"
    with open(strawman_path, 'r') as f:
        data = json.load(f)

    # Parse strawman
    strawman = PresentationStrawman(**data)

    # Get the matrix_2x2 slide (slide 2)
    matrix_slide = strawman.slides[1]  # 0-indexed

    print(f"{Colors.CYAN}Matrix Slide Details:{Colors.ENDC}")
    print(f"  Slide ID: {matrix_slide.slide_id}")
    print(f"  Classification: {matrix_slide.slide_type_classification}")
    print(f"  Variant ID: {matrix_slide.variant_id}")
    print(f"  Generated Title: {matrix_slide.generated_title}")
    print(f"  Generated Subtitle: {matrix_slide.generated_subtitle}")
    print(f"  Layout ID: {matrix_slide.layout_id}")
    print(f"  Key Points: {len(matrix_slide.key_points)}")
    print(f"  Narrative: {matrix_slide.narrative[:80]}...")

    # Initialize Text Service client
    print(f"\n{Colors.CYAN}Initializing Text Service v1.2 Client...{Colors.ENDC}")
    client = TextServiceClientV1_2()

    # Health check
    print(f"{Colors.CYAN}Running health check...{Colors.ENDC}")
    healthy = await client.health_check()
    print(f"  Service healthy: {Colors.GREEN if healthy else Colors.RED}{healthy}{Colors.ENDC}")

    if not healthy:
        print(f"\n{Colors.RED}❌ Text Service is not healthy. Cannot proceed.{Colors.ENDC}")
        return

    # Build v1.2 request
    print(f"\n{Colors.CYAN}Building v1.2 request...{Colors.ENDC}")
    request = V1_2_Transformer.transform_slide_to_v1_2_request(
        slide=matrix_slide,
        strawman=strawman,
        slide_number=2,
        prior_slides_summary="- AI in Healthcare: Transforming Patient Outcomes"
    )

    print(f"{Colors.CYAN}Request Details:{Colors.ENDC}")
    print(f"  Variant ID: {request['variant_id']}")
    print(f"  Slide Title: {request['slide_spec']['slide_title']}")
    print(f"  Slide Purpose: {request['slide_spec']['slide_purpose'][:60]}...")
    print(f"  Key Message: {request['slide_spec']['key_message'][:60]}...")
    print(f"  Tone: {request['slide_spec']['tone']}")
    print(f"  Audience: {request['slide_spec']['audience']}")
    print(f"  Target Points: {len(request['slide_spec'].get('target_points', []))}")
    print(f"  Enable Parallel: {request['enable_parallel']}")
    print(f"  Validate Counts: {request['validate_character_counts']}")

    print(f"\n{Colors.CYAN}Full Request JSON:{Colors.ENDC}")
    print(json.dumps(request, indent=2))

    # Try to generate
    print(f"\n{Colors.BOLD}{Colors.CYAN}Calling Text Service v1.2 /v1.2/generate endpoint...{Colors.ENDC}")
    print(f"{Colors.YELLOW}⏳ This may take 5-15 seconds...{Colors.ENDC}\n")

    try:
        result = await client.generate(request)

        print(f"{Colors.GREEN}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.GREEN}✅ Generation SUCCESSFUL!{Colors.ENDC}")
        print(f"{Colors.GREEN}{'=' * 70}{Colors.ENDC}\n")

        print(f"{Colors.CYAN}Result Details:{Colors.ENDC}")
        print(f"  Content Length: {len(result.content)} characters")
        print(f"  Variant ID: {result.metadata.get('variant_id')}")
        print(f"  Generation Mode: {result.metadata.get('generation_mode')}")
        print(f"  Element Count: {result.metadata.get('element_count')}")
        print(f"  Template Path: {result.metadata.get('template_path')}")
        print(f"  Character Validation: {result.metadata.get('character_validation_valid')}")
        print(f"  Violations: {result.metadata.get('character_validation_violations')}")

        print(f"\n{Colors.CYAN}Generated HTML Preview:{Colors.ENDC}")
        preview = result.content[:500]
        print(f"  {preview}...")

        print(f"\n{Colors.GREEN}✅ Matrix_2x2 generation is working correctly!{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.RED}{'=' * 70}{Colors.ENDC}")
        print(f"{Colors.RED}❌ Generation FAILED!{Colors.ENDC}")
        print(f"{Colors.RED}{'=' * 70}{Colors.ENDC}\n")

        print(f"{Colors.RED}Error Type: {type(e).__name__}{Colors.ENDC}")
        print(f"{Colors.RED}Error Message: {str(e)}{Colors.ENDC}")

        import traceback
        print(f"\n{Colors.YELLOW}Full Traceback:{Colors.ENDC}")
        traceback.print_exc()

        print(f"\n{Colors.RED}❌ Matrix_2x2 generation is failing{Colors.ENDC}")

    print(f"\n{'=' * 70}")
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Standalone Test for Stage 6 (CONTENT_GENERATION)

Tests Text Service v1.2 integration without running Stages 1-5.
Uses pre-prepared strawman from test_strawman.json.

Usage:
    python tests/stage6_only/test_content_generation.py

Author: Director v3.4 Team
Version: 1.0
Date: 2025-11-04
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

# Import Director and models
from src.agents.director import DirectorAgent
from src.models.agents import StateContext, PresentationStrawman
from config.settings import get_settings

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class Stage6Tester:
    """Standalone tester for Stage 6 (CONTENT_GENERATION)."""

    def __init__(self):
        """Initialize the tester with paths and settings."""
        self.test_dir = Path(__file__).parent
        self.output_dir = self.test_dir / "output"
        self.output_dir.mkdir(exist_ok=True)

        # Load settings
        self.settings = get_settings()

        self._print_header()

    def _print_header(self):
        """Print test suite header."""
        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}     Stage 6 (CONTENT_GENERATION) Standalone Test{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.CYAN}Text Service:{Colors.ENDC} {self.settings.TEXT_SERVICE_URL}")
        print(f"{Colors.CYAN}Version:{Colors.ENDC} v{self.settings.TEXT_SERVICE_VERSION}")
        print(f"{Colors.CYAN}Timeout:{Colors.ENDC} {self.settings.TEXT_SERVICE_TIMEOUT}s")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    def load_test_strawman(self) -> PresentationStrawman:
        """
        Load pre-prepared strawman from JSON.

        Returns:
            PresentationStrawman with all v1.2 fields populated

        Raises:
            FileNotFoundError: If test_strawman.json not found
            ValueError: If strawman validation fails
        """
        strawman_path = self.test_dir / "test_strawman.json"

        print(f"{Colors.CYAN}📄 Loading test strawman...{Colors.ENDC}")
        print(f"   Path: {strawman_path}")

        if not strawman_path.exists():
            raise FileNotFoundError(
                f"test_strawman.json not found at {strawman_path}. "
                "Please ensure the file exists in tests/stage6_only/"
            )

        with open(strawman_path, 'r') as f:
            data = json.load(f)

        strawman = PresentationStrawman(**data)

        print(f"{Colors.GREEN}✅ Strawman loaded successfully{Colors.ENDC}")
        print(f"   Title: {strawman.main_title}")
        print(f"   Slides: {len(strawman.slides)}")
        print(f"   Footer: {strawman.footer_text} ({len(strawman.footer_text)} chars)")
        print(f"   Duration: {strawman.presentation_duration} minutes")

        # Validate v1.2 fields
        self._validate_strawman(strawman)

        return strawman

    def _validate_strawman(self, strawman: PresentationStrawman):
        """
        Validate strawman has all required v1.2 fields.

        Args:
            strawman: Loaded presentation strawman

        Raises:
            ValueError: If validation fails
        """
        print(f"\n{Colors.CYAN}🔍 Validating v1.2 fields...{Colors.ENDC}")

        errors = []
        warnings = []

        # Check presentation-level fields
        if not strawman.footer_text:
            errors.append("Missing footer_text on presentation")
        elif len(strawman.footer_text) > 20:
            errors.append(f"Footer text too long: {len(strawman.footer_text)} chars (max 20)")

        # Check each slide
        for slide in strawman.slides:
            slide_ref = f"Slide {slide.slide_number}"

            # Required fields
            if not slide.variant_id:
                errors.append(f"{slide_ref}: Missing variant_id")
            if not slide.slide_type_classification:
                errors.append(f"{slide_ref}: Missing slide_type_classification")
            if not slide.generated_title:
                errors.append(f"{slide_ref}: Missing generated_title")
            if not slide.layout_id:
                warnings.append(f"{slide_ref}: Missing layout_id (may cause issues)")

            # Character limits
            if slide.generated_title and len(slide.generated_title) > 50:
                errors.append(
                    f"{slide_ref}: generated_title too long: "
                    f"{len(slide.generated_title)} chars (max 50)"
                )
            if slide.generated_subtitle and len(slide.generated_subtitle) > 90:
                errors.append(
                    f"{slide_ref}: generated_subtitle too long: "
                    f"{len(slide.generated_subtitle)} chars (max 90)"
                )

            # Content guidance
            if not slide.content_guidance:
                warnings.append(f"{slide_ref}: Missing content_guidance")

        # Display results
        if errors:
            print(f"{Colors.RED}❌ Validation failed with {len(errors)} error(s):{Colors.ENDC}")
            for error in errors:
                print(f"   {Colors.RED}- {error}{Colors.ENDC}")
            raise ValueError("Strawman validation failed. Fix errors and try again.")

        if warnings:
            print(f"{Colors.YELLOW}⚠️  {len(warnings)} warning(s):{Colors.ENDC}")
            for warning in warnings:
                print(f"   {Colors.YELLOW}- {warning}{Colors.ENDC}")

        print(f"{Colors.GREEN}✅ All required v1.2 fields present{Colors.ENDC}")

        # Show field summary
        print(f"\n{Colors.CYAN}Field Summary:{Colors.ENDC}")
        for slide in strawman.slides:
            print(f"  Slide {slide.slide_number}:")
            print(f"    - Type: {slide.slide_type_classification}")
            print(f"    - Variant: {slide.variant_id}")
            print(f"    - Title: {slide.generated_title} ({len(slide.generated_title)} chars)")
            if slide.generated_subtitle:
                print(f"    - Subtitle: {slide.generated_subtitle} ({len(slide.generated_subtitle)} chars)")

    async def run_stage6_test(self) -> Dict[str, Any]:
        """
        Run Stage 6 test with pre-prepared strawman.

        Returns:
            Dict with test results including success status and timing
        """

        # Load strawman
        strawman = self.load_test_strawman()

        # Initialize Director
        print(f"\n{Colors.CYAN}🎬 Initializing Director Agent...{Colors.ENDC}")
        try:
            director = DirectorAgent()
            print(f"{Colors.GREEN}✅ Director initialized{Colors.ENDC}")
        except Exception as e:
            print(f"{Colors.RED}❌ Director initialization failed: {e}{Colors.ENDC}")
            raise

        # Create StateContext for CONTENT_GENERATION
        print(f"\n{Colors.CYAN}📍 Creating StateContext for CONTENT_GENERATION...{Colors.ENDC}")
        state_context = StateContext(
            current_state="CONTENT_GENERATION",
            session_data={
                "presentation_strawman": strawman.model_dump()
            },
            conversation_history=[]
        )
        print(f"{Colors.GREEN}✅ StateContext created{Colors.ENDC}")
        print(f"   State: CONTENT_GENERATION")
        print(f"   Session Data: presentation_strawman ({len(strawman.slides)} slides)")

        # Run Stage 6
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}🚀 Running Stage 6 (CONTENT_GENERATION)...{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
        print(f"{Colors.YELLOW}⏳ This may take 30-60 seconds...{Colors.ENDC}\n")

        start_time = datetime.now()

        try:
            result = await director.process(state_context)

            duration = (datetime.now() - start_time).total_seconds()

            print(f"\n{Colors.GREEN}{'='*70}{Colors.ENDC}")
            print(f"{Colors.GREEN}✅ Stage 6 completed successfully in {duration:.2f}s{Colors.ENDC}")
            print(f"{Colors.GREEN}{'='*70}{Colors.ENDC}\n")

            # Display results
            self._display_results(result)

            # Save output
            output_path = self._save_output(result, strawman, duration, success=True)

            return {
                "success": True,
                "duration_seconds": duration,
                "result": result,
                "output_file": str(output_path)
            }

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            print(f"\n{Colors.RED}{'='*70}{Colors.ENDC}")
            print(f"{Colors.RED}❌ Stage 6 failed after {duration:.2f}s{Colors.ENDC}")
            print(f"{Colors.RED}{'='*70}{Colors.ENDC}")
            print(f"{Colors.RED}Error: {str(e)}{Colors.ENDC}\n")

            # Print full traceback
            import traceback
            print(f"{Colors.YELLOW}Full Traceback:{Colors.ENDC}")
            traceback.print_exc()

            # Save error output
            output_path = self._save_output(
                {"error": str(e), "traceback": traceback.format_exc()},
                strawman,
                duration,
                success=False
            )

            return {
                "success": False,
                "duration_seconds": duration,
                "error": str(e),
                "output_file": str(output_path)
            }

    def _display_results(self, result: Any):
        """
        Display test results in formatted output.

        Args:
            result: Result from Director.run()
        """
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}")
        print(f"{Colors.BOLD}📊 Test Results{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

        if isinstance(result, dict):
            # Extract key information
            result_type = result.get("type", "unknown")
            slide_count = result.get("slide_count", "unknown")
            successful = result.get("successful_slides", 0)
            failed = result.get("failed_slides", 0)
            skipped = result.get("skipped_slides", 0)
            content_gen = result.get("content_generated", False)

            print(f"{Colors.CYAN}Result Type:{Colors.ENDC} {result_type}")
            print(f"{Colors.CYAN}Total Slides:{Colors.ENDC} {slide_count}")

            # Success/failure/skip metrics
            success_color = Colors.GREEN if successful > 0 else Colors.YELLOW
            fail_color = Colors.RED if failed > 0 else Colors.GREEN
            skip_color = Colors.BLUE if skipped > 0 else Colors.CYAN

            print(f"{Colors.CYAN}Successful:{Colors.ENDC} {success_color}{successful}{Colors.ENDC}")
            print(f"{Colors.CYAN}Failed:{Colors.ENDC} {fail_color}{failed}{Colors.ENDC}")
            print(f"{Colors.CYAN}Skipped:{Colors.ENDC} {skip_color}{skipped}{Colors.ENDC} (hero slides)")

            content_color = Colors.GREEN if content_gen else Colors.RED
            print(f"{Colors.CYAN}Content Generated:{Colors.ENDC} {content_color}{content_gen}{Colors.ENDC}")

            # Presentation URL
            if "url" in result:
                print(f"\n{Colors.CYAN}🔗 Presentation URL:{Colors.ENDC}")
                print(f"   {Colors.UNDERLINE}{result['url']}{Colors.ENDC}")

            # Message
            if "message" in result:
                print(f"\n{Colors.CYAN}Message:{Colors.ENDC}")
                print(f"   {result['message']}")
        else:
            print(f"{Colors.YELLOW}Result Type:{Colors.ENDC} {type(result)}")
            print(f"{Colors.YELLOW}Result:{Colors.ENDC} {result}")

        print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")

    def _save_output(
        self,
        result: Any,
        strawman: PresentationStrawman,
        duration: float,
        success: bool
    ) -> Path:
        """
        Save test output to JSON file.

        Args:
            result: Test result
            strawman: Input strawman
            duration: Test duration in seconds
            success: Whether test passed

        Returns:
            Path to saved output file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "success" if success else "failed"

        # Determine filename
        results_file = self.output_dir / f"test_results_{status}_{timestamp}.json"

        # Prepare output data
        output_data = {
            "test_info": {
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": round(duration, 2),
                "success": success,
                "test_type": "stage6_standalone"
            },
            "strawman_info": {
                "title": strawman.main_title,
                "slide_count": len(strawman.slides),
                "footer_text": strawman.footer_text,
                "duration_minutes": strawman.presentation_duration
            },
            "slides": [
                {
                    "slide_number": slide.slide_number,
                    "classification": slide.slide_type_classification,
                    "variant_id": slide.variant_id,
                    "generated_title": slide.generated_title,
                    "layout_id": slide.layout_id
                }
                for slide in strawman.slides
            ],
            "result": result if isinstance(result, dict) else str(result)
        }

        # Save to file
        with open(results_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        print(f"\n{Colors.GREEN}💾 Results saved to:{Colors.ENDC}")
        print(f"   {results_file}")

        return results_file


async def main():
    """Main test runner."""
    print(f"\n{Colors.BOLD}Starting Stage 6 Standalone Test{Colors.ENDC}\n")

    tester = Stage6Tester()
    result = await tester.run_stage6_test()

    # Final status
    print(f"\n{Colors.BOLD}{'='*70}{Colors.ENDC}")
    if result["success"]:
        print(f"{Colors.GREEN}{Colors.BOLD}✅ TEST PASSED{Colors.ENDC}")
        print(f"{Colors.GREEN}All slides generated successfully!{Colors.ENDC}")
        exit_code = 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌ TEST FAILED{Colors.ENDC}")
        print(f"{Colors.RED}Check error details above{Colors.ENDC}")
        exit_code = 1

    print(f"{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

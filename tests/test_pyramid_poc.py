"""
Pyramid Integration Proof-of-Concept Test

Tests the complete integration pipeline:
Director (simulated) → Illustrator Service → Layout Builder

This validates:
1. Illustrator API generates pyramids correctly
2. Multiple pyramids can be created
3. HTML embeds properly in L25 layout
4. Layout Builder accepts and renders pyramids
5. End-to-end workflow is viable

Author: Director v3.4 Integration Team
Date: January 15, 2025
"""

import httpx
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any

# Service URLs
ILLUSTRATOR_URL = "http://localhost:8000"
LAYOUT_BUILDER_URL = "https://web-production-f0d13.up.railway.app"

# Test configuration
TIMEOUT = 60.0
TEST_OUTPUT_DIR = "tests/pyramid_poc_output"


class PyramidIntegrationTester:
    """Test harness for pyramid integration"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "pyramids": [],
            "presentation": None,
            "success": False,
            "errors": []
        }

    async def test_illustrator_health(self) -> bool:
        """Check if Illustrator service is healthy"""
        print("\n🏥 Checking Illustrator Service Health...")

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{ILLUSTRATOR_URL}/health")

                if response.status_code == 200:
                    print("    ✅ Illustrator service is healthy")
                    return True
                else:
                    print(f"    ❌ Illustrator service unhealthy: {response.status_code}")
                    return False
        except Exception as e:
            print(f"    ❌ Cannot reach Illustrator service: {str(e)}")
            return False

    async def generate_pyramid(
        self,
        num_levels: int,
        topic: str,
        target_points: List[str],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a single pyramid via Illustrator API"""

        payload = {
            "num_levels": num_levels,
            "topic": topic,
            "target_points": target_points,
            "context": context,
            "tone": "professional",
            "audience": "executives",
            "validate_constraints": True
        }

        print(f"\n  📊 Generating {num_levels}-level pyramid: '{topic}'")
        print(f"      Points: {', '.join(target_points)}")

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    f"{ILLUSTRATOR_URL}/v1.0/pyramid/generate",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()

                    print(f"      ✅ Generated: {len(result['html'])} bytes")
                    print(f"      ⏱️  Time: {result['generation_time_ms']}ms")
                    print(f"      🔍 Valid: {result['validation']['valid']}")

                    if not result["validation"]["valid"]:
                        violations = result["validation"]["violations"]
                        print(f"      ⚠️  Violations: {len(violations)}")
                        for v in violations:
                            print(f"          - {v['field']}: {v['actual_length']} chars ({v['status']})")

                    return result
                else:
                    error_msg = f"API error: {response.status_code} - {response.text}"
                    print(f"      ❌ {error_msg}")
                    self.results["errors"].append(error_msg)
                    return None

        except Exception as e:
            error_msg = f"Failed to generate pyramid: {str(e)}"
            print(f"      ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            return None

    async def test_pyramid_generation(self) -> List[Dict[str, Any]]:
        """Test generating 3 pyramids with different configurations"""

        print("\n" + "=" * 80)
        print("📊 Step 1: Generating 3 Pyramids via Illustrator API")
        print("=" * 80)

        pyramid_configs = [
            {
                "num_levels": 4,
                "topic": "Organizational Structure",
                "target_points": ["Vision", "Strategy", "Operations", "Execution"],
                "context": {
                    "presentation_title": "Company Overview",
                    "slide_purpose": "Show reporting hierarchy from execution to vision",
                    "industry": "Technology"
                }
            },
            {
                "num_levels": 3,
                "topic": "Product Development Stages",
                "target_points": ["Launch", "Build", "Plan"],
                "context": {
                    "presentation_title": "Company Overview",
                    "slide_purpose": "Show product development progression",
                    "industry": "Technology"
                }
            },
            {
                "num_levels": 5,
                "topic": "Employee Growth Framework",
                "target_points": ["Expert Level", "Advanced Skills", "Core Competencies", "Intermediate", "Foundation"],
                "context": {
                    "presentation_title": "Company Overview",
                    "slide_purpose": "Show career progression pathway",
                    "industry": "Technology"
                }
            }
        ]

        pyramids = []

        for i, config in enumerate(pyramid_configs, 1):
            print(f"\n🔹 Pyramid {i}/3:")

            result = await self.generate_pyramid(**config)

            if result:
                pyramid_data = {
                    "index": i,
                    "topic": config["topic"],
                    "num_levels": config["num_levels"],
                    "html": result["html"],
                    "html_size_bytes": len(result["html"]),
                    "metadata": result["metadata"],
                    "validation": result["validation"],
                    "generated_content": result["generated_content"]
                }

                pyramids.append(pyramid_data)
                self.results["pyramids"].append({
                    "topic": config["topic"],
                    "success": True,
                    "validation_valid": result["validation"]["valid"],
                    "generation_time_ms": result["metadata"]["generation_time_ms"],
                    "html_size": len(result["html"])
                })
            else:
                self.results["pyramids"].append({
                    "topic": config["topic"],
                    "success": False,
                    "error": "Generation failed"
                })

        print(f"\n✅ Successfully generated {len(pyramids)}/3 pyramids")

        return pyramids

    def transform_to_layout_format(self, pyramids: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform pyramid data to Layout Builder slide format"""

        print("\n" + "=" * 80)
        print("🔄 Step 2: Transforming to Layout Builder Format")
        print("=" * 80)

        slides = []

        # Title slide (L29 hero)
        print("\n  📄 Creating title slide (L29)")
        slides.append({
            "layout": "L29",
            "content": {
                "hero_content": """
                <div style='
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-direction: column;
                    font-family: system-ui, -apple-system, sans-serif;
                '>
                    <h1 style='
                        font-size: 96px;
                        color: white;
                        margin: 0;
                        font-weight: 700;
                    '>Pyramid Test</h1>
                    <p style='
                        font-size: 32px;
                        color: rgba(255, 255, 255, 0.9);
                        margin-top: 20px;
                        font-weight: 300;
                    '>Integration Validation</p>
                </div>
                """
            }
        })

        # Pyramid slides (L25 content)
        for pyramid in pyramids:
            print(f"  📊 Creating pyramid slide: {pyramid['topic']} (L25)")
            print(f"      HTML size: {pyramid['html_size_bytes']} bytes")

            slides.append({
                "layout": "L25",
                "content": {
                    "slide_title": pyramid["topic"],
                    "subtitle": f"{pyramid['num_levels']}-Level Hierarchy",
                    "rich_content": pyramid["html"],
                    "presentation_name": "Pyramid Integration Test"
                }
            })

        # Closing slide (L29 hero)
        print("  📄 Creating closing slide (L29)")
        slides.append({
            "layout": "L29",
            "content": {
                "hero_content": """
                <div style='
                    width: 100%;
                    height: 100%;
                    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-family: system-ui, -apple-system, sans-serif;
                '>
                    <h1 style='
                        font-size: 96px;
                        color: white;
                        font-weight: 700;
                    '>Test Complete ✅</h1>
                </div>
                """
            }
        })

        print(f"\n✅ Created {len(slides)} slides (1 title + {len(pyramids)} pyramids + 1 closing)")

        return slides

    async def create_presentation(self, slides: List[Dict[str, Any]]) -> str:
        """Send slides to Layout Builder and create presentation"""

        print("\n" + "=" * 80)
        print("📦 Step 3: Creating Presentation in Layout Builder")
        print("=" * 80)

        payload = {
            "title": "Pyramid Integration Test - Multiple Slides",
            "slides": slides
        }

        print(f"\n  📤 Sending {len(slides)} slides to Layout Builder...")
        print(f"      URL: {LAYOUT_BUILDER_URL}/api/presentations")

        try:
            async with httpx.AsyncClient(timeout=TIMEOUT) as client:
                response = await client.post(
                    f"{LAYOUT_BUILDER_URL}/api/presentations",
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()
                    presentation_id = result.get("id")

                    print(f"      ✅ Presentation created successfully!")
                    print(f"      🆔 ID: {presentation_id}")

                    presentation_url = f"{LAYOUT_BUILDER_URL}/p/{presentation_id}"
                    print(f"\n      🔗 View at: {presentation_url}")

                    self.results["presentation"] = {
                        "id": presentation_id,
                        "url": presentation_url,
                        "slide_count": len(slides),
                        "success": True
                    }

                    return presentation_url

                else:
                    error_msg = f"Layout Builder error: {response.status_code}"
                    print(f"      ❌ {error_msg}")
                    print(f"      Response: {response.text[:500]}")
                    self.results["errors"].append(error_msg)
                    self.results["presentation"] = {
                        "success": False,
                        "error": error_msg
                    }
                    return None

        except Exception as e:
            error_msg = f"Failed to create presentation: {str(e)}"
            print(f"      ❌ {error_msg}")
            self.results["errors"].append(error_msg)
            self.results["presentation"] = {
                "success": False,
                "error": error_msg
            }
            return None

    def save_results(self):
        """Save test results to JSON file"""

        import os
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

        output_file = f"{TEST_OUTPUT_DIR}/poc_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n💾 Results saved to: {output_file}")

    async def run_complete_test(self):
        """Run the complete integration test"""

        print("\n" + "=" * 80)
        print("🧪 PYRAMID INTEGRATION PROOF-OF-CONCEPT TEST")
        print("=" * 80)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Health check
        if not await self.test_illustrator_health():
            print("\n❌ Illustrator service is not available. Exiting.")
            self.results["success"] = False
            self.save_results()
            return

        # Step 1: Generate pyramids
        pyramids = await self.test_pyramid_generation()

        if not pyramids:
            print("\n❌ No pyramids generated. Exiting.")
            self.results["success"] = False
            self.save_results()
            return

        # Step 2: Transform to layout format
        slides = self.transform_to_layout_format(pyramids)

        # Step 3: Create presentation
        presentation_url = await self.create_presentation(slides)

        # Summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        if presentation_url:
            print("\n✅ TEST SUCCESSFUL!")
            print(f"\n🎯 Results:")
            print(f"   - Pyramids generated: {len(pyramids)}/3")
            print(f"   - Total slides: {len(slides)}")
            print(f"   - Presentation URL: {presentation_url}")

            self.results["success"] = True

            print(f"\n🔍 Next Steps:")
            print(f"   1. Open the presentation URL in your browser")
            print(f"   2. Verify all pyramid slides render correctly")
            print(f"   3. Check for any CSS conflicts or layout issues")
            print(f"   4. Review the test results JSON file")

        else:
            print("\n❌ TEST FAILED")
            print(f"\n❌ Errors encountered:")
            for error in self.results["errors"]:
                print(f"   - {error}")

            self.results["success"] = False

        # Save results
        self.save_results()

        print(f"\n⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)


async def main():
    """Main test execution"""
    tester = PyramidIntegrationTester()
    await tester.run_complete_test()


if __name__ == "__main__":
    asyncio.run(main())

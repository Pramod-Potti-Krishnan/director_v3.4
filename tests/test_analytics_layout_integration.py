"""
Analytics Service v3 + Layout Builder L02 Integration Test
===========================================================

Tests end-to-end flow:
1. Call Analytics Service L02 endpoint
2. Get 2-field response (element_3 chart + element_2 observations)
3. Assemble into L02 layout format
4. Send to Layout Builder
5. Verify rendered presentation

Usage:
    python test_analytics_layout_integration.py
"""

import asyncio
import httpx
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, '/Users/pk1980/Documents/Software/deckster-backend/deckster-w-content-strategist/agents/director_agent/v3.4')

from src.clients.analytics_client import AnalyticsClient
from config.settings import get_settings


# Configuration
ANALYTICS_SERVICE_URL = "https://analytics-v30-production.up.railway.app"
LAYOUT_BUILDER_URL = "https://web-production-f0d13.up.railway.app"


async def test_1_analytics_service_l02():
    """Test 1: Call Analytics Service L02 endpoint directly."""
    print("\n" + "=" * 80)
    print("TEST 1: Analytics Service L02 Direct Call")
    print("=" * 80)

    test_cases = [
        {
            "name": "Revenue Over Time",
            "analytics_type": "revenue_over_time",
            "data": [
                {"label": "Q1 2024", "value": 125000},
                {"label": "Q2 2024", "value": 145000},
                {"label": "Q3 2024", "value": 162000},
                {"label": "Q4 2024", "value": 195000}
            ],
            "narrative": "Show quarterly revenue growth with strong Q4 performance",
            "title": "Quarterly Revenue Growth",
            "subtitle": "FY 2024 Performance"
        },
        {
            "name": "Market Share Analysis",
            "analytics_type": "market_share",
            "data": [
                {"label": "Our Company", "value": 35},
                {"label": "Competitor A", "value": 28},
                {"label": "Competitor B", "value": 22},
                {"label": "Others", "value": 15}
            ],
            "narrative": "Market share distribution across major players",
            "title": "Market Share Distribution",
            "subtitle": "Q4 2024"
        },
        {
            "name": "YoY Growth",
            "analytics_type": "yoy_growth",
            "data": [
                {"label": "2021", "value": 2.5},
                {"label": "2022", "value": 8.3},
                {"label": "2023", "value": 12.7},
                {"label": "2024", "value": 18.9}
            ],
            "narrative": "Year-over-year growth acceleration",
            "title": "YoY Growth Trend",
            "subtitle": "2021-2024"
        }
    ]

    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📊 Test Case {i}: {test_case['name']}")
            print(f"   Analytics Type: {test_case['analytics_type']}")
            print(f"   Data Points: {len(test_case['data'])}")

            try:
                # Call Analytics Service L02 endpoint
                endpoint = f"{ANALYTICS_SERVICE_URL}/api/v1/analytics/L02/{test_case['analytics_type']}"

                payload = {
                    "presentation_id": f"test-pres-{i}",
                    "slide_id": f"slide-{i}",
                    "slide_number": i,
                    "narrative": test_case["narrative"],
                    "data": test_case["data"],
                    "context": {
                        "theme": "professional",
                        "audience": "Board of Directors",
                        "slide_title": test_case["title"],
                        "subtitle": test_case["subtitle"]
                    },
                    "options": {
                        "enable_editor": False
                    }
                }

                print(f"   Calling: {endpoint}")
                response = await client.post(endpoint, json=payload)

                if response.status_code == 200:
                    data = response.json()

                    # Verify 2-field response
                    assert "content" in data, "Missing 'content' field"
                    assert "element_3" in data["content"], "Missing 'element_3' (chart)"
                    assert "element_2" in data["content"], "Missing 'element_2' (observations)"

                    chart_html = data["content"]["element_3"]
                    obs_html = data["content"]["element_2"]

                    print(f"   ✅ Success:")
                    print(f"      - element_3 (chart): {len(chart_html)} chars")
                    print(f"      - element_2 (observations): {len(obs_html)} chars")
                    print(f"      - Generation time: {data['metadata'].get('generation_time_ms', 0)}ms")

                    results.append({
                        "test_case": test_case["name"],
                        "success": True,
                        "response": data,
                        "title": test_case["title"],
                        "subtitle": test_case["subtitle"]
                    })
                else:
                    print(f"   ❌ Failed: HTTP {response.status_code}")
                    results.append({
                        "test_case": test_case["name"],
                        "success": False,
                        "error": f"HTTP {response.status_code}"
                    })

            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                results.append({
                    "test_case": test_case["name"],
                    "success": False,
                    "error": str(e)
                })

    success_count = sum(1 for r in results if r["success"])
    print(f"\n✅ Test 1 Results: {success_count}/{len(test_cases)} analytics calls successful")

    return results


async def test_2_l02_layout_assembly(analytics_results: List[Dict]):
    """Test 2: Assemble Analytics responses into L02 layout format."""
    print("\n" + "=" * 80)
    print("TEST 2: L02 Layout Assembly")
    print("=" * 80)

    l02_slides = []

    for i, result in enumerate(analytics_results, 1):
        if not result["success"]:
            print(f"\n⚠️  Skipping {result['test_case']} (analytics call failed)")
            continue

        print(f"\n📋 Assembling Slide {i}: {result['test_case']}")

        analytics_response = result["response"]

        # Assemble L02 layout following the integration guide
        l02_slide = {
            "layout": "L25",
            "variant_id": "L02",  # Director uses variant_id
            "content": {
                # Director provides
                "slide_title": result["title"],
                "element_1": result["subtitle"],

                # Analytics provides
                "element_3": analytics_response["content"]["element_3"],  # Chart HTML
                "element_2": analytics_response["content"]["element_2"],  # Observations HTML

                # Director provides
                "presentation_name": "Analytics Test Suite",
                "company_logo": ""
            },
            "metadata": {
                "analytics_type": analytics_response["metadata"]["analytics_type"],
                "chart_type": analytics_response["metadata"]["chart_type"],
                "source": "analytics_service_v3"
            }
        }

        print(f"   ✅ L02 slide assembled:")
        print(f"      - layout: {l02_slide['layout']}")
        print(f"      - variant_id: {l02_slide['variant_id']}")
        print(f"      - slide_title: {l02_slide['content']['slide_title']}")
        print(f"      - element_1 (subtitle): {l02_slide['content']['element_1']}")
        print(f"      - element_3 (chart): {len(l02_slide['content']['element_3'])} chars")
        print(f"      - element_2 (observations): {len(l02_slide['content']['element_2'])} chars")

        l02_slides.append(l02_slide)

    print(f"\n✅ Test 2 Results: {len(l02_slides)} L02 slides assembled")
    return l02_slides


async def test_3_layout_builder_integration(l02_slides: List[Dict]):
    """Test 3: Send L02 slides to Layout Builder and verify rendering."""
    print("\n" + "=" * 80)
    print("TEST 3: Layout Builder Integration")
    print("=" * 80)

    if not l02_slides:
        print("⚠️  No L02 slides to send (skipping)")
        return None

    print(f"\n📤 Sending {len(l02_slides)} slides to Layout Builder")
    print(f"   URL: {LAYOUT_BUILDER_URL}")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Prepare presentation payload
            presentation_payload = {
                "title": "Analytics Test Suite - L02 Integration",
                "slides": l02_slides
            }

            # Send to Layout Builder
            endpoint = f"{LAYOUT_BUILDER_URL}/api/presentations"
            print(f"   Endpoint: {endpoint}")
            print(f"   Presentation Title: {presentation_payload['title']}")

            response = await client.post(endpoint, json=presentation_payload)

            if response.status_code in [200, 201]:
                data = response.json()
                presentation_id = data.get("id") or data.get("presentation_id")

                if presentation_id:
                    preview_url = f"{LAYOUT_BUILDER_URL}/static/builder.html?id={presentation_id}"
                    print(f"\n   ✅ Presentation Created Successfully!")
                    print(f"      - Presentation ID: {presentation_id}")
                    print(f"      - Preview URL: {preview_url}")
                    print(f"      - Slides: {len(l02_slides)}")

                    return {
                        "success": True,
                        "presentation_id": presentation_id,
                        "preview_url": preview_url,
                        "slides_count": len(l02_slides)
                    }
                else:
                    print(f"   ⚠️  Presentation created but no ID returned")
                    return {"success": False, "error": "No presentation ID"}
            else:
                print(f"   ❌ Failed: HTTP {response.status_code}")
                print(f"   Response: {response.text[:500]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        return {"success": False, "error": str(e)}


async def test_4_analytics_client_l02():
    """Test 4: Use AnalyticsClient with L02 layout."""
    print("\n" + "=" * 80)
    print("TEST 4: AnalyticsClient L02 Integration")
    print("=" * 80)

    settings = get_settings()
    client = AnalyticsClient(
        base_url=settings.ANALYTICS_SERVICE_URL,
        timeout=settings.ANALYTICS_SERVICE_TIMEOUT
    )

    print(f"\n📊 Testing AnalyticsClient.generate_chart() with L02 layout")

    test_data = [
        {"label": "Q1", "value": 100},
        {"label": "Q2", "value": 120},
        {"label": "Q3", "value": 158},
        {"label": "Q4", "value": 180}
    ]

    try:
        result = await client.generate_chart(
            analytics_type="revenue_over_time",
            layout="L02",  # Specify L02 layout
            data=test_data,
            narrative="Quarterly revenue growth showing 58% increase in Q3",
            context={
                "presentation_title": "Q4 Business Review",
                "tone": "professional",
                "audience": "executives",
                "slide_title": "Revenue Growth",
                "subtitle": "Q1-Q4 2024"
            },
            presentation_id="test_client_001",
            slide_id="slide_client_002",
            slide_number=2
        )

        # Verify response structure
        assert "content" in result
        assert "element_3" in result["content"]
        assert "element_2" in result["content"]

        print(f"   ✅ AnalyticsClient call successful:")
        print(f"      - element_3: {len(result['content']['element_3'])} chars")
        print(f"      - element_2: {len(result['content']['element_2'])} chars")
        print(f"      - Layout: {result['metadata'].get('layout')}")

        return {"success": True, "response": result}

    except Exception as e:
        print(f"   ❌ AnalyticsClient error: {str(e)}")
        return {"success": False, "error": str(e)}


async def main():
    """Run all L02 integration tests."""
    print("\n" + "=" * 100)
    print("ANALYTICS SERVICE v3 + LAYOUT BUILDER L02 INTEGRATION TEST SUITE")
    print("Testing: Analytics → L02 Assembly → Layout Builder Rendering")
    print("=" * 100)

    start_time = datetime.now()

    # Test 1: Call Analytics Service L02 endpoints
    print("\n🔹 Phase 1: Analytics Service L02 API Calls")
    analytics_results = await test_1_analytics_service_l02()

    # Test 2: Assemble into L02 layout format
    print("\n🔹 Phase 2: L02 Layout Assembly")
    l02_slides = await test_2_l02_layout_assembly(analytics_results)

    # Test 3: Send to Layout Builder
    print("\n🔹 Phase 3: Layout Builder Integration")
    layout_result = await test_3_layout_builder_integration(l02_slides)

    # Test 4: Test AnalyticsClient
    print("\n🔹 Phase 4: AnalyticsClient Testing")
    client_result = await test_4_analytics_client_l02()

    # Summary
    duration = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 100)
    print("TEST SUITE SUMMARY")
    print("=" * 100)

    analytics_success = sum(1 for r in analytics_results if r["success"])
    print(f"\n✅ Test 1 - Analytics API Calls: {analytics_success}/3 successful")
    print(f"✅ Test 2 - L02 Layout Assembly: {len(l02_slides)} slides assembled")

    if layout_result and layout_result.get("success"):
        print(f"✅ Test 3 - Layout Builder: Presentation created")
        print(f"   📊 Preview URL: {layout_result['preview_url']}")
    else:
        print(f"❌ Test 3 - Layout Builder: Failed")

    if client_result and client_result.get("success"):
        print(f"✅ Test 4 - AnalyticsClient: Working correctly")
    else:
        print(f"❌ Test 4 - AnalyticsClient: Failed")

    print(f"\n⏱️  Total Duration: {duration:.2f}s")

    if layout_result and layout_result.get("success"):
        print("\n" + "=" * 100)
        print("🎉 SUCCESS! Analytics slides rendered in Layout Builder")
        print("=" * 100)
        print(f"\n🔗 Open this URL to view the presentation:")
        print(f"   {layout_result['preview_url']}")
        print(f"\n📊 Slides included:")
        for i, slide in enumerate(l02_slides, 1):
            print(f"   {i}. {slide['content']['slide_title']} ({slide['metadata']['analytics_type']})")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

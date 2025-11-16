"""
Test Analytics with layout: "L02" instead of layout: "L25"
"""

import asyncio
import httpx

ANALYTICS_URL = "https://analytics-v30-production.up.railway.app"
LAYOUT_BUILDER_URL = "https://web-production-f0d13.up.railway.app"


async def create_l02_presentation():
    """Create analytics presentation using layout: L02 directly."""

    print("=" * 70)
    print("ANALYTICS TEST - Using layout: 'L02' (not L25)")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Call Analytics Service
        print("\n🔹 Step 1: Calling Analytics Service")

        analytics_response = await client.post(
            f"{ANALYTICS_URL}/api/v1/analytics/L02/revenue_over_time",
            json={
                "presentation_id": "test-l02-direct",
                "slide_id": "slide-001",
                "slide_number": 1,
                "narrative": "Strong quarterly revenue growth throughout 2024",
                "data": [
                    {"label": "Q1 2024", "value": 125000},
                    {"label": "Q2 2024", "value": 145000},
                    {"label": "Q3 2024", "value": 162000},
                    {"label": "Q4 2024", "value": 195000}
                ],
                "context": {
                    "theme": "professional",
                    "slide_title": "Quarterly Revenue Growth",
                    "subtitle": "FY 2024 Performance"
                }
            }
        )

        if analytics_response.status_code != 200:
            print(f"❌ Analytics error: {analytics_response.status_code}")
            return

        analytics_data = analytics_response.json()
        print(f"✅ Analytics response received")

        # Step 2: Assemble slide with layout: "L02"
        print("\n🔹 Step 2: Assembling slide with layout: 'L02'")

        slide = {
            "layout": "L02",  # Using L02 directly instead of L25
            "content": {
                "slide_title": "Quarterly Revenue Growth",
                "element_1": "FY 2024 Performance",
                "element_3": analytics_data["content"]["element_3"],
                "element_2": analytics_data["content"]["element_2"],
                "presentation_name": "Analytics Demo"
            }
        }

        print(f"✅ Slide assembled:")
        print(f"   - layout: {slide['layout']}")
        print(f"   - content.element_3: {len(slide['content']['element_3'])} chars")
        print(f"   - content.element_2: {len(slide['content']['element_2'])} chars")

        # Step 3: Send to Layout Builder
        print("\n🔹 Step 3: Sending to Layout Builder")

        presentation_payload = {
            "title": "Analytics Test - L02 Layout Direct",
            "slides": [slide]
        }

        layout_response = await client.post(
            f"{LAYOUT_BUILDER_URL}/api/presentations",
            json=presentation_payload,
            timeout=30.0
        )

        if layout_response.status_code not in [200, 201]:
            print(f"❌ Layout Builder error: {layout_response.status_code}")
            print(layout_response.text[:500])
            return

        result = layout_response.json()
        pres_id = result.get("id") or result.get("presentation_id")

        print(f"✅ Presentation created: {pres_id}")

        # Step 4: Verify what was saved
        print("\n🔹 Step 4: Verifying saved data")

        verify_response = await client.get(
            f"{LAYOUT_BUILDER_URL}/api/presentations/{pres_id}"
        )

        if verify_response.status_code == 200:
            saved_data = verify_response.json()
            saved_slide = saved_data["slides"][0]

            print(f"   Saved layout: {saved_slide.get('layout')}")
            print(f"   Saved keys: {list(saved_slide.keys())}")
            print(f"   Has variant_id: {'variant_id' in saved_slide}")

        # Step 5: Open both viewer endpoints
        preview_url = f"{LAYOUT_BUILDER_URL}/static/builder.html?id={pres_id}"
        viewer_url = f"{LAYOUT_BUILDER_URL}/p/{pres_id}"

        print(f"\n{'=' * 70}")
        print(f"🎉 PRESENTATION CREATED")
        print(f"{'=' * 70}")
        print(f"\n🔗 Builder URL:")
        print(f"   {preview_url}")
        print(f"\n🔗 Viewer URL:")
        print(f"   {viewer_url}")
        print(f"\n📊 Using layout: 'L02' (instead of L25)")

        import subprocess
        subprocess.run(["open", preview_url])

        return pres_id


if __name__ == "__main__":
    asyncio.run(create_l02_presentation())

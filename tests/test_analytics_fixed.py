"""
Analytics + Layout Builder Test - Fixed for variant_id persistence
"""

import asyncio
import httpx
import json

ANALYTICS_URL = "https://analytics-v30-production.up.railway.app"
LAYOUT_BUILDER_URL = "https://web-production-f0d13.up.railway.app"


async def create_analytics_presentation():
    """Create analytics presentation ensuring variant_id is preserved."""

    print("=" * 70)
    print("ANALYTICS + LAYOUT BUILDER TEST (variant_id fix)")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Step 1: Call Analytics Service
        print("\n🔹 Step 1: Calling Analytics Service")

        analytics_response = await client.post(
            f"{ANALYTICS_URL}/api/v1/analytics/L02/revenue_over_time",
            json={
                "presentation_id": "test-fixed-001",
                "slide_id": "slide-001",
                "slide_number": 1,
                "narrative": "Quarterly revenue growth with strong Q4",
                "data": [
                    {"label": "Q1 2024", "value": 125000},
                    {"label": "Q2 2024", "value": 145000},
                    {"label": "Q3 2024", "value": 162000},
                    {"label": "Q4 2024", "value": 195000}
                ],
                "context": {
                    "theme": "professional",
                    "slide_title": "Quarterly Revenue Performance",
                    "subtitle": "FY 2024 Strong Growth"
                }
            }
        )

        if analytics_response.status_code != 200:
            print(f"❌ Analytics error: {analytics_response.status_code}")
            return

        analytics_data = analytics_response.json()
        print(f"✅ Analytics response received")
        print(f"   Chart: {len(analytics_data['content']['element_3'])} chars")
        print(f"   Observations: {len(analytics_data['content']['element_2'])} chars")

        # Step 2: Assemble slide with variant_id at TOP LEVEL
        print("\n🔹 Step 2: Assembling slide (variant_id at top level)")

        slide = {
            "layout": "L25",
            "variant_id": "L02",  # TOP LEVEL - critical for rendering
            "content": {
                "slide_title": "Quarterly Revenue Performance",
                "element_1": "FY 2024 Strong Growth",
                "element_3": analytics_data["content"]["element_3"],
                "element_2": analytics_data["content"]["element_2"],
                "presentation_name": "Analytics Demo"
            }
        }

        print(f"✅ Slide structure:")
        print(f"   - layout: {slide['layout']}")
        print(f"   - variant_id: {slide['variant_id']}")
        print(f"   - content keys: {list(slide['content'].keys())}")

        # Step 3: Send to Layout Builder
        print("\n🔹 Step 3: Sending to Layout Builder")

        presentation_payload = {
            "title": "Analytics Demo - Revenue Performance",
            "slides": [slide]
        }

        print(f"Payload preview:")
        print(f"  - slides[0].variant_id: {presentation_payload['slides'][0].get('variant_id')}")

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

        if not pres_id:
            print("❌ No presentation ID returned")
            return

        print(f"✅ Presentation created: {pres_id}")

        # Step 4: Verify variant_id was saved
        print("\n🔹 Step 4: Verifying variant_id persistence")

        verify_response = await client.get(
            f"{LAYOUT_BUILDER_URL}/api/presentations/{pres_id}"
        )

        if verify_response.status_code == 200:
            saved_data = verify_response.json()
            saved_slide = saved_data["slides"][0]

            has_variant_id = "variant_id" in saved_slide
            variant_value = saved_slide.get("variant_id", "MISSING")

            print(f"   variant_id present: {has_variant_id}")
            print(f"   variant_id value: {variant_value}")

            if has_variant_id and variant_value == "L02":
                print(f"   ✅ variant_id correctly saved!")
            else:
                print(f"   ⚠️  variant_id NOT saved or incorrect")
                print(f"   Saved slide keys: {list(saved_slide.keys())}")

        # Step 5: Open preview
        preview_url = f"{LAYOUT_BUILDER_URL}/static/builder.html?id={pres_id}"

        print(f"\n{'=' * 70}")
        print(f"🎉 PRESENTATION READY")
        print(f"{'=' * 70}")
        print(f"\n🔗 Preview URL:")
        print(f"   {preview_url}")
        print(f"\n📊 Slide Details:")
        print(f"   - Layout: L25")
        print(f"   - Variant: L02")
        print(f"   - Chart Type: Line (revenue over time)")
        print(f"   - Data Points: Q1-Q4 2024")

        import subprocess
        subprocess.run(["open", preview_url])

        return pres_id


if __name__ == "__main__":
    asyncio.run(create_analytics_presentation())

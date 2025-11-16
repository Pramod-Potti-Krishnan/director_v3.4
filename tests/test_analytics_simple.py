"""
Simple Analytics + Layout Builder Test
Quick test to create analytics presentation with debugging
"""

import asyncio
import httpx
import json

ANALYTICS_URL = "https://analytics-v30-production.up.railway.app"
LAYOUT_BUILDER_URL = "https://web-production-f0d13.up.railway.app"


async def create_analytics_presentation():
    """Create a simple analytics presentation."""

    print("🔹 Step 1: Calling Analytics Service")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Call Analytics Service
        analytics_response = await client.post(
            f"{ANALYTICS_URL}/api/v1/analytics/L02/revenue_over_time",
            json={
                "presentation_id": "test-simple-001",
                "slide_id": "slide-001",
                "slide_number": 1,
                "narrative": "Quarterly revenue growth",
                "data": [
                    {"label": "Q1", "value": 100000},
                    {"label": "Q2", "value": 125000},
                    {"label": "Q3", "value": 150000},
                    {"label": "Q4", "value": 180000}
                ],
                "context": {
                    "theme": "professional",
                    "slide_title": "Revenue Growth Q1-Q4",
                    "subtitle": "2024 Performance"
                }
            }
        )

        if analytics_response.status_code != 200:
            print(f"❌ Analytics Service error: {analytics_response.status_code}")
            print(analytics_response.text)
            return

        analytics_data = analytics_response.json()
        print(f"✅ Analytics response received")
        print(f"   - element_3: {len(analytics_data['content']['element_3'])} chars")
        print(f"   - element_2: {len(analytics_data['content']['element_2'])} chars")

        # Assemble L02 slide
        print("\n🔹 Step 2: Assembling L02 Slide")

        slide = {
            "layout": "L25",
            "variant_id": "L02",
            "content": {
                "slide_title": "Revenue Growth Q1-Q4",
                "element_1": "2024 Performance",
                "element_3": analytics_data["content"]["element_3"],
                "element_2": analytics_data["content"]["element_2"],
                "presentation_name": "Analytics Demo"
            }
        }

        print(f"✅ Slide assembled")

        # Send to Layout Builder
        print("\n🔹 Step 3: Sending to Layout Builder")

        presentation_payload = {
            "title": "Analytics Demo - Revenue Growth",
            "slides": [slide]
        }

        print(f"Payload size: {len(json.dumps(presentation_payload))} bytes")

        layout_response = await client.post(
            f"{LAYOUT_BUILDER_URL}/api/presentations",
            json=presentation_payload
        )

        print(f"Response status: {layout_response.status_code}")

        if layout_response.status_code in [200, 201]:
            result = layout_response.json()
            pres_id = result.get("id") or result.get("presentation_id")

            if pres_id:
                preview_url = f"{LAYOUT_BUILDER_URL}/static/builder.html?id={pres_id}"
                print(f"\n✅ SUCCESS!")
                print(f"Presentation ID: {pres_id}")
                print(f"Preview URL: {preview_url}")

                # Try to verify the presentation exists
                verify_response = await client.get(
                    f"{LAYOUT_BUILDER_URL}/api/presentations/{pres_id}"
                )
                print(f"\nVerification status: {verify_response.status_code}")
                if verify_response.status_code == 200:
                    print("✅ Presentation verified - accessible")
                else:
                    print(f"⚠️  Presentation verification failed: {verify_response.text[:200]}")

                return preview_url
            else:
                print(f"⚠️  No presentation ID in response")
                print(f"Response: {result}")
        else:
            print(f"❌ Layout Builder error: {layout_response.status_code}")
            print(f"Response: {layout_response.text[:500]}")


async def main():
    print("=" * 70)
    print("SIMPLE ANALYTICS + LAYOUT BUILDER TEST")
    print("=" * 70)

    preview_url = await create_analytics_presentation()

    if preview_url:
        print("\n" + "=" * 70)
        print("🎉 PRESENTATION CREATED")
        print("=" * 70)
        print(f"\n🔗 Open this URL:")
        print(f"   {preview_url}")

        # Open in browser
        import subprocess
        subprocess.run(["open", preview_url])
    else:
        print("\n❌ Failed to create presentation")


if __name__ == "__main__":
    asyncio.run(main())

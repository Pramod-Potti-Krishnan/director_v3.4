#!/usr/bin/env python3
"""
Create a presentation with verified pyramid slides using Layout Builder on Railway.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.clients.illustrator_client import IllustratorClient
import httpx


async def create_pyramid_presentation():
    """Generate pyramids and create presentation on Railway."""

    print("=" * 80)
    print("CREATING PYRAMID PRESENTATION ON RAILWAY")
    print("=" * 80)
    print()

    # Initialize Illustrator client
    illustrator_client = IllustratorClient(
        base_url="http://localhost:8000",
        timeout=60
    )

    # Pyramid configurations
    pyramid_configs = [
        {
            "name": "Organizational Hierarchy",
            "num_levels": 4,
            "topic": "Our Organizational Structure",
            "target_points": [
                "Executive Leadership",
                "Department Management",
                "Team Coordination",
                "Individual Contributors"
            ],
            "tone": "professional",
            "audience": "executives"
        },
        {
            "name": "Product Strategy",
            "num_levels": 3,
            "topic": "Product Development Strategy",
            "target_points": [
                "Vision & Strategy",
                "Planning & Design",
                "Execution & Delivery"
            ],
            "tone": "professional",
            "audience": "product teams"
        },
        {
            "name": "Career Progression",
            "num_levels": 5,
            "topic": "Engineering Career Path",
            "target_points": [
                "Principal Engineer",
                "Senior Engineer",
                "Mid-Level Engineer",
                "Junior Engineer",
                "Entry Level"
            ],
            "tone": "inspirational",
            "audience": "engineers"
        }
    ]

    slides = []

    print("📊 Generating Pyramid Slides...")
    print()

    # Generate pyramids
    for i, config in enumerate(pyramid_configs, 1):
        print(f"{i}. Generating: {config['name']} ({config['num_levels']} levels)")

        try:
            # Add delay to avoid rate limiting
            if i > 1:
                await asyncio.sleep(3)

            # Generate pyramid
            response = await illustrator_client.generate_pyramid(
                num_levels=config['num_levels'],
                topic=config['topic'],
                target_points=config['target_points'],
                tone=config['tone'],
                audience=config['audience'],
                validate_constraints=True
            )

            html = response.get('html', '')

            # Check for placeholders
            has_placeholders = '{overview_heading}' in html or '{overview_text}' in html

            if has_placeholders:
                print(f"   ⚠️  WARNING: Placeholders found in HTML!")
            else:
                print(f"   ✅ Generated successfully ({len(html):,} chars)")

            # Add to slides
            slides.append({
                "slide_title": config['topic'],
                "rich_content": html
            })

        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            return None

    print()
    print(f"✅ Generated {len(slides)} pyramid slides")
    print()

    # Create presentation with Layout Builder
    print("=" * 80)
    print("CREATING PRESENTATION ON RAILWAY")
    print("=" * 80)
    print()

    layout_builder_url = "https://web-production-f0d13.up.railway.app"

    # Add title slide
    presentation_slides = [
        {
            "slide_title": "Pyramid Visualizations",
            "slide_subtitle": "Bug Fix Verification",
            "presentation_name": "Pyramid Bug Fix Verification"
        }
    ] + slides

    # Prepare presentation data
    presentation_data = {
        "title": "Pyramid Bug Fix Verification",
        "slides": []
    }

    # Convert to Layout Builder format
    for i, slide in enumerate(presentation_slides):
        if i == 0:
            # Title slide
            presentation_data["slides"].append({
                "layout": "L01",  # Title slide layout
                "content": {
                    "slide_title": slide["slide_title"],
                    "slide_subtitle": slide.get("slide_subtitle", ""),
                    "presentation_name": slide.get("presentation_name", "")
                }
            })
        else:
            # Content slide with pyramid
            presentation_data["slides"].append({
                "layout": "L25",  # Rich content layout
                "content": {
                    "slide_title": slide["slide_title"],
                    "rich_content": slide["rich_content"]
                }
            })

    print(f"Presentation: {presentation_data['title']}")
    print(f"Total Slides: {len(presentation_data['slides'])}")
    print(f"   - Title slide: 1")
    print(f"   - Pyramid slides: {len(slides)}")
    print()

    try:
        # Create presentation via Layout Builder API
        endpoint = f"{layout_builder_url}/api/presentations"

        print(f"Calling: {endpoint}")
        print("Sending presentation data...")
        print()

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                endpoint,
                json=presentation_data
            )
            response.raise_for_status()
            result = response.json()

        presentation_id = result.get('id')
        presentation_url = result.get('url')
        full_url = f"{layout_builder_url}{presentation_url}"

        print("=" * 80)
        print("✅ PRESENTATION CREATED SUCCESSFULLY!")
        print("=" * 80)
        print()
        print(f"🎉 Presentation URL: {full_url}")
        print()
        print(f"Presentation ID: {presentation_id}")
        print(f"Slide Count: {len(presentation_data['slides'])}")
        print(f"Pyramid Count: {len(slides)}")
        print()

        # Save presentation info
        pres_info = {
            "status": "success",
            "presentation_url": full_url,
            "presentation_id": presentation_id,
            "railway_url": layout_builder_url,
            "slide_count": len(presentation_data['slides']),
            "pyramid_count": len(slides),
            "pyramids": [p["name"] for p in pyramid_configs],
            "response": result
        }

        with open("test_output/pyramid_presentation_verified.json", 'w') as f:
            json.dump(pres_info, f, indent=2)

        print(f"📊 Presentation info saved to: test_output/pyramid_presentation_verified.json")
        print()

        return full_url

    except httpx.HTTPStatusError as e:
        print(f"❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Failed to create presentation: {e}")
        return None


if __name__ == "__main__":
    url = asyncio.run(create_pyramid_presentation())
    sys.exit(0 if url else 1)

"""
Direct test of Text Service + Deck Builder integration.

Tests the new constraint limits (L25: 1250 chars, L29: 500 chars)
and verifies visual richness in the deck builder output.

This bypasses Director stages 1-5 to focus on Stage 6 content generation quality.
"""

import asyncio
import json
import requests
from typing import Dict, Any

# Service URLs
TEXT_SERVICE_URL = "http://localhost:8002"
DECK_BUILDER_URL = "http://localhost:8504"


def generate_text_content(slide_number: int, layout: str, title: str, narrative: str, key_points: list) -> Dict[str, Any]:
    """
    Generate content using local text service with new constraints.

    Args:
        slide_number: Slide number
        layout: Layout ID (L25 or L29)
        title: Slide title
        narrative: Narrative/description
        key_points: List of key points

    Returns:
        Generated content dictionary
    """
    # Simulate Director's constraint calculation with NEW smart defaults
    if layout == "L25":
        # L25 rich_content: 1250 chars (~250 words)
        max_characters = 1250
        format_type = "bullet_points" if key_points else "paragraph"
    else:  # L29
        # L29 hero_content: 500 chars (~100 words)
        max_characters = 500
        format_type = "paragraph"

    # v3.3: Determine layout metadata for conditional prompt rules
    slide_purpose = None
    suggested_pattern = None

    if layout == "L29":
        # Determine L29 slide purpose
        if slide_number == 1:
            slide_purpose = "title_slide"
        elif "Join Us" in title or "Thank You" in title or "Questions" in title:
            slide_purpose = "closing_slide"
        else:
            slide_purpose = "section_divider"
    else:  # L25
        # Determine L25 suggested pattern based on content
        if key_points and any("$" in kp or "%" in kp or any(char.isdigit() for char in kp) for kp in key_points):
            suggested_pattern = "3-card-metrics-grid"
        elif key_points and len(key_points) >= 4:
            suggested_pattern = "2-column-split-lists"
        else:
            suggested_pattern = "standard-content"

    # Build text service request
    request_payload = {
        "presentation_id": "test_presentation",
        "slide_id": f"slide_{slide_number}",
        "slide_number": slide_number,
        "topics": key_points if key_points else [title],
        "narrative": narrative,
        "context": {
            "presentation_theme": "Testing rich content generation",
            "target_audience": "Business executives",
            "previous_slides": []
        },
        "constraints": {
            "max_characters": max_characters,
            "tone": "professional",
            "format": format_type
        },
        # v3.3: Explicit layout metadata for prompt conditionals
        "layout_id": layout,
        "slide_purpose": slide_purpose,  # Only for L29
        "suggested_pattern": suggested_pattern  # Only for L25
    }

    print(f"\n{'='*60}")
    print(f"Generating content for {layout} slide #{slide_number}")
    print(f"  Title: {title}")
    print(f"  Max characters: {max_characters} (~{int(max_characters/5)} words)")
    print(f"  Format: {format_type}")
    print(f"  Layout metadata:")
    print(f"    - layout_id: {layout}")
    print(f"    - slide_purpose: {slide_purpose or 'N/A (L25 slide)'}")
    print(f"    - suggested_pattern: {suggested_pattern or 'N/A (L29 slide)'}")
    print(f"{'='*60}")

    # Call text service (increased timeout for gemini-2.5-pro)
    response = requests.post(
        f"{TEXT_SERVICE_URL}/api/v1/generate/text",
        json=request_payload,
        timeout=120
    )

    if response.status_code == 200:
        result = response.json()
        generated_html = result.get("content", "")
        word_count = result.get("metadata", {}).get("word_count", 0)
        char_count = len(generated_html)

        print(f"\n✅ Content generated successfully!")
        print(f"  Characters: {char_count} / {max_characters} ({int(char_count/max_characters*100)}%)")
        print(f"  Words: {word_count}")
        print(f"\n📝 Generated HTML preview:")
        print(f"  {generated_html[:200]}...")

        return {
            "success": True,
            "content": generated_html,
            "metadata": result.get("metadata", {})
        }
    else:
        print(f"\n❌ Text generation failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return {
            "success": False,
            "content": f"<p>Error generating content: {response.text}</p>",
            "metadata": {}
        }


def send_to_deck_builder(slides: list) -> str:
    """
    Send generated slides to Railway deck builder.

    Args:
        slides: List of slide dictionaries

    Returns:
        URL of generated presentation
    """
    print(f"\n{'='*60}")
    print(f"Sending {len(slides)} slides to deck builder...")
    print(f"{'='*60}")

    # Build deck builder request
    presentation_data = {
        "title": "Text Service + Deck Builder Integration Test",
        "slides": slides
    }

    # Call deck builder API
    response = requests.post(
        f"{DECK_BUILDER_URL}/api/presentations",
        json=presentation_data,
        timeout=30
    )

    if response.status_code == 200:
        result = response.json()
        url = result.get("url", "")
        print(f"\n✅ Deck built successfully!")
        print(f"  URL: {url}")
        return url
    else:
        print(f"\n❌ Deck builder failed: {response.status_code}")
        print(f"  Error: {response.text}")
        return ""


def main():
    """Run focused text service + deck builder integration test."""

    print("="*60)
    print("TEXT SERVICE + DECK BUILDER INTEGRATION TEST")
    print("="*60)
    print(f"Text Service: {TEXT_SERVICE_URL}")
    print(f"Deck Builder: {DECK_BUILDER_URL}")
    print(f"\nTesting new constraint limits:")
    print(f"  L25 rich_content: 1250 chars (~250 words)")
    print(f"  L29 hero_content: 500 chars (~100 words)")

    # Test Slide 1: L29 Hero (Title slide)
    print("\n" + "="*60)
    print("TEST 1: L29 HERO SLIDE (Title)")
    print("="*60)

    hero_result = generate_text_content(
        slide_number=1,
        layout="L29",
        title="Transforming Healthcare Through AI",
        narrative="Revolutionary AI technology reducing diagnostic time by 73% while improving accuracy to 99.2%",
        key_points=[]
    )

    # Test Slide 2: L25 Content (with rich content)
    print("\n" + "="*60)
    print("TEST 2: L25 CONTENT SLIDE (Rich Content)")
    print("="*60)

    content_result = generate_text_content(
        slide_number=2,
        layout="L25",
        title="Market Performance Overview",
        narrative="Q3 delivered exceptional results across all key performance indicators, driven by strategic expansion into emerging markets and operational efficiency gains.",
        key_points=[
            "Total revenue: $127M, up +32% YoY",
            "Recurring revenue: $89M (70% of total)",
            "New customer acquisitions: 2,400 accounts",
            "EBITDA margin improved to 32.3% from 28.1%",
            "Customer retention: 94%"
        ]
    )

    # Test Slide 3: Another L25 Content
    print("\n" + "="*60)
    print("TEST 3: L25 CONTENT SLIDE (Detailed Analysis)")
    print("="*60)

    analysis_result = generate_text_content(
        slide_number=3,
        layout="L25",
        title="Product Innovation Pipeline",
        narrative="Our product development strategy focuses on three core areas: AI-powered diagnostics, patient engagement platforms, and provider workflow optimization. Each area represents significant market opportunity with clear competitive advantages.",
        key_points=[
            "AI Diagnostics: 5 models in clinical trials, 2 FDA submissions pending",
            "Patient Engagement: Mobile app with 150K+ downloads, 4.8 rating",
            "Provider Tools: Integration with 80% of major EHR systems",
            "R&D Investment: $12M annually, 45 person engineering team"
        ]
    )

    # Test Slide 4: L29 Closing
    print("\n" + "="*60)
    print("TEST 4: L29 HERO SLIDE (Closing)")
    print("="*60)

    closing_result = generate_text_content(
        slide_number=4,
        layout="L29",
        title="Join Us in Transforming Healthcare",
        narrative="Together we can make quality healthcare accessible to everyone, everywhere",
        key_points=[]
    )

    # Build slides array for deck builder
    slides = []

    # Slide 1: L29 Hero
    if hero_result["success"]:
        slides.append({
            "layout": "L29",
            "content": {
                "hero_content": hero_result["content"]
            }
        })

    # Slide 2: L25 Content
    if content_result["success"]:
        slides.append({
            "layout": "L25",
            "content": {
                "slide_title": "Market Performance Overview",
                "subtitle": "Q3 2024 Results",
                "rich_content": content_result["content"]
            }
        })

    # Slide 3: L25 Content
    if analysis_result["success"]:
        slides.append({
            "layout": "L25",
            "content": {
                "slide_title": "Product Innovation Pipeline",
                "subtitle": "Strategic Development Areas",
                "rich_content": analysis_result["content"]
            }
        })

    # Slide 4: L29 Closing
    if closing_result["success"]:
        slides.append({
            "layout": "L29",
            "content": {
                "hero_content": closing_result["content"]
            }
        })

    # Send to deck builder
    presentation_url = send_to_deck_builder(slides)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Slides generated: {len(slides)}/4")
    print(f"\nPresentation URL:")
    print(f"  {presentation_url}")
    print("\n📊 Review the presentation to verify:")
    print("  ✓ Content fills the space appropriately")
    print("  ✓ Rich HTML formatting (h3, h4, lists, metrics)")
    print("  ✓ Visual variety (not sparse/bland)")
    print("  ✓ Professional appearance")
    print("="*60)


if __name__ == "__main__":
    main()

"""
Quick single-slide test to verify text service prompt fixes.
"""

import requests
import json

TEXT_SERVICE_URL = "http://localhost:8002"

# Test L25 with metrics to trigger 3-card-grid pattern
request_payload = {
    "presentation_id": "test_quick",
    "slide_id": "slide_test",
    "slide_number": 2,
    "topics": [
        "Total revenue: $127M, up +32% YoY",
        "Recurring revenue: $89M (70% of total)",
        "New customer acquisitions: 2,400 accounts"
    ],
    "narrative": "Q3 delivered exceptional results across all key performance indicators",
    "context": {
        "presentation_theme": "Testing prompt fixes",
        "target_audience": "Business executives",
        "previous_slides": []
    },
    "constraints": {
        "max_characters": 1250,
        "tone": "professional",
        "format": "bullet_points"
    },
    # v3.3: Explicit layout metadata
    "layout_id": "L25",
    "slide_purpose": None,  # Only for L29
    "suggested_pattern": "3-card-metrics-grid"
}

print("=" * 60)
print("SINGLE SLIDE TEST - Verify Prompt Fixes")
print("=" * 60)
print("\nSending request to text service...")
print(f"  Max chars: {request_payload['constraints']['max_characters']}")
print(f"  Topics: {len(request_payload['topics'])} metrics")

response = requests.post(
    f"{TEXT_SERVICE_URL}/api/v1/generate/text",
    json=request_payload,
    timeout=120  # Increased timeout for gemini-2.5-pro
)

if response.status_code == 200:
    result = response.json()
    content = result.get("content", "")
    word_count = result.get("metadata", {}).get("word_count", 0)

    print(f"\n✅ Content generated successfully!")
    print(f"  Characters: {len(content)}")
    print(f"  Words: {word_count}")

    print(f"\n📝 Generated HTML:")
    print("=" * 60)
    print(content)
    print("=" * 60)

    # Check for critical issues
    issues = []
    if "<h1" in content or "<h2" in content:
        issues.append("❌ DEFECT: Contains h1/h2 heading (should not duplicate slide title)")
    if "background:#" in content.replace(" ", "") or "background: #" in content or "background:rgb" in content:
        first_div = content[:content.find(">") + 1] if ">" in content else content
        if "background" in first_div and ("dark" in first_div.lower() or "gray" in first_div.lower() or "#1" in first_div or "#2" in first_div or "#3" in first_div):
            issues.append("❌ DEFECT: Main wrapper has dark/gray background (should be white/transparent)")

    if issues:
        print(f"\n⚠️ ISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
    else:
        print(f"\n✅ No critical defects detected!")

else:
    print(f"\n❌ Failed: {response.status_code}")
    print(f"  Error: {response.text}")

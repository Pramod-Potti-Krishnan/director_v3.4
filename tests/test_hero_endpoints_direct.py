"""
Test Hero Slide Endpoints Directly

Tests the new /v1.2/hero/* endpoints against Railway deployment.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Text Service v1.2 URL (Railway)
TEXT_SERVICE_URL = "https://web-production-5daf.up.railway.app"


async def test_hero_health():
    """Test hero endpoints health check."""
    print("\n" + "="*80)
    print("Testing Hero Endpoints Health Check")
    print("="*80)

    url = f"{TEXT_SERVICE_URL}/v1.2/hero/health"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            result = response.json()

            print(f"✅ Hero health check successful!")
            print(f"Status: {result.get('status')}")
            print(f"Service: {result.get('service')}")
            print(f"Endpoints: {json.dumps(result.get('endpoints'), indent=2)}")
            return True

    except Exception as e:
        print(f"❌ Hero health check failed: {e}")
        return False


async def test_title_slide():
    """Test title slide generation."""
    print("\n" + "="*80)
    print("Testing Title Slide Endpoint")
    print("="*80)

    url = f"{TEXT_SERVICE_URL}/v1.2/hero/title"

    payload = {
        "slide_number": 1,
        "slide_type": "title_slide",
        "narrative": "AI in Healthcare: Transforming Diagnostics and Patient Outcomes",
        "topics": ["Diagnostic AI", "Treatment Optimization", "Patient Care"],
        "context": {
            "theme": "professional",
            "audience": "healthcare executives",
            "presentation_title": "AI Healthcare Revolution 2025"
        }
    }

    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))

    try:
        start = datetime.utcnow()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Title slide generated successfully! ({duration:.2f}s)")
        print(f"\nGenerated HTML:")
        print(result.get('content', '')[:500] + "...")
        print(f"\nMetadata: {json.dumps(result.get('metadata'), indent=2)}")
        return True

    except Exception as e:
        print(f"❌ Title slide generation failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False


async def test_section_divider():
    """Test section divider generation."""
    print("\n" + "="*80)
    print("Testing Section Divider Endpoint")
    print("="*80)

    url = f"{TEXT_SERVICE_URL}/v1.2/hero/section"

    payload = {
        "slide_number": 2,
        "slide_type": "section_divider",
        "narrative": "Deep dive into AI-powered diagnostic technologies",
        "topics": ["Medical Imaging", "Early Detection", "Accuracy Improvements"],
        "context": {
            "theme": "professional",
            "audience": "healthcare executives"
        }
    }

    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))

    try:
        start = datetime.utcnow()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Section divider generated successfully! ({duration:.2f}s)")
        print(f"\nGenerated HTML:")
        print(result.get('content', '')[:500] + "...")
        print(f"\nMetadata: {json.dumps(result.get('metadata'), indent=2)}")
        return True

    except Exception as e:
        print(f"❌ Section divider generation failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False


async def test_closing_slide():
    """Test closing slide generation."""
    print("\n" + "="*80)
    print("Testing Closing Slide Endpoint")
    print("="*80)

    url = f"{TEXT_SERVICE_URL}/v1.2/hero/closing"

    payload = {
        "slide_number": 3,
        "slide_type": "closing_slide",
        "narrative": "Join us in transforming healthcare through AI innovation",
        "topics": ["Future of Healthcare", "AI Partnership", "Next Steps"],
        "context": {
            "theme": "professional",
            "audience": "healthcare executives",
            "contact_info": "dr.sarah.chen@medtechinnovations.com | www.medtechinnovations.com"
        }
    }

    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))

    try:
        start = datetime.utcnow()
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
        duration = (datetime.utcnow() - start).total_seconds()

        print(f"\n✅ Closing slide generated successfully! ({duration:.2f}s)")
        print(f"\nGenerated HTML:")
        print(result.get('content', '')[:500] + "...")
        print(f"\nMetadata: {json.dumps(result.get('metadata'), indent=2)}")
        return True

    except Exception as e:
        print(f"❌ Closing slide generation failed: {e}")
        if hasattr(e, 'response'):
            print(f"Response: {e.response.text}")
        return False


async def main():
    """Run all hero endpoint tests."""
    print("\n" + "="*80)
    print("HERO SLIDE ENDPOINTS TEST SUITE")
    print("="*80)
    print(f"Testing against: {TEXT_SERVICE_URL}")
    print("="*80)

    results = {
        "health": await test_hero_health(),
        "title": await test_title_slide(),
        "section": await test_section_divider(),
        "closing": await test_closing_slide()
    }

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.ljust(20)}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Hero endpoints are working correctly!")
    else:
        print(f"\n⚠️  {total - passed} tests failed. Check logs above for details.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

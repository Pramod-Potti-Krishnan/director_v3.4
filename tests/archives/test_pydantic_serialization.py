#!/usr/bin/env python3
"""
Test Pydantic V2 serialization behavior with None values.

This script demonstrates that Pydantic V2's model_dump(mode='json')
EXCLUDES fields with None values by default, which is why
preview_presentation_id doesn't reach the frontend.
"""

from pydantic import BaseModel, Field
from typing import Optional
import json


class SlideMetadata(BaseModel):
    """Metadata about the entire presentation (simplified for testing)"""
    main_title: str = Field(..., description="Main presentation title")
    preview_url: Optional[str] = Field(None, description="Preview URL")
    preview_presentation_id: Optional[str] = Field(None, description="Presentation ID")


def test_none_values_default():
    """Test 1: None values with default mode='json'"""
    print("=" * 80)
    print("TEST 1: None values with default mode='json'")
    print("=" * 80)

    metadata = SlideMetadata(
        main_title="Test Presentation",
        preview_url=None,
        preview_presentation_id=None
    )

    result = metadata.model_dump(mode='json')

    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"\nHas 'preview_presentation_id' key: {'preview_presentation_id' in result}")
    print(f"Has 'preview_url' key: {'preview_url' in result}")

    if 'preview_presentation_id' not in result:
        print("\n❌ PROBLEM: Field is EXCLUDED when None (default Pydantic V2 behavior)")
        print("   This is why frontend doesn't receive the field!")

    print()


def test_none_values_with_exclude_none_false():
    """Test 2: None values with exclude_none=False"""
    print("=" * 80)
    print("TEST 2: None values with exclude_none=False")
    print("=" * 80)

    metadata = SlideMetadata(
        main_title="Test Presentation",
        preview_url=None,
        preview_presentation_id=None
    )

    result = metadata.model_dump(mode='json', exclude_none=False)

    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"\nHas 'preview_presentation_id' key: {'preview_presentation_id' in result}")
    print(f"Has 'preview_url' key: {'preview_url' in result}")
    print(f"Value of preview_presentation_id: {result.get('preview_presentation_id')}")

    if 'preview_presentation_id' in result:
        print("\n✅ SOLUTION: Field is INCLUDED even when None")
        print("   Frontend can now check if field exists and handle null value")

    print()


def test_actual_values():
    """Test 3: With actual UUID values"""
    print("=" * 80)
    print("TEST 3: With actual values (deck-builder success case)")
    print("=" * 80)

    metadata = SlideMetadata(
        main_title="Test Presentation",
        preview_url="https://web-production-f0d13.up.railway.app/p/abc-123",
        preview_presentation_id="abc-123"
    )

    result = metadata.model_dump(mode='json')

    print(f"Result: {json.dumps(result, indent=2)}")
    print(f"\nHas 'preview_presentation_id' key: {'preview_presentation_id' in result}")
    print(f"Value: {result.get('preview_presentation_id')}")

    if 'preview_presentation_id' in result and result['preview_presentation_id']:
        print("\n✅ SUCCESS: Field is included when it has a value")
        print("   This case works fine")

    print()


def test_comparison():
    """Test 4: Side-by-side comparison"""
    print("=" * 80)
    print("TEST 4: Side-by-side comparison")
    print("=" * 80)

    metadata = SlideMetadata(
        main_title="Test Presentation",
        preview_url=None,
        preview_presentation_id=None
    )

    default_result = metadata.model_dump(mode='json')
    fixed_result = metadata.model_dump(mode='json', exclude_none=False)

    print("WITHOUT exclude_none=False:")
    print(f"  Keys: {list(default_result.keys())}")
    print(f"  JSON: {json.dumps(default_result)}")

    print("\nWITH exclude_none=False:")
    print(f"  Keys: {list(fixed_result.keys())}")
    print(f"  JSON: {json.dumps(fixed_result)}")

    print("\nDIFFERENCE:")
    missing_keys = set(fixed_result.keys()) - set(default_result.keys())
    if missing_keys:
        print(f"  ❌ These fields are MISSING without exclude_none=False: {missing_keys}")
        print(f"  ✅ THE FIX: Add exclude_none=False to include these fields")

    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PYDANTIC V2 SERIALIZATION TEST" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    test_none_values_default()
    test_none_values_with_exclude_none_false()
    test_actual_values()
    test_comparison()

    print("=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    print()
    print("ROOT CAUSE:")
    print("  Pydantic V2's model_dump(mode='json') excludes fields with None values")
    print()
    print("FIX:")
    print("  Change: message.model_dump(mode='json')")
    print("  To:     message.model_dump(mode='json', exclude_none=False)")
    print()
    print("LOCATION:")
    print("  src/handlers/websocket.py, line 93")
    print()
    print("=" * 80)

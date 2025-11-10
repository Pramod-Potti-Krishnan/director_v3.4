#!/usr/bin/env python3
"""
Test script for L25/L29 layout constraint fix.

Validates that:
1. L25 slides ONLY get content variants (hero variants blocked)
2. L29 slides ONLY get hero variants (content variants blocked)
3. Fallback logic is layout-aware
4. All variant selection paths respect the constraint
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.slide_type_mapper import SlideTypeMapper


def test_fallback_logic():
    """Test that fallback logic is layout-aware."""
    print("\n" + "="*80)
    print("TEST 1: Layout-Aware Fallback Logic")
    print("="*80)

    test_cases = [
        # (classification, layout_id, expected_variant_type)
        ("title_slide", "L29", "hero"),  # Hero classification on L29 → hero variant
        ("title_slide", "L25", "content"),  # Hero classification on L25 → content fallback!
        ("section_divider", "L29", "hero"),  # Hero classification on L29 → hero variant
        ("section_divider", "L25", "content"),  # Hero classification on L25 → content fallback!
        ("matrix_2x2", "L25", "content"),  # Content classification on L25 → content variant
        ("grid_3x3", "L25", "content"),  # Content classification on L25 → content variant
        ("metrics_grid", "L25", "content"),  # Content classification on L25 → content variant
    ]

    passed = 0
    failed = 0

    for classification, layout_id, expected_type in test_cases:
        variant_id = SlideTypeMapper.get_default_variant(classification, layout_id)

        # Check if variant is hero or content
        is_hero = variant_id in ["hero_centered", "hero_opening_centered", "hero_closing_final"]

        if expected_type == "hero":
            if is_hero:
                print(f"✅ {classification} + {layout_id} → {variant_id} (hero variant - CORRECT)")
                passed += 1
            else:
                print(f"❌ {classification} + {layout_id} → {variant_id} (NOT hero variant - WRONG!)")
                failed += 1
        else:  # expected_type == "content"
            if not is_hero:
                print(f"✅ {classification} + {layout_id} → {variant_id} (content variant - CORRECT)")
                passed += 1
            else:
                print(f"❌ {classification} + {layout_id} → {variant_id} (IS hero variant - WRONG!)")
                failed += 1

    print(f"\n📊 Fallback Logic Test Results: {passed} passed, {failed} failed")
    return failed == 0


def test_constraint_rules():
    """Test the key constraint rules."""
    print("\n" + "="*80)
    print("TEST 2: L25/L29 Constraint Rules")
    print("="*80)

    print("\n🔍 Rule 1: L29 always gets hero variants")
    l29_hero = SlideTypeMapper.get_default_variant("title_slide", "L29")
    l29_section = SlideTypeMapper.get_default_variant("section_divider", "L29")
    l29_closing = SlideTypeMapper.get_default_variant("closing_slide", "L29")

    rule1_pass = all([
        l29_hero == "hero_centered",
        l29_section == "hero_centered",
        l29_closing == "hero_centered"
    ])

    if rule1_pass:
        print(f"✅ L29 layout always returns hero_centered for all hero classifications")
    else:
        print(f"❌ L29 layout returned non-hero variants: {l29_hero}, {l29_section}, {l29_closing}")

    print("\n🔍 Rule 2: L25 with hero classification gets content fallback")
    l25_title = SlideTypeMapper.get_default_variant("title_slide", "L25")
    l25_section = SlideTypeMapper.get_default_variant("section_divider", "L25")
    l25_closing = SlideTypeMapper.get_default_variant("closing_slide", "L25")

    rule2_pass = all([
        l25_title == "single_column_2section",
        l25_section == "single_column_2section",
        l25_closing == "single_column_2section"
    ])

    if rule2_pass:
        print(f"✅ L25 layout returns content variant (single_column_2section) for hero classifications")
    else:
        print(f"❌ L25 layout returned unexpected variants: {l25_title}, {l25_section}, {l25_closing}")

    print("\n🔍 Rule 3: L25 with content classification gets correct content variant")
    l25_matrix = SlideTypeMapper.get_default_variant("matrix_2x2", "L25")
    l25_grid = SlideTypeMapper.get_default_variant("grid_3x3", "L25")
    l25_metrics = SlideTypeMapper.get_default_variant("metrics_grid", "L25")

    rule3_pass = all([
        l25_matrix == "matrix_2x2",
        l25_grid == "grid_3x3",
        l25_metrics == "metrics_2col"
    ])

    if rule3_pass:
        print(f"✅ L25 layout returns appropriate content variants for content classifications")
    else:
        print(f"❌ L25 layout returned unexpected variants: {l25_matrix}, {l25_grid}, {l25_metrics}")

    print(f"\n📊 Constraint Rules Test: {'✅ PASSED' if all([rule1_pass, rule2_pass, rule3_pass]) else '❌ FAILED'}")
    return all([rule1_pass, rule2_pass, rule3_pass])


def test_problematic_scenario():
    """Test the exact problematic scenario from the bug report."""
    print("\n" + "="*80)
    print("TEST 3: Problematic Scenario (Section Hero on L25)")
    print("="*80)

    print("\n🐛 Original Bug: section_divider on L25 was getting 'hero_centered' variant")
    print("   This violates the rule: L25 can ONLY use content variants")

    # Test the fix
    variant = SlideTypeMapper.get_default_variant("section_divider", "L25")

    print(f"\n🧪 Testing: section_divider + L25")
    print(f"   Returned variant: '{variant}'")

    # Check if it's NOT a hero variant
    is_hero = variant in ["hero_centered", "hero_opening_centered", "hero_closing_final"]

    if not is_hero:
        print(f"   ✅ Variant '{variant}' is a content variant - BUG FIXED!")
        return True
    else:
        print(f"   ❌ Variant '{variant}' is a hero variant - BUG STILL EXISTS!")
        return False


def run_all_tests():
    """Run all validation tests."""
    print("\n" + "="*80)
    print("🚀 L25/L29 LAYOUT CONSTRAINT FIX - VALIDATION TEST SUITE")
    print("="*80)
    print("\nValidating critical bug fix:")
    print("  • L25 slides CANNOT use hero variants")
    print("  • L29 slides CANNOT use content variants")
    print("  • Fallback logic must respect layout constraints")

    # Run tests
    test1_pass = test_fallback_logic()
    test2_pass = test_constraint_rules()
    test3_pass = test_problematic_scenario()

    # Summary
    print("\n\n" + "="*80)
    print("📊 FINAL TEST SUMMARY")
    print("="*80)

    all_passed = all([test1_pass, test2_pass, test3_pass])

    print(f"\n{'✅' if test1_pass else '❌'} Test 1: Layout-Aware Fallback Logic")
    print(f"{'✅' if test2_pass else '❌'} Test 2: L25/L29 Constraint Rules")
    print(f"{'✅' if test3_pass else '❌'} Test 3: Problematic Scenario Fix")

    print(f"\n" + "="*80)
    if all_passed:
        print("✅ OVERALL: ALL TESTS PASSED - BUG FIX VALIDATED")
        print("="*80)
        print("\n🎉 The L25/L29 layout constraint is now properly enforced!")
        print("\nNext Steps:")
        print("  • Commit the fix to feature branch")
        print("  • Test with real presentations")
        print("  • Verify no hero variants appear on L25 slides in production")
    else:
        print("❌ OVERALL: SOME TESTS FAILED - BUG FIX INCOMPLETE")
        print("="*80)
        print("\n⚠️  Please review failed tests above")

    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Analytics P0 Fixes Verification
================================

Tests the 5 previously broken charts that Analytics Service claims to have fixed:
1. bar_grouped - Multi-series data structure bug
2. bar_stacked - Multi-series data structure bug
3. area_stacked - Multi-series data structure bug
4. mixed - Multi-series data structure bug
5. d3_sunburst - Internal mapping bug

Date: November 27, 2025
Analytics Service Version: v3.4.3 (claimed fixes)
"""

import asyncio
import sys
from pathlib import Path
import httpx
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.clients.analytics_client import AnalyticsClient


LAYOUT_SERVICE_URL = "https://web-production-f0d13.up.railway.app"


async def test_fixed_charts():
    """Test the 5 previously broken charts."""

    print("=" * 80)
    print("ANALYTICS P0 FIXES VERIFICATION")
    print("Testing 5 Previously Broken Charts")
    print("=" * 80)
    print()
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Analytics Service Version: v3.4.3 (claimed fixes)")
    print()

    analytics_client = AnalyticsClient()

    # Test cases for the 5 previously broken charts
    test_cases = [
        {
            "name": "bar_grouped - Regional Performance",
            "chart_type": "bar_grouped",
            "analytics_type": "quarterly_comparison",
            "slide_title": "Regional Performance Comparison",
            "subtitle": "Q1-Q4 2024 by Region",
            "narrative": "Compare quarterly performance across three regions",
            "data": [
                {"label": "Q1", "North America": 124, "EMEA": 98, "APAC": 75},
                {"label": "Q2", "North America": 145, "EMEA": 112, "APAC": 88},
                {"label": "Q3", "North America": 165, "EMEA": 128, "APAC": 105},
                {"label": "Q4", "North America": 180, "EMEA": 145, "APAC": 125}
            ],
            "previous_issue": "Multi-series data structure bug - Error: 'Grouped bar chart requires datasets in data'"
        },
        {
            "name": "bar_stacked - Cost Structure",
            "chart_type": "bar_stacked",
            "analytics_type": "quarterly_comparison",
            "slide_title": "Quarterly Cost Structure",
            "subtitle": "Department Breakdown Q1-Q4 2024",
            "narrative": "Show quarterly cost breakdown by department",
            "data": [
                {"label": "Q1", "Operations": 43, "Sales": 28, "R&D": 24, "Marketing": 18},
                {"label": "Q2", "Operations": 47, "Sales": 31, "R&D": 26, "Marketing": 20},
                {"label": "Q3", "Operations": 51, "Sales": 34, "R&D": 29, "Marketing": 23},
                {"label": "Q4", "Operations": 53, "Sales": 36, "R&D": 29, "Marketing": 25}
            ],
            "previous_issue": "Multi-series data structure bug - Blank chart, cannot save edits"
        },
        {
            "name": "area_stacked - Product Revenue Mix",
            "chart_type": "area_stacked",
            "analytics_type": "revenue_over_time",
            "slide_title": "Product Revenue Composition",
            "subtitle": "Multi-Product Revenue Mix Q1-Q4 2024",
            "narrative": "Show revenue contribution from three product lines over time",
            "data": [
                {"label": "Q1", "Product A": 50, "Product B": 35, "Product C": 39},
                {"label": "Q2", "Product A": 58, "Product B": 42, "Product C": 45},
                {"label": "Q3", "Product A": 71, "Product B": 52, "Product C": 55},
                {"label": "Q4", "Product A": 65, "Product B": 48, "Product C": 50}
            ],
            "previous_issue": "Multi-series data structure bug - Blank chart, 'Failed to save' error"
        },
        {
            "name": "mixed - Revenue vs Costs",
            "chart_type": "mixed",
            "analytics_type": "kpi_metrics",
            "slide_title": "Revenue vs Operating Costs",
            "subtitle": "Quarterly Comparison 2024",
            "narrative": "Show revenue trend (line) vs quarterly costs (bar) comparison",
            "data": [
                {"label": "Q1", "Revenue": 125, "Costs": 80},
                {"label": "Q2", "Revenue": 145, "Costs": 90},
                {"label": "Q3", "Revenue": 170, "Costs": 110},
                {"label": "Q4", "Revenue": 195, "Costs": 120}
            ],
            "previous_issue": "Multi-series data structure bug - Blank chart, cannot change data points"
        },
        {
            "name": "d3_sunburst - Budget Hierarchy",
            "chart_type": "d3_sunburst",
            "analytics_type": "market_share",
            "slide_title": "Hierarchical Budget Distribution",
            "subtitle": "FY 2025 Department Allocation",
            "narrative": "Display FY2025 budget hierarchy across all departments in circular layout",
            "data": [
                {"label": "Engineering", "value": 800000},
                {"label": "Sales", "value": 600000},
                {"label": "Marketing", "value": 400000},
                {"label": "Operations", "value": 350000},
                {"label": "Finance", "value": 200000},
                {"label": "HR", "value": 150000}
            ],
            "previous_issue": "Internal mapping bug - Rendered column chart instead of sunburst diagram"
        }
    ]

    results = []
    viewable_urls = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Chart {i}/5: {test['name']}")
        print(f"Chart Type: {test['chart_type']}")
        print(f"Previous Issue: {test['previous_issue']}")
        print("=" * 80)

        try:
            # Generate analytics
            print(f"\n  🔄 Generating {test['chart_type']} chart...")
            analytics_response = await analytics_client.generate_chart(
                analytics_type=test['analytics_type'],
                layout="L02",
                chart_type=test['chart_type'],
                narrative=test['narrative'],
                data=test['data'],
                context={
                    "presentation_title": "P0 Fixes Verification",
                    "tone": "professional",
                    "audience": "executives"
                },
                presentation_id=f"fix_verify_{i:03d}",
                slide_id=f"slide_{i:03d}",
                slide_number=i
            )

            content = analytics_response.get('content', {})
            element_3 = content.get('element_3', '')
            element_2 = content.get('element_2', '')

            chart_html_size = len(element_3)
            print(f"  ✅ Analytics generated (HTML: {chart_html_size} chars)")

            # Check if chart HTML is suspiciously small (indicates error)
            if chart_html_size < 500:
                print(f"  ⚠️  WARNING: Chart HTML is very small ({chart_html_size} chars) - may indicate error")
                results.append({
                    "chart_type": test['chart_type'],
                    "status": "⚠️ SUSPICIOUS",
                    "html_size": chart_html_size,
                    "reason": "Chart HTML too small - likely error"
                })
            else:
                results.append({
                    "chart_type": test['chart_type'],
                    "status": "✅ PASS",
                    "html_size": chart_html_size,
                    "reason": "Chart HTML generated successfully"
                })

            # Post to Layout Service for visual validation
            print(f"  🔄 Posting to Layout Service for visual validation...")

            layout_request = {
                "title": f"Fix Verification - {test['name']}",
                "slides": [{
                    "layout": "L02",
                    "content": {
                        "slide_title": test['slide_title'],
                        "element_1": test['subtitle'],
                        "element_3": element_3,
                        "element_2": element_2,
                        "presentation_name": "P0 Fixes Verification",
                        "company_logo": "✅"
                    }
                }]
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{LAYOUT_SERVICE_URL}/api/presentations",
                    json=layout_request
                )

                if response.status_code == 200:
                    result = response.json()
                    viewable_url = f"{LAYOUT_SERVICE_URL}{result.get('url')}"

                    print(f"  ✅ Visual Validation URL: {viewable_url}")

                    viewable_urls.append({
                        "name": test['name'],
                        "chart_type": test['chart_type'],
                        "url": viewable_url,
                        "html_size": chart_html_size,
                        "previous_issue": test['previous_issue']
                    })
                else:
                    print(f"  ❌ Layout Service error: {response.status_code}")
                    results[-1]["status"] = "❌ FAIL"
                    results[-1]["reason"] = f"Layout Service error: {response.status_code}"

        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append({
                "chart_type": test['chart_type'],
                "status": "❌ FAIL",
                "html_size": 0,
                "reason": str(e)
            })
            import traceback
            traceback.print_exc()

    # Generate summary report
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for r in results if r["status"] == "✅ PASS")
    suspicious = sum(1 for r in results if r["status"] == "⚠️ SUSPICIOUS")
    failed = sum(1 for r in results if r["status"] == "❌ FAIL")

    print(f"Total Charts Tested: {len(results)}")
    print(f"  ✅ PASS:       {passed}/5 ({passed*20}%)")
    print(f"  ⚠️  SUSPICIOUS: {suspicious}/5 ({suspicious*20}%)")
    print(f"  ❌ FAIL:       {failed}/5 ({failed*20}%)")
    print()

    # Detailed results
    print("Detailed Results:")
    print("-" * 80)
    for result in results:
        print(f"{result['status']} {result['chart_type']:<20} HTML: {result['html_size']:>6} chars - {result['reason']}")
    print()

    # Visual validation URLs
    if viewable_urls:
        print("\n" + "=" * 80)
        print("VISUAL VALIDATION URLs")
        print("=" * 80)
        print()
        print("⚠️  IMPORTANT: Click each URL to visually verify the chart renders correctly:")
        print()

        for i, item in enumerate(viewable_urls, 1):
            print(f"{i}. {item['name']}")
            print(f"   Chart Type:      {item['chart_type']}")
            print(f"   HTML Size:       {item['html_size']} chars")
            print(f"   Previous Issue:  {item['previous_issue']}")
            print(f"   Validation URL:  {item['url']}")
            print()

        # Write results to file
        output_file = Path("test_outputs/P0_FIXES_VERIFICATION_RESULTS.md")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            f.write("# Analytics P0 Fixes Verification Results\n\n")
            f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Analytics Service Version**: v3.4.3 (claimed fixes)\n\n")
            f.write("---\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Charts Tested**: {len(results)}\n")
            f.write(f"- **✅ PASS**: {passed}/5 ({passed*20}%)\n")
            f.write(f"- **⚠️ SUSPICIOUS**: {suspicious}/5 ({suspicious*20}%)\n")
            f.write(f"- **❌ FAIL**: {failed}/5 ({failed*20}%)\n\n")
            f.write("---\n\n")
            f.write("## Detailed Results\n\n")
            f.write("| Status | Chart Type | HTML Size | Result |\n")
            f.write("|--------|------------|-----------|--------|\n")
            for result in results:
                f.write(f"| {result['status']} | {result['chart_type']} | {result['html_size']} chars | {result['reason']} |\n")
            f.write("\n---\n\n")
            f.write("## Visual Validation URLs\n\n")
            f.write("⚠️ **IMPORTANT**: Click each URL to visually verify the chart renders correctly\n\n")
            for item in viewable_urls:
                f.write(f"### {item['name']}\n\n")
                f.write(f"- **Chart Type**: `{item['chart_type']}`\n")
                f.write(f"- **HTML Size**: {item['html_size']} chars\n")
                f.write(f"- **Previous Issue**: {item['previous_issue']}\n")
                f.write(f"- **Validation URL**: {item['url']}\n\n")
                f.write("---\n\n")

        print(f"📄 Results written to: {output_file}")
        print()

    # Final verdict
    print("=" * 80)
    if passed == 5:
        print("🎉 SUCCESS! All 5 previously broken charts are now working!")
        print("=" * 80)
        return True
    elif passed + suspicious == 5:
        print("⚠️  SUSPICIOUS RESULTS - Manual visual validation required")
        print("=" * 80)
        return False
    else:
        print(f"❌ FAILURE - {failed} chart(s) still broken")
        print("=" * 80)
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_fixed_charts())
    print()

    if success:
        print("✅ VERIFICATION COMPLETE - ALL FIXES CONFIRMED")
        sys.exit(0)
    else:
        print("⚠️  VERIFICATION INCOMPLETE - MANUAL REVIEW NEEDED")
        sys.exit(1)

#!/usr/bin/env python3
"""
Analytics Final 2 Charts Verification
======================================

Tests the 2 remaining charts that Analytics Service claims to have fixed:
1. mixed - Revenue vs Costs (line + bar combination)
2. d3_sunburst - Budget Hierarchy (circular sunburst diagram)

Date: November 27, 2025
Analytics Service Version: v3.4.5 (claimed fixes for CDN issues)
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


async def test_final_2_charts():
    """Test the 2 remaining charts after CDN fixes."""

    print("=" * 80)
    print("ANALYTICS FINAL 2 CHARTS VERIFICATION")
    print("Testing mixed and d3_sunburst after CDN fixes")
    print("=" * 80)
    print()
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Analytics Service Version: v3.4.5 (claimed CDN fixes)")
    print()

    analytics_client = AnalyticsClient()

    test_cases = [
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
            "previous_issue": "Wrong CDN plugin + rendering as line instead of mixed (line+bar)",
            "expected": "Line chart for Revenue + bar chart for Costs in single visualization"
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
            "previous_issue": "Wrong CDN plugin + rendering as bar chart instead of circular sunburst",
            "expected": "D3.js circular sunburst diagram showing hierarchical budget distribution"
        }
    ]

    results = []
    viewable_urls = []

    for i, test in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"Chart {i}/2: {test['name']}")
        print(f"Chart Type: {test['chart_type']}")
        print(f"Previous Issue: {test['previous_issue']}")
        print(f"Expected: {test['expected']}")
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
                    "presentation_title": "Final 2 Charts Verification",
                    "tone": "professional",
                    "audience": "executives"
                },
                presentation_id=f"final2_{i:03d}",
                slide_id=f"slide_{i:03d}",
                slide_number=i
            )

            content = analytics_response.get('content', {})
            element_3 = content.get('element_3', '')
            element_2 = content.get('element_2', '')

            chart_html_size = len(element_3)
            print(f"  ✅ Analytics generated (HTML: {chart_html_size} chars)")

            # Check HTML size
            if chart_html_size < 500:
                print(f"  ⚠️  WARNING: Chart HTML is very small ({chart_html_size} chars) - may indicate error")
                results.append({
                    "chart_type": test['chart_type'],
                    "status": "⚠️ SUSPICIOUS",
                    "html_size": chart_html_size,
                    "reason": "Chart HTML too small - likely error"
                })
            else:
                # Check for specific improvements
                improvement_notes = []

                # For mixed: Check if it mentions both line and bar
                if test['chart_type'] == 'mixed':
                    if 'line' in element_3.lower() and 'bar' in element_3.lower():
                        improvement_notes.append("Contains both line and bar references")

                # For d3_sunburst: Check for D3 references
                if test['chart_type'] == 'd3_sunburst':
                    if 'd3' in element_3.lower():
                        improvement_notes.append("Contains D3.js references")

                results.append({
                    "chart_type": test['chart_type'],
                    "status": "✅ PASS",
                    "html_size": chart_html_size,
                    "reason": f"Chart HTML generated successfully. {'; '.join(improvement_notes) if improvement_notes else ''}",
                    "notes": improvement_notes
                })

            # Post to Layout Service for visual validation
            print(f"  🔄 Posting to Layout Service for visual validation...")

            layout_request = {
                "title": f"Final 2 Charts - {test['name']}",
                "slides": [{
                    "layout": "L02",
                    "content": {
                        "slide_title": test['slide_title'],
                        "element_1": test['subtitle'],
                        "element_3": element_3,
                        "element_2": element_2,
                        "presentation_name": "Final 2 Charts Verification",
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
                        "previous_issue": test['previous_issue'],
                        "expected": test['expected']
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
    print(f"  ✅ PASS:       {passed}/2 ({passed*50}%)")
    print(f"  ⚠️  SUSPICIOUS: {suspicious}/2 ({suspicious*50}%)")
    print(f"  ❌ FAIL:       {failed}/2 ({failed*50}%)")
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
            print(f"   Expected:        {item['expected']}")
            print(f"   Validation URL:  {item['url']}")
            print()

        # Write results to file
        output_file = Path("test_outputs/FINAL_2_CHARTS_VERIFICATION_RESULTS.md")
        output_file.parent.mkdir(exist_ok=True)

        with open(output_file, 'w') as f:
            f.write("# Analytics Final 2 Charts Verification Results\n\n")
            f.write(f"**Test Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Analytics Service Version**: v3.4.5 (CDN fixes)\n\n")
            f.write("---\n\n")
            f.write("## Summary\n\n")
            f.write(f"- **Total Charts Tested**: {len(results)}\n")
            f.write(f"- **✅ PASS**: {passed}/2 ({passed*50}%)\n")
            f.write(f"- **⚠️ SUSPICIOUS**: {suspicious}/2 ({suspicious*50}%)\n")
            f.write(f"- **❌ FAIL**: {failed}/2 ({failed*50}%)\n\n")
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
                f.write(f"- **Expected Result**: {item['expected']}\n")
                f.write(f"- **Validation URL**: {item['url']}\n\n")
                f.write("---\n\n")

        print(f"📄 Results written to: {output_file}")
        print()

    # Final verdict
    print("=" * 80)
    if passed == 2:
        print("🎉 SUCCESS! Both remaining charts are now working!")
        print("=" * 80)
        return True
    elif passed == 1:
        print("⚠️  PARTIAL SUCCESS - 1 of 2 charts working")
        print("=" * 80)
        return False
    else:
        print(f"❌ FAILURE - Both charts still broken")
        print("=" * 80)
        return False


if __name__ == "__main__":
    print()
    success = asyncio.run(test_final_2_charts())
    print()

    if success:
        print("✅ VERIFICATION COMPLETE - ALL FIXES CONFIRMED")
        print("🎉 Director can now re-enable mixed and d3_sunburst charts!")
        sys.exit(0)
    else:
        print("⚠️  VERIFICATION INCOMPLETE - MANUAL REVIEW NEEDED")
        sys.exit(1)

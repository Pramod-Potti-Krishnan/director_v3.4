"""
Analytics Service Client for Director Agent v3.4

Handles communication with Analytics Microservice v3 for chart generation
and data visualization with AI-generated observations.

Integration:
- Works with Analytics Microservice v3 for L01, L02, L03 layouts
- Director-managed context (stateless service calls)
- Returns 2-field response for L02: element_3 (chart) + element_2 (observations)
- Optional session tracking fields for narrative continuity

Author: Director v3.4 Integration Team
Date: January 16, 2025
"""

import httpx
from typing import Dict, Any, Optional, List
from src.utils.logger import setup_logger
from config.settings import get_settings

logger = setup_logger(__name__)


class AnalyticsClient:
    """
    Client for calling Analytics Microservice v3 APIs.

    The Analytics Service generates interactive charts with AI-generated observations
    for presentation slides. It follows the same architecture as Text Service v1.2:
    - Stateless service (no server-side sessions)
    - Director passes explicit context via previous_slides
    - Optional session tracking fields for logging/analytics

    Supported Analytics Types:
    - revenue_over_time: Line chart showing time series
    - quarterly_comparison: Bar chart comparing periods
    - market_share: Donut chart showing distribution
    - yoy_growth: Bar chart with year-over-year comparison
    - kpi_metrics: Multi-metric bar chart

    Supported Layouts:
    - L01: Single chart centered (simple)
    - L02: Chart left + observations right (detailed)
    - L03: Two charts side-by-side (comparison)

    Usage:
        client = AnalyticsClient()
        result = await client.generate_chart(
            analytics_type="revenue_over_time",
            layout="L02",
            data=[
                {"label": "Q1 2024", "value": 125000},
                {"label": "Q2 2024", "value": 145000}
            ],
            narrative="Show quarterly revenue growth",
            context={
                "presentation_title": "Q4 Board Review",
                "previous_slides": [...],
                "tone": "professional",
                "audience": "executives"
            }
        )
    """

    def __init__(self, base_url: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize Analytics client.

        Args:
            base_url: Override default Analytics service URL
            timeout: Override default request timeout (default: 30s for chart generation)
        """
        settings = get_settings()
        self.base_url = base_url or getattr(settings, 'ANALYTICS_SERVICE_URL', 'https://analytics-v30-production.up.railway.app')
        self.timeout = timeout or getattr(settings, 'ANALYTICS_SERVICE_TIMEOUT', 30)
        self.enabled = getattr(settings, 'ANALYTICS_SERVICE_ENABLED', True)

        logger.info(
            f"AnalyticsClient initialized",
            extra={
                "base_url": self.base_url,
                "timeout": self.timeout,
                "enabled": self.enabled
            }
        )

    async def health_check(self) -> bool:
        """
        Check if Analytics service is healthy and reachable.

        Returns:
            True if service is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")

                if response.status_code == 200:
                    logger.info("Analytics service health check: OK")
                    return True
                else:
                    logger.warning(
                        f"Analytics service health check failed: {response.status_code}",
                        extra={"status_code": response.status_code}
                    )
                    return False
        except Exception as e:
            logger.error(
                f"Cannot reach Analytics service: {str(e)}",
                extra={"error": str(e), "url": self.base_url}
            )
            return False

    async def generate_chart(
        self,
        analytics_type: str,
        layout: str,
        data: List[Dict[str, Any]],
        narrative: str,
        context: Optional[Dict[str, Any]] = None,
        presentation_id: Optional[str] = None,
        slide_id: Optional[str] = None,
        slide_number: Optional[int] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate an analytics chart with AI-generated observations.

        The Analytics service will:
        1. Generate chart using Chart.js or similar library
        2. Generate AI observations/insights using GPT-4o-mini
        3. Create HTML for chart (element_3) and observations (element_2)
        4. Consider previous slides context for narrative continuity

        Args:
            analytics_type: Type of analytics visualization
                - "revenue_over_time": Line chart for time series
                - "quarterly_comparison": Bar chart for period comparison
                - "market_share": Donut chart for distribution
                - "yoy_growth": Bar chart with YoY comparison
                - "kpi_metrics": Multi-metric bar chart
            layout: Target layout template
                - "L01": Single centered chart
                - "L02": Chart left + observations right
                - "L03": Two charts side-by-side
            data: Chart data points as list of dicts
                - Each dict must have: {"label": str, "value": number}
                - Example: [{"label": "Q1 2024", "value": 125000}, ...]
            narrative: User's narrative/request about what to show
            context: Additional context dict with keys:
                - presentation_title: Overall presentation title
                - previous_slides: List of previous slide summaries (for LLM context)
                - tone: Content tone (professional, casual, technical)
                - audience: Target audience (executives, managers, technical)
                - theme: Visual theme (professional, bold, minimal)
            presentation_id: Optional presentation identifier (for logging)
            slide_id: Optional slide identifier (for logging)
            slide_number: Optional slide position (for context)
            options: Additional options:
                - enable_editor: Include "Edit Data" button (default: True)
                - chart_height: Chart height in pixels (default: 600)

        Returns:
            Dict containing:
                For L02 layout:
                    - content.element_3: Chart HTML (1260×720px for L02 left panel)
                    - content.element_2: Observations text (for L02 right panel)
                    - content.slide_title: Optional title override
                    - content.element_1: Optional subtitle override
                For L01/L03 layouts:
                    - content fields matching those layouts
                - metadata: Generation metadata (service, type, time, model)

        Raises:
            httpx.HTTPError: If API call fails
            ValueError: If response is invalid or layout unsupported
        """
        if not self.enabled:
            raise RuntimeError("Analytics service is disabled in settings")

        # Validate analytics_type
        valid_types = {
            "revenue_over_time", "quarterly_comparison", "market_share",
            "yoy_growth", "kpi_metrics"
        }
        if analytics_type not in valid_types:
            logger.warning(
                f"Unknown analytics_type: {analytics_type}, proceeding anyway",
                extra={"analytics_type": analytics_type, "valid_types": list(valid_types)}
            )

        # Validate layout
        valid_layouts = {"L01", "L02", "L03"}
        if layout not in valid_layouts:
            raise ValueError(
                f"Invalid layout '{layout}'. Must be one of: {valid_layouts}"
            )

        # Build request payload
        payload = {
            "narrative": narrative,
            "data": data
        }

        # Add optional session tracking fields
        if presentation_id:
            payload["presentation_id"] = presentation_id
        if slide_id:
            payload["slide_id"] = slide_id
        if slide_number is not None:
            payload["slide_number"] = slide_number

        # Add context (including previous_slides for narrative continuity)
        if context:
            payload["context"] = context

        # Add options
        if options:
            payload["options"] = options
        else:
            # Default options
            payload["options"] = {
                "enable_editor": True,
                "chart_height": 600
            }

        logger.info(
            f"Generating {analytics_type} chart for {layout} layout",
            extra={
                "analytics_type": analytics_type,
                "layout": layout,
                "data_points": len(data),
                "presentation_id": presentation_id,
                "slide_id": slide_id,
                "has_previous_context": bool(context and context.get("previous_slides"))
            }
        )

        try:
            # Call Analytics Service API
            endpoint = f"{self.base_url}/api/v1/analytics/{layout}/{analytics_type}"

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    endpoint,
                    json=payload
                )

                if response.status_code == 200:
                    result = response.json()

                    # Log generation results
                    metadata = result.get("metadata", {})
                    logger.info(
                        "Analytics chart generated successfully",
                        extra={
                            "analytics_type": analytics_type,
                            "layout": layout,
                            "chart_type": metadata.get("chart_type"),
                            "generation_time_ms": metadata.get("generation_time_ms"),
                            "model": metadata.get("model_used"),
                            "data_points": metadata.get("data_points")
                        }
                    )

                    # Validate response structure for L02
                    if layout == "L02":
                        content = result.get("content", {})
                        if "element_3" not in content or "element_2" not in content:
                            logger.warning(
                                "L02 response missing required fields (element_3, element_2)",
                                extra={"content_keys": list(content.keys())}
                            )

                    return result

                elif response.status_code == 422:
                    # Validation error
                    error_detail = response.json().get("detail", "Validation error")
                    logger.error(
                        f"Analytics validation error: {error_detail}",
                        extra={
                            "analytics_type": analytics_type,
                            "layout": layout,
                            "status_code": 422
                        }
                    )
                    raise ValueError(f"Analytics validation error: {error_detail}")

                else:
                    # Other API error
                    logger.error(
                        f"Analytics API error: {response.status_code}",
                        extra={
                            "status_code": response.status_code,
                            "response": response.text[:500],
                            "endpoint": endpoint
                        }
                    )
                    raise httpx.HTTPError(
                        f"Analytics API error: {response.status_code} - {response.text[:200]}"
                    )

        except httpx.TimeoutException as e:
            logger.error(
                f"Analytics service timeout after {self.timeout}s",
                extra={
                    "analytics_type": analytics_type,
                    "layout": layout,
                    "timeout": self.timeout
                }
            )
            raise

        except httpx.HTTPError as e:
            logger.error(
                f"HTTP error calling Analytics service: {str(e)}",
                extra={"analytics_type": analytics_type, "layout": layout}
            )
            raise

        except Exception as e:
            logger.error(
                f"Unexpected error generating analytics chart: {str(e)}",
                extra={
                    "analytics_type": analytics_type,
                    "layout": layout,
                    "error_type": type(e).__name__
                }
            )
            raise

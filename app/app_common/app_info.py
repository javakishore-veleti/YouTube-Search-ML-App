"""
app_info.py
===========
AppInfo registers the /info route and owns all static app metadata.
"""
from __future__ import annotations

from app.app_common.dtos.init_dtos import InitDTO


class AppInfo:
    """Owns the /info endpoint and all static application metadata."""

    APP_NAME    = "VidSage"
    VERSION     = "1.0.0"
    DESCRIPTION = (
        "A smart video discovery application powered by Machine Learning. "
        "It helps users search public video content using natural language queries, "
        "leveraging ML models to understand user intent and surface the most relevant "
        "results. Instead of relying solely on keyword matching, the app uses "
        "semantic understanding to deliver smarter, context-aware discovery results."
    )
    FEATURES = [
        "Natural language video discovery",
        "AI-powered semantic understanding of search queries",
        "Context-aware and intent-driven results",
        "RESTful API interface for easy integration",
    ]

    def info(self) -> dict:
        return {
            "name":        self.APP_NAME,
            "description": self.DESCRIPTION,
            "features":    self.FEATURES,
            "version":     self.VERSION,
        }

    def initialize(self, dto: InitDTO) -> None:
        """Register the /info route on the FastAPI app supplied via dto."""
        dto.app.add_api_route(
            "/info",
            endpoint=self.info,
            methods=["GET"],
        )


class Initializer:
    def initialize(self, dto: InitDTO) -> None:
        AppInfo().initialize(dto)

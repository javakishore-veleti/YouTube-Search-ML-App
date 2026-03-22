from app.app_common.dtos.init_dtos import InitDTO


class AppInfo:
    def info(self) -> dict:
        return {
            "name": "VidSage",
            "description": (
                "A smart video discovery application powered by Machine Learning. "
                "It helps users search public video content using natural language queries, "
                "leveraging ML models to understand user intent and surface the most relevant "
                "results. Instead of relying solely on keyword matching, the app uses "
                "semantic understanding to deliver smarter, context-aware discovery results."
            ),
            "features": [
                "Natural language video discovery",
                "AI-powered semantic understanding of search queries",
                "Context-aware and intent-driven results",
                "RESTful API interface for easy integration",
            ],
            "version": "1.0.0",
        }


def initialize(dto: InitDTO) -> None:
    handler = AppInfo()
    dto.app.add_api_route(
        "/info",
        endpoint=handler.info,
        methods=["GET"],
    )

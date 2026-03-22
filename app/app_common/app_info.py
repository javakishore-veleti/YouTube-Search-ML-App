from app.dtos.init_dtos import InitDTO


class AppInfo:
    def info(self) -> dict:
        return {
            "name": "YouTube Search ML App",
            "description": (
                "A smart YouTube search application powered by Machine Learning. "
                "It allows users to search for YouTube videos using natural language queries, "
                "leveraging ML models to understand user intent and surface the most relevant "
                "video content. Instead of relying solely on keyword matching, the app uses "
                "semantic understanding to deliver smarter, context-aware search results "
                "from YouTube."
            ),
            "features": [
                "Natural language YouTube video search",
                "ML-powered semantic understanding of search queries",
                "Context-aware and intent-driven search results",
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

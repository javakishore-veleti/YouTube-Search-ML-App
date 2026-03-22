from app.app_common.dtos.init_dtos import InitDTO


class HealthCheck:
    def health_check(self) -> dict:
        return {"health_check": "OK"}


def initialize(dto: InitDTO) -> None:
    handler = HealthCheck()
    dto.app.add_api_route(
        "/health_check",
        endpoint=handler.health_check,
        methods=["GET"],
    )

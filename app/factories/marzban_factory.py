from app.clients.marzban_client import MarzbanClient
from app.config.config import config
from app.services.marzban_service import MarzbanService


def create_marzban_service() -> MarzbanService:
    client = MarzbanClient(
        base_url=config.MARZBAN_URL,
    )

    return MarzbanService(
        client=client,
        username=config.MARZBAN_USERNAME,
        password=config.MARZBAN_PASSWORD,
    )
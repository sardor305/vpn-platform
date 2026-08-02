from app.clients.marzban_client import MarzbanClient


class MarzbanService:

    def __init__(
        self,
        client: MarzbanClient,
    ):
        self.client = client
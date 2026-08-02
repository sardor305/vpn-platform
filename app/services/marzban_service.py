from app.clients.marzban_client import MarzbanClient


class MarzbanService:

    def __init__(
        self,
        client: MarzbanClient,
        username: str,
        password: str,
    ):
        self.client = client
        self.username = username
        self.password = password

    async def login(self):

        return await self.client.login(
            username=self.username,
            password=self.password,
        )

    async def create_user(
        self,
        user_data: dict,
    ):

        await self.login()

        return await self.client.create_user(
            user_data=user_data,
        )
from httpx import HTTPStatusError

from app.clients.marzban_client import MarzbanClient
from app.schemas.marzban_user import MarzbanUser


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
    ) -> MarzbanUser:

        await self.login()

        username = user_data["username"]

        try:
            result = await self.client.create_user(
                user_data=user_data,
            )

        except HTTPStatusError as e:

            if e.response.status_code != 409:
                raise

            result = await self.client.get_user(
                username=username,
            )

            if result is None:
                raise RuntimeError(
                    "Marzban foydalanuvchini qaytara olmadi."
                )

        return MarzbanUser(
            username=result["username"],
            vpn_link=result["links"][0],
            subscription_url=result["subscription_url"],
        )

    async def create_vless_user(
        self,
        username: str,
        inbound_name: str = "VLESS TCP",
    ) -> MarzbanUser:

        user_data = {
            "username": username,
            "proxies": {
                "vless": {}
            },
            "inbounds": {
                "vless": [
                    inbound_name
                ]
            },
            "status": "active",
        }

        return await self.create_user(
            user_data=user_data,
        )
from datetime import datetime, timezone

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

    @staticmethod
    def _datetime_to_timestamp(
        value: datetime,
    ) -> int:

        if value.tzinfo is None:
            value = value.replace(
                tzinfo=timezone.utc
            )

        return int(value.timestamp())

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

            print(
                "\n========== CREATE USER RESPONSE =========="
            )
            print(result)

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

            print(
                "\n========== GET USER RESPONSE =========="
            )
            print(result)

        print(
            "\n========== DEBUG =========="
        )
        print(
            "USERNAME:",
            result.get("username"),
        )
        print(
            "LINKS:",
            result.get("links"),
        )
        print(
            "SUBSCRIPTION:",
            result.get("subscription_url"),
        )
        print(
            "EXPIRE:",
            result.get("expire"),
        )
        print(
            "========================================\n"
        )

        return MarzbanUser(
            username=result["username"],
            vpn_link=(
                result["links"][0]
                if result.get("links")
                else ""
            ),
            subscription_url=result[
                "subscription_url"
            ],
        )

    async def create_vless_user(
        self,
        username: str,
        expire: datetime,
        inbound_name: str = "VLESS TCP",
    ) -> MarzbanUser:

        expire_timestamp = (
            self._datetime_to_timestamp(
                expire
            )
        )

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
            "expire": expire_timestamp,
        }

        return await self.create_user(
            user_data=user_data,
        )

    async def get_user(
        self,
        username: str,
    ) -> dict | None:

        await self.login()

        return await self.client.get_user(
            username=username,
        )

    async def update_user_expire(
        self,
        username: str,
        expire: datetime,
    ):

        await self.login()

        expire_timestamp = (
            self._datetime_to_timestamp(
                expire
            )
        )

        return await self.client.modify_user(
            username=username,
            user_data={
                "expire": expire_timestamp,
            },
        )

    async def activate_user(
        self,
        username: str,
    ):

        await self.login()

        return await self.client.modify_user(
            username=username,
            user_data={
                "status": "active",
            },
        )

    async def deactivate_user(
        self,
        username: str,
    ):

        await self.login()

        return await self.client.modify_user(
            username=username,
            user_data={
                "status": "disabled",
            },
        )

    async def delete_user(
        self,
        username: str,
    ) -> bool:

        await self.login()

        return await self.client.delete_user(
            username=username,
        )
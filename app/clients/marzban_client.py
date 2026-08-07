import httpx


class MarzbanClient:

    def __init__(
        self,
        base_url: str,
    ):
        self.base_url = base_url.rstrip("/")

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30,
        )

        self.token: str | None = None

    async def login(
        self,
        username: str,
        password: str,
    ):

        response = await self.client.post(
            "/api/admin/token",
            data={
                "username": username,
                "password": password,
            },
        )

        response.raise_for_status()

        data = response.json()

        self.token = data["access_token"]

        return self.token

    async def get_user(
        self,
        username: str,
    ):

        if self.token is None:
            raise RuntimeError(
                "MarzbanClient is not authenticated. Call login() first."
            )

        response = await self.client.get(
            f"/api/user/{username}",
            headers={
                "Authorization": f"Bearer {self.token}",
            },
        )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

    async def create_user(
        self,
        user_data: dict,
    ):

        if self.token is None:
            raise RuntimeError(
                "MarzbanClient is not authenticated. Call login() first."
            )

        response = await self.client.post(
            "/api/user",
            json=user_data,
            headers={
                "Authorization": f"Bearer {self.token}",
            },
        )

        response.raise_for_status()

        return response.json()
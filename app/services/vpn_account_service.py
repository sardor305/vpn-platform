from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vpn_account import VPNAccount
from app.repositories.vpn_account_repository import VPNAccountRepository


class VPNAccountService:

    def __init__(self, session: AsyncSession):
        self.repository = VPNAccountRepository(session)

    async def create(
        self,
        subscription_id: int,
        marzban_username: str,
        protocol: str,
        subscription_url: str,
    ) -> VPNAccount:

        return await self.repository.create(
            subscription_id=subscription_id,
            marzban_username=marzban_username,
            protocol=protocol,
            subscription_url=subscription_url,
        )
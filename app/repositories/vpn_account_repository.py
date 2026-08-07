from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vpn_account import VPNAccount


class VPNAccountRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_subscription_and_protocol(
        self,
        subscription_id: int,
        protocol: str,
    ) -> VPNAccount | None:

        stmt = (
            select(VPNAccount)
            .where(
                VPNAccount.subscription_id == subscription_id,
                VPNAccount.protocol == protocol,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
        self,
        subscription_id: int,
        marzban_username: str,
        protocol: str,
        vpn_link: str,
        subscription_url: str,
    ) -> VPNAccount:

        vpn_account = VPNAccount(
            subscription_id=subscription_id,
            marzban_username=marzban_username,
            protocol=protocol,
            vpn_link=vpn_link,
            subscription_url=subscription_url,
            is_active=True,
        )

        self.session.add(vpn_account)

        await self.session.flush()
        await self.session.refresh(vpn_account)

        return vpn_account
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.vpn_account import VPNAccount


class VPNAccountRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_by_user_and_protocol(
        self,
        user_id: int,
        protocol: str,
    ) -> VPNAccount | None:

        stmt = (
            select(VPNAccount)
            .where(
                VPNAccount.user_id == user_id,
                VPNAccount.protocol == protocol,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: int,
        marzban_username: str,
        protocol: str,
        vpn_link: str,
        subscription_url: str,
    ) -> VPNAccount:

        vpn_account = VPNAccount(
            user_id=user_id,
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

    async def get_all(
        self,
    ) -> list[VPNAccount]:

        stmt = (
            select(VPNAccount)
            .options(
                selectinload(
                    VPNAccount.user
                ).selectinload(
                    User.subscriptions
                ),
            )
            .order_by(
                VPNAccount.id
            )
        )

        result = await self.session.execute(stmt)

        return list(
            result.scalars().all()
        )

    async def get_by_id(
        self,
        account_id: int,
    ) -> VPNAccount | None:

        stmt = (
            select(VPNAccount)
            .options(
                selectinload(
                    VPNAccount.user
                ).selectinload(
                    User.subscriptions
                ),
            )
            .where(
                VPNAccount.id == account_id
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def activate(
        self,
        account: VPNAccount,
    ) -> VPNAccount:

        account.is_active = True

        await self.session.flush()
        await self.session.refresh(account)

        return account

    async def deactivate(
        self,
        account: VPNAccount,
    ) -> VPNAccount:

        account.is_active = False

        await self.session.flush()
        await self.session.refresh(account)

        return account

    async def delete(
        self,
        account: VPNAccount,
    ) -> None:

        await self.session.delete(account)

        await self.session.flush()
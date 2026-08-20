from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vpn_account import VPNAccount
from app.repositories.vpn_account_repository import VPNAccountRepository
from app.services.username_service import UsernameService
from app.services.marzban_service import MarzbanService


class VPNAccountService:

    def __init__(
        self,
        session: AsyncSession,
        marzban_service: MarzbanService,
    ):
        self.repository = VPNAccountRepository(session)
        self.username_service = UsernameService()
        self.marzban_service = marzban_service

    async def get_or_create(
        self,
        user_id: int,
        end_date: datetime,
        protocol: str = "vless",
    ) -> VPNAccount:

        vpn_account = await self.repository.get_by_user_and_protocol(
            user_id=user_id,
            protocol=protocol,
        )

        if vpn_account is not None:

            await self.marzban_service.update_user_expire(
                username=vpn_account.marzban_username,
                expire=end_date,
            )

            return vpn_account

        username = self.username_service.generate(
            user_id=user_id,
        )

        if protocol == "vless":

            marzban_user = await self.marzban_service.create_vless_user(
                username=username,
                expire=end_date,
            )

        else:
            raise ValueError(
                f"Unsupported protocol: {protocol}"
            )

        return await self.repository.create(
            user_id=user_id,
            marzban_username=marzban_user.username,
            protocol=protocol,
            vpn_link=marzban_user.vpn_link,
            subscription_url=marzban_user.subscription_url,
        )

    async def get_existing(
        self,
        user_id: int,
        protocol: str = "vless",
    ) -> VPNAccount | None:

        return await self.repository.get_by_user_and_protocol(
            user_id=user_id,
            protocol=protocol,
        )

    async def get_all_accounts(
        self,
    ) -> list[VPNAccount]:

        return await self.repository.get_all()

    async def get_account(
        self,
        account_id: int,
    ) -> VPNAccount | None:

        return await self.repository.get_by_id(
            account_id=account_id
        )

    async def activate_account(
        self,
        account_id: int,
    ) -> VPNAccount:

        account = await self.repository.get_by_id(
            account_id=account_id
        )

        if account is None:
            raise ValueError(
                "VPN hisob topilmadi."
            )

        await self.marzban_service.activate_user(
            username=account.marzban_username,
        )

        return await self.repository.activate(
            account
        )

    async def deactivate_account(
        self,
        account_id: int,
    ) -> VPNAccount:

        account = await self.repository.get_by_id(
            account_id=account_id
        )

        if account is None:
            raise ValueError(
                "VPN hisob topilmadi."
            )

        await self.marzban_service.deactivate_user(
            username=account.marzban_username,
        )

        return await self.repository.deactivate(
            account
        )

    async def delete_account(
        self,
        account_id: int,
    ) -> VPNAccount:

        account = await self.repository.get_by_id(
            account_id=account_id
        )

        if account is None:
            raise ValueError(
                "VPN hisob topilmadi."
            )

        await self.marzban_service.delete_user(
            username=account.marzban_username,
        )

        await self.repository.delete(
            account
        )

        return account
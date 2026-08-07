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
        subscription_id: int,
        user_id: int,
        protocol: str = "vless",
    ) -> VPNAccount:

        vpn_account = await self.repository.get_by_subscription_and_protocol(
            subscription_id=subscription_id,
            protocol=protocol,
        )

        if vpn_account is not None:
            return vpn_account

        username = self.username_service.generate(
            user_id=user_id,
        )

        if protocol == "vless":
            marzban_user = await self.marzban_service.create_vless_user(
                username=username,
            )
        else:
            raise ValueError(
                f"Unsupported protocol: {protocol}"
            )

        return await self.repository.create(
            subscription_id=subscription_id,
            marzban_username=marzban_user.username,
            protocol=protocol,
            vpn_link=marzban_user.vpn_link,
            subscription_url=marzban_user.subscription_url,
        )
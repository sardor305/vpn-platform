from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.factories.marzban_factory import create_marzban_service
from app.services.service_period_service import ServicePeriodService
from app.services.vpn_account_service import VPNAccountService


class ServiceAccessService:
    """
    Synchronizes the currently active service period with the user's
    VPN account in Marzban.

    Business priority and service activation remain inside
    ServicePeriodService. This service only translates the selected
    current service into VPN access settings.
    """

    DATA_LIMIT_UNLIMITED = 0
    DATA_LIMIT_RESET_NO_RESET = "no_reset"
    PROTOCOL = "vless"

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.service_period_service = ServicePeriodService(
            session
        )

        self.marzban_service = create_marzban_service()

        self.vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=self.marzban_service,
        )

    @staticmethod
    def _get_data_limit(
        current_service,
    ) -> int:
        if current_service is None:
            return ServiceAccessService.DATA_LIMIT_UNLIMITED

        if (
            current_service.service_type
            == ServicePeriodService.WELCOME
        ):
            traffic = getattr(
                current_service.item,
                "traffic",
                None,
            )

            if traffic is None:
                raise ValueError(
                    "Welcome bonus uchun trafik limiti topilmadi."
                )

            if traffic.traffic_limit_bytes <= 0:
                raise ValueError(
                    "Welcome bonus trafik limiti noto'g'ri."
                )

            return traffic.traffic_limit_bytes

        return ServiceAccessService.DATA_LIMIT_UNLIMITED

    @staticmethod
    def _get_data_limit_reset_strategy(
        current_service,
    ) -> str:
        return ServiceAccessService.DATA_LIMIT_RESET_NO_RESET

    async def _reset_usage_for_welcome_if_needed(
        self,
        current_service,
        vpn_account,
        target_data_limit: int,
    ) -> None:
        """
        Reset Marzban traffic exactly when an existing VPN account
        enters the finite-traffic Welcome service.

        A Welcome service uses its own 3 GB traffic budget. Marzban's
        cumulative used_traffic must therefore be reset before applying
        the Welcome data limit.

        The reset is intentionally guarded by the current Marzban
        data_limit. Once the account already has the Welcome limit,
        repeated scheduler reconciliation will not reset usage again.
        """
        if current_service is None:
            return

        if (
            current_service.service_type
            != ServicePeriodService.WELCOME
        ):
            return

        if vpn_account is None:
            return

        marzban_user = await self.marzban_service.get_user(
            username=vpn_account.marzban_username,
        )

        if marzban_user is None:
            return

        current_data_limit = marzban_user.get(
            "data_limit"
        )

        if current_data_limit == target_data_limit:
            return

        await self.marzban_service.reset_user_data_usage(
            username=vpn_account.marzban_username,
        )

    async def sync_user(
        self,
        user_id: int,
    ):
        """
        Reconcile the service queue and synchronize Marzban access.

        Returns:
            tuple[current_service, vpn_account]
        """
        current_service = (
            await self.service_period_service.reconcile_user(
                user_id=user_id
            )
        )

        if current_service is None:
            vpn_account = (
                await self.vpn_account_service.get_existing(
                    user_id=user_id,
                    protocol=self.PROTOCOL,
                )
            )

            if vpn_account is not None and vpn_account.is_active:
                await self.marzban_service.deactivate_user(
                    username=vpn_account.marzban_username,
                )

                vpn_account = (
                    await self.vpn_account_service
                    .deactivate_account(
                        account_id=vpn_account.id
                    )
                )

            return None, vpn_account

        if current_service.end_date is None:
            raise ValueError(
                "Faol xizmatning tugash sanasi aniqlanmadi."
            )

        data_limit = self._get_data_limit(
            current_service=current_service
        )

        data_limit_reset_strategy = (
            self._get_data_limit_reset_strategy(
                current_service=current_service
            )
        )

        existing_account = (
            await self.vpn_account_service.get_existing(
                user_id=user_id,
                protocol=self.PROTOCOL,
            )
        )

        await self._reset_usage_for_welcome_if_needed(
            current_service=current_service,
            vpn_account=existing_account,
            target_data_limit=data_limit,
        )

        vpn_account = (
            await self.vpn_account_service.get_or_create(
                user_id=user_id,
                end_date=current_service.end_date,
                protocol=self.PROTOCOL,
                data_limit=data_limit,
                data_limit_reset_strategy=(
                    data_limit_reset_strategy
                ),
            )
        )

        return current_service, vpn_account
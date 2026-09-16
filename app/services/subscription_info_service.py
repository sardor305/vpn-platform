from sqlalchemy.ext.asyncio import AsyncSession

from app.factories.marzban_factory import create_marzban_service
from app.repositories.promo_repository import PromoRepository
from app.repositories.referral_repository import ReferralRepository
from app.services.daily_subscription_service import DailySubscriptionService
from app.services.service_period_service import ServicePeriodService
from app.services.subscription_service import SubscriptionService
from app.services.user_bonus_service import UserBonusService
from app.services.vpn_account_service import VPNAccountService


class SubscriptionInfoService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.subscription_service = SubscriptionService(session)
        self.daily_subscription_service = DailySubscriptionService(session)
        self.user_bonus_service = UserBonusService(session)
        self.service_period_service = ServicePeriodService(session)
        self.promo_repository = PromoRepository(session)
        self.referral_repository = ReferralRepository(session)

        self.vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=create_marzban_service(),
        )

    async def _get_bonus_source(
        self,
        bonus,
    ) -> dict:
        """Resolve the user-facing source of a numbered bonus."""

        bonus_type = bonus.bonus_type.lower()

        if bonus_type == ServicePeriodService.PROMO:
            redemption = (
                await self.promo_repository.get_redemption_by_bonus_id(
                    bonus.id,
                )
            )

            return {
                "bonus_type": bonus_type,
                "bonus_number": bonus.bonus_number,
                "source_type": "promo",
                "source": (
                    redemption.promo.code
                    if redemption is not None and redemption.promo is not None
                    else None
                ),
            }

        if bonus_type == ServicePeriodService.REFERRAL:
            referral = None
            if bonus.referral_id is not None:
                referral = (
                    await self.referral_repository.get_by_id_with_invited_user(
                        bonus.referral_id,
                    )
                )

            source = None
            if referral is not None and referral.invited_user is not None:
                source = str(referral.invited_user.telegram_id)

            return {
                "bonus_type": bonus_type,
                "bonus_number": bonus.bonus_number,
                "source_type": "referral",
                "source": source,
            }

        return {
            "bonus_type": bonus_type,
            "bonus_number": bonus.bonus_number,
            "source_type": bonus_type,
            "source": None,
        }

    async def _build_queue_details(
        self,
        pending_queue,
    ) -> list[dict]:
        """Attach stable number/source metadata to each projected queue item."""

        details: list[dict] = []

        for position, period in enumerate(pending_queue, start=1):
            detail = {
                "position": position,
                "period": period,
                "bonus_number": None,
                "source_type": None,
                "source": None,
            }

            if period.service_type in {
                ServicePeriodService.PROMO,
                ServicePeriodService.REFERRAL,
                ServicePeriodService.ADMIN,
            }:
                source_data = await self._get_bonus_source(period.item)
                detail.update(source_data)

            details.append(detail)

        return details

    async def _build_current_service_source(
        self,
        current_service,
    ) -> dict | None:
        if current_service is None:
            return None

        if current_service.service_type not in {
            ServicePeriodService.PROMO,
            ServicePeriodService.REFERRAL,
            ServicePeriodService.ADMIN,
        }:
            return None

        return await self._get_bonus_source(current_service.item)

    async def get_info(
        self,
        user_id: int,
    ):
        current_service = (
            await self.service_period_service.get_current_service(user_id)
        )

        # When a service is currently active, the displayed queue must start
        # when that service ends. Otherwise queue dates would incorrectly be
        # projected from "now" and could appear to overlap the current service.
        queue_start_date = None

        if (
            current_service is not None
            and current_service.end_date is not None
        ):
            queue_start_date = current_service.end_date

        pending_queue = (
            await self.service_period_service.get_pending_queue(
                user_id=user_id,
                start_date=queue_start_date,
            )
        )

        pending_queue_details = await self._build_queue_details(
            pending_queue,
        )

        current_service_source = (
            await self._build_current_service_source(current_service)
        )

        subscription = None
        daily_subscription = None
        active_bonus = None

        if current_service is not None:
            if current_service.service_type == ServicePeriodService.PAID:
                subscription = current_service.item

            elif current_service.service_type == ServicePeriodService.DAILY:
                daily_subscription = current_service.item

            else:
                active_bonus = current_service.item

        latest_subscription = (
            await self.subscription_service.get_latest_subscription(
                user_id,
            )
        )

        pending_bonuses = (
            await self.user_bonus_service.get_pending_bonuses(
                user_id,
            )
        )

        bonus_history = (
            await self.user_bonus_service.get_bonus_history(
                user_id,
            )
        )

        vpn_account = (
            await self.vpn_account_service.get_existing(
                user_id=user_id,
                protocol="vless",
            )
        )

        if (
            current_service is None
            and not pending_queue
            and latest_subscription is None
            and not bonus_history
        ):
            return None

        return {
            "current_service": current_service,
            "current_service_source": current_service_source,
            "pending_queue": pending_queue,
            "pending_queue_details": pending_queue_details,
            "subscription": subscription,
            "daily_subscription": daily_subscription,
            "active_bonus": active_bonus,
            "latest_subscription": latest_subscription,
            "pending_bonuses": pending_bonuses,
            "bonus_history": bonus_history,
            "vpn_account": vpn_account,
        }

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.promo import Promo
from app.models.promo_redemption import PromoRedemption
from app.models.user_bonus import UserBonus
from app.repositories.promo_repository import PromoRepository
from app.services.service_access_service import ServiceAccessService
from app.services.user_bonus_service import UserBonusService
from app.utils.datetime import utc_now


@dataclass
class PromoRedeemResult:
    success: bool
    message: str
    promo: Promo | None = None
    bonus: UserBonus | None = None
    redemption: PromoRedemption | None = None


class PromoService:
    """
    Business logic for promo-code redemption.

    Responsibilities:
    - Normalize and validate promo codes.
    - Check campaign availability and redemption limits.
    - Protect the redemption-limit check with a row lock on the Promo.
    - Create a pending UserBonus for a successful redemption.
    - Create the corresponding PromoRedemption record.
    - Immediately synchronize service access so an unused queue entry
      can become active when there is no currently active service.

    This service does not commit the database transaction.
    The caller is responsible for commit/rollback.
    """

    BONUS_TYPE = "promo"

    def __init__(self, session: AsyncSession):
        self.promo_repository = PromoRepository(session)
        self.user_bonus_service = UserBonusService(session)
        self.service_access_service = ServiceAccessService(session)

    @staticmethod
    def normalize_code(code: str) -> str:
        return (code or "").strip().upper()

    @staticmethod
    def _as_aware_utc(value: datetime | None) -> datetime | None:
        """
        Normalize a datetime for safe UTC comparison.

        The project database currently uses SQLAlchemy DateTime without
        timezone=True, so values may come back as naive UTC datetimes.
        """
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @classmethod
    def _is_not_started(
        cls,
        start_date: datetime | None,
        now: datetime,
    ) -> bool:
        normalized_start = cls._as_aware_utc(start_date)
        if normalized_start is None:
            return False
        return now < normalized_start

    @classmethod
    def _is_expired(
        cls,
        end_date: datetime | None,
        now: datetime,
    ) -> bool:
        normalized_end = cls._as_aware_utc(end_date)
        if normalized_end is None:
            return False
        return now >= normalized_end

    async def get_promo(self, code: str) -> Promo | None:
        normalized_code = self.normalize_code(code)
        if not normalized_code:
            return None
        return await self.promo_repository.get_by_code(
            code=normalized_code
        )

    async def redeem(
        self,
        user_id: int,
        code: str,
    ) -> PromoRedeemResult:
        """
        Redeem a promo code for a user.

        A successful redemption creates:
            PromoRedemption
                -> UserBonus(status="pending")

        If the user currently has no active service, ServiceAccessService
        may activate the new bonus immediately. Otherwise it remains in the
        normal service queue.

        No database commit is performed here.
        The caller is responsible for commit/rollback.
        """

        normalized_code = self.normalize_code(code)

        if not normalized_code:
            return PromoRedeemResult(
                success=False,
                message="❌ Promo kodini kiriting.",
            )

        if user_id <= 0:
            return PromoRedeemResult(
                success=False,
                message="❌ Foydalanuvchi aniqlanmadi.",
            )

        # Lock the Promo row so concurrent redemptions serialize their
        # redemption-limit checks for this campaign.
        promo = await self.promo_repository.get_by_code_for_update(
            code=normalized_code
        )

        if promo is None:
            return PromoRedeemResult(
                success=False,
                message="❌ Bunday promo kod topilmadi.",
            )

        if not promo.is_active:
            return PromoRedeemResult(
                success=False,
                message="❌ Bu promo kod hozir faol emas.",
                promo=promo,
            )

        now = utc_now()
        comparison_now = self._as_aware_utc(now)

        if comparison_now is None:
            raise RuntimeError("Current UTC time could not be determined.")

        if self._is_not_started(
            start_date=promo.start_date,
            now=comparison_now,
        ):
            return PromoRedeemResult(
                success=False,
                message="⏳ Bu promo kod hali kuchga kirmagan.",
                promo=promo,
            )

        if self._is_expired(
            end_date=promo.end_date,
            now=comparison_now,
        ):
            return PromoRedeemResult(
                success=False,
                message="⌛ Bu promo kodning amal qilish muddati tugagan.",
                promo=promo,
            )

        if promo.duration_days <= 0:
            return PromoRedeemResult(
                success=False,
                message="❌ Promo bonus davomiyligi noto'g'ri sozlangan.",
                promo=promo,
            )

        if promo.per_user_limit <= 0:
            return PromoRedeemResult(
                success=False,
                message="❌ Promo foydalanuvchi limiti noto'g'ri sozlangan.",
                promo=promo,
            )

        if (
            promo.total_redemption_limit is not None
            and promo.total_redemption_limit <= 0
        ):
            return PromoRedeemResult(
                success=False,
                message="❌ Promo umumiy limiti noto'g'ri sozlangan.",
                promo=promo,
            )

        total_redemptions = (
            await self.promo_repository.count_redemptions(
                promo_id=promo.id
            )
        )

        if (
            promo.total_redemption_limit is not None
            and total_redemptions >= promo.total_redemption_limit
        ):
            return PromoRedeemResult(
                success=False,
                message="❌ Bu promo kod bo'yicha barcha bonuslar tugagan.",
                promo=promo,
            )

        user_redemptions = (
            await self.promo_repository.count_user_redemptions(
                promo_id=promo.id,
                user_id=user_id,
            )
        )

        if user_redemptions >= promo.per_user_limit:
            return PromoRedeemResult(
                success=False,
                message="❌ Siz bu promo koddan foydalanish limitiga yetgansiz.",
                promo=promo,
            )

        # Promo campaign end_date only controls when the code can be redeemed.
        # Once redeemed, the bonus becomes a normal pending service period and
        # keeps its full duration until it reaches the front of the queue.
        bonus = await self.user_bonus_service.create_bonus(
            user_id=user_id,
            bonus_type=self.BONUS_TYPE,
            duration_days=promo.duration_days,
        )

        redemption = await self.promo_repository.create_redemption(
            promo_id=promo.id,
            user_id=user_id,
            bonus_id=bonus.id,
        )

        await self.service_access_service.sync_user(
            user_id=user_id
        )

        return PromoRedeemResult(
            success=True,
            message=(
                f"✅ Promo kod qabul qilindi! "
                f"Sizga {promo.duration_days} kun bonus berildi."
            ),
            promo=promo,
            bonus=bonus,
            redemption=redemption,
        )

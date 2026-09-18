from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.bonus_traffic import BonusTraffic
from app.models.promo import Promo
from app.models.promo_redemption import PromoRedemption
from app.models.referral import Referral
from app.models.user_bonus import UserBonus
from app.utils.datetime import utc_now


@dataclass(slots=True)
class BonusTypeStats:
    total: int = 0
    active: int = 0
    pending: int = 0
    expired: int = 0
    revoked: int = 0


@dataclass(slots=True)
class WelcomeTrafficStats:
    total_welcome: int = 0
    active: int = 0
    pending: int = 0
    expired: int = 0
    total_limit_bytes: int = 0
    total_used_bytes: int = 0
    warning_500mb_sent: int = 0
    exhausted: int = 0

    @property
    def remaining_bytes(self) -> int:
        return max(
            self.total_limit_bytes - self.total_used_bytes,
            0,
        )


@dataclass(slots=True)
class ReferralStats:
    total: int = 0
    rewarded: int = 0
    pending: int = 0
    reward_3_days: int = 0
    reward_7_days: int = 0
    total_reward_days: int = 0


@dataclass(slots=True)
class PromoStats:
    redemptions: int = 0
    bonuses: int = 0
    active: int = 0
    pending: int = 0
    expired: int = 0
    revoked: int = 0
    total_duration_days: int = 0


@dataclass(slots=True)
class BonusStatistics:
    period_days: int | None = None
    total: int = 0
    active: int = 0
    pending: int = 0
    expired: int = 0
    revoked: int = 0
    by_type: dict[str, BonusTypeStats] = field(default_factory=dict)
    welcome_traffic: WelcomeTrafficStats = field(
        default_factory=WelcomeTrafficStats
    )
    referral: ReferralStats = field(default_factory=ReferralStats)
    promo: PromoStats = field(default_factory=PromoStats)


@dataclass(slots=True)
class UserBonusStatistics:
    total: int = 0
    active: int = 0
    pending: int = 0
    expired: int = 0
    revoked: int = 0
    by_type: dict[str, BonusTypeStats] = field(default_factory=dict)
    welcome_traffic: WelcomeTrafficStats = field(
        default_factory=WelcomeTrafficStats
    )
    referral: ReferralStats = field(default_factory=ReferralStats)
    promo: PromoStats = field(default_factory=PromoStats)
    promo_codes: list[tuple[str, int, str, str]] = field(
        default_factory=list
    )


class BonusStatisticsService:
    """Read-only aggregate statistics for the admin bonus dashboard."""

    BONUS_TYPES = (
        "welcome",
        "promo",
        "referral",
        "admin",
    )

    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _created_filter(column, period_days: int | None):
        if period_days is None:
            return None

        now = utc_now()
        if period_days == 0:
            start = now.replace(
                hour=0,
                minute=0,
                second=0,
                microsecond=0,
            )
        else:
            start = now - timedelta(days=period_days)

        return column >= start

    @staticmethod
    def _empty_type_stats() -> dict[str, BonusTypeStats]:
        return {
            bonus_type: BonusTypeStats()
            for bonus_type in BonusStatisticsService.BONUS_TYPES
        }

    @staticmethod
    def _apply_status(stats: BonusTypeStats, status: str) -> None:
        if status == "active":
            stats.active += 1
        elif status == "pending":
            stats.pending += 1
        elif status == "expired":
            stats.expired += 1
        elif status == "revoked":
            stats.revoked += 1

    async def _bonus_rows(
        self,
        user_id: int | None = None,
        period_days: int | None = None,
    ) -> list[UserBonus]:
        stmt = select(UserBonus).order_by(
            UserBonus.created_at.asc(),
            UserBonus.id.asc(),
        )

        if user_id is not None:
            stmt = stmt.where(UserBonus.user_id == user_id)

        created_filter = self._created_filter(
            UserBonus.created_at,
            period_days,
        )
        if created_filter is not None:
            stmt = stmt.where(created_filter)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def _welcome_traffic_stats(
        self,
        user_id: int | None = None,
        period_days: int | None = None,
    ) -> WelcomeTrafficStats:
        stmt = (
            select(
                func.count(UserBonus.id),
                func.count(UserBonus.id).filter(
                    UserBonus.status == "active"
                ),
                func.count(UserBonus.id).filter(
                    UserBonus.status == "pending"
                ),
                func.count(UserBonus.id).filter(
                    UserBonus.status == "expired"
                ),
                func.coalesce(
                    func.sum(BonusTraffic.traffic_limit_bytes),
                    0,
                ),
                func.coalesce(
                    func.sum(BonusTraffic.traffic_used_bytes),
                    0,
                ),
                func.count(BonusTraffic.id).filter(
                    BonusTraffic.warning_500mb_sent.is_(True)
                ),
                func.count(BonusTraffic.id).filter(
                    BonusTraffic.exhausted_notified.is_(True)
                ),
            )
            .select_from(UserBonus)
            .outerjoin(
                BonusTraffic,
                BonusTraffic.bonus_id == UserBonus.id,
            )
            .where(UserBonus.bonus_type == "welcome")
        )

        if user_id is not None:
            stmt = stmt.where(UserBonus.user_id == user_id)

        created_filter = self._created_filter(
            UserBonus.created_at,
            period_days,
        )
        if created_filter is not None:
            stmt = stmt.where(created_filter)

        result = await self.session.execute(stmt)
        row = result.one()

        return WelcomeTrafficStats(
            total_welcome=int(row[0] or 0),
            active=int(row[1] or 0),
            pending=int(row[2] or 0),
            expired=int(row[3] or 0),
            total_limit_bytes=int(row[4] or 0),
            total_used_bytes=int(row[5] or 0),
            warning_500mb_sent=int(row[6] or 0),
            exhausted=int(row[7] or 0),
        )

    async def _referral_stats(
        self,
        user_id: int | None = None,
        period_days: int | None = None,
    ) -> ReferralStats:
        referral_stmt = select(Referral).order_by(Referral.id.asc())
        if user_id is not None:
            referral_stmt = referral_stmt.where(
                Referral.inviter_user_id == user_id
            )

        created_filter = self._created_filter(
            Referral.created_at,
            period_days,
        )
        if created_filter is not None:
            referral_stmt = referral_stmt.where(created_filter)

        result = await self.session.execute(referral_stmt)
        referrals = list(result.scalars().all())

        stats = ReferralStats(
            total=len(referrals),
            rewarded=sum(
                1 for item in referrals
                if item.status == "rewarded"
            ),
            pending=sum(
                1 for item in referrals
                if item.status == "pending"
            ),
        )

        bonus_stmt = select(UserBonus).where(
            UserBonus.bonus_type == "referral"
        )
        if user_id is not None:
            bonus_stmt = bonus_stmt.where(
                UserBonus.user_id == user_id
            )

        bonus_created_filter = self._created_filter(
            UserBonus.created_at,
            period_days,
        )
        if bonus_created_filter is not None:
            bonus_stmt = bonus_stmt.where(bonus_created_filter)

        bonus_result = await self.session.execute(bonus_stmt)
        referral_bonuses = list(bonus_result.scalars().all())

        for bonus in referral_bonuses:
            if bonus.duration_days == 7:
                stats.reward_7_days += 1
            elif bonus.duration_days == 3:
                stats.reward_3_days += 1
            stats.total_reward_days += bonus.duration_days

        return stats

    async def _promo_stats(
        self,
        user_id: int | None = None,
        period_days: int | None = None,
    ) -> tuple[PromoStats, list[tuple[str, int, str, str]]]:
        redemption_stmt = (
            select(
                PromoRedemption,
                Promo,
                UserBonus,
            )
            .join(Promo, Promo.id == PromoRedemption.promo_id)
            .join(UserBonus, UserBonus.id == PromoRedemption.bonus_id)
            .order_by(PromoRedemption.created_at.desc())
        )

        if user_id is not None:
            redemption_stmt = redemption_stmt.where(
                PromoRedemption.user_id == user_id
            )

        created_filter = self._created_filter(
            PromoRedemption.created_at,
            period_days,
        )
        if created_filter is not None:
            redemption_stmt = redemption_stmt.where(created_filter)

        result = await self.session.execute(redemption_stmt)
        rows = result.all()

        stats = PromoStats(
            redemptions=len(rows),
            bonuses=len(rows),
        )
        promo_codes: list[tuple[str, int, str, str]] = []

        for _, promo, bonus in rows:
            status = bonus.status
            if status == "active":
                stats.active += 1
            elif status == "pending":
                stats.pending += 1
            elif status == "expired":
                stats.expired += 1
            elif status == "revoked":
                stats.revoked += 1

            stats.total_duration_days += promo.duration_days
            promo_codes.append(
                (
                    promo.code,
                    promo.duration_days,
                    status,
                    promo.created_at.strftime("%d.%m.%Y %H:%M"),
                )
            )

        return stats, promo_codes

    async def get_global_statistics(
        self,
        period_days: int | None = None,
    ) -> BonusStatistics:
        bonuses = await self._bonus_rows(
            period_days=period_days,
        )

        stats = BonusStatistics(
            period_days=period_days,
            by_type=self._empty_type_stats(),
        )

        for bonus in bonuses:
            stats.total += 1
            self._apply_status(stats, bonus.status)

            type_stats = stats.by_type.setdefault(
                bonus.bonus_type,
                BonusTypeStats(),
            )
            type_stats.total += 1
            self._apply_status(type_stats, bonus.status)

        stats.welcome_traffic = await self._welcome_traffic_stats(
            period_days=period_days,
        )
        stats.referral = await self._referral_stats(
            period_days=period_days,
        )
        stats.promo, _ = await self._promo_stats(
            period_days=period_days,
        )

        return stats

    async def get_user_statistics(
        self,
        user_id: int,
    ) -> UserBonusStatistics:
        bonuses = await self._bonus_rows(user_id=user_id)

        stats = UserBonusStatistics(
            by_type=self._empty_type_stats(),
        )

        for bonus in bonuses:
            stats.total += 1
            self._apply_status(stats, bonus.status)

            type_stats = stats.by_type.setdefault(
                bonus.bonus_type,
                BonusTypeStats(),
            )
            type_stats.total += 1
            self._apply_status(type_stats, bonus.status)

        stats.welcome_traffic = await self._welcome_traffic_stats(
            user_id=user_id,
        )
        stats.referral = await self._referral_stats(
            user_id=user_id,
        )
        stats.promo, stats.promo_codes = await self._promo_stats(
            user_id=user_id,
        )

        return stats

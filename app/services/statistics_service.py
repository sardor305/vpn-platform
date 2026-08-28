from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.statistics_repository import (
    StatisticsRepository,
)
from app.schemas.statistics import StatisticsResult
from app.utils.datetime import utc_now


class StatisticsService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.repository = StatisticsRepository(
            session
        )

    async def get_statistics(
        self,
    ) -> StatisticsResult:

        now = utc_now()

        start_of_day = now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        start_of_month = now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return StatisticsResult(
            total_users=await self.repository.count_total_users(),
            active_users=await self.repository.count_active_users(),
            inactive_users=await self.repository.count_inactive_users(),
            users_today=await self.repository.count_users_today(
                start_of_day
            ),
            users_this_month=await self.repository.count_users_this_month(
                start_of_month
            ),
            total_subscriptions=(
                await self.repository.count_total_subscriptions()
            ),
            active_subscriptions=(
                await self.repository.count_active_subscriptions(
                    now
                )
            ),
            expired_subscriptions=(
                await self.repository.count_expired_subscriptions(
                    now
                )
            ),
            total_vpn_accounts=(
                await self.repository.count_total_vpn_accounts()
            ),
            active_vpn_accounts=(
                await self.repository.count_active_vpn_accounts()
            ),
            protocol_counts=(
                await self.repository.count_vpn_accounts_by_protocol()
            ),
            total_tickets=(
                await self.repository.count_total_tickets()
            ),
            new_tickets=(
                await self.repository.count_new_tickets()
            ),
            open_tickets=(
                await self.repository.count_open_tickets()
            ),
            closed_tickets=(
                await self.repository.count_closed_tickets()
            ),
        )
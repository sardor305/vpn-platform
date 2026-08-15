from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import Subscription
from app.models.support_ticket import SupportTicket
from app.models.user import User
from app.models.vpn_account import VPNAccount


class StatisticsRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def count_total_users(self) -> int:

        stmt = select(
            func.count(User.id)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_active_users(self) -> int:

        stmt = select(
            func.count(User.id)
        ).where(
            User.is_active.is_(True)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_inactive_users(self) -> int:

        stmt = select(
            func.count(User.id)
        ).where(
            User.is_active.is_(False)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_users_today(
        self,
        start_of_day: datetime,
    ) -> int:

        stmt = select(
            func.count(User.id)
        ).where(
            User.created_at >= start_of_day
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_users_this_month(
        self,
        start_of_month: datetime,
    ) -> int:

        stmt = select(
            func.count(User.id)
        ).where(
            User.created_at >= start_of_month
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_total_subscriptions(self) -> int:

        stmt = select(
            func.count(Subscription.id)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_active_subscriptions(
        self,
        now: datetime,
    ) -> int:

        stmt = select(
            func.count(Subscription.id)
        ).where(
            Subscription.status == "active",
            Subscription.end_date > now,
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_expired_subscriptions(
        self,
        now: datetime,
    ) -> int:

        stmt = select(
            func.count(Subscription.id)
        ).where(
            Subscription.end_date <= now
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_total_vpn_accounts(self) -> int:

        stmt = select(
            func.count(VPNAccount.id)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_active_vpn_accounts(self) -> int:

        stmt = select(
            func.count(VPNAccount.id)
        ).where(
            VPNAccount.is_active.is_(True)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_vless_accounts(self) -> int:

        stmt = select(
            func.count(VPNAccount.id)
        ).where(
            VPNAccount.protocol == "vless"
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_total_tickets(self) -> int:

        stmt = select(
            func.count(SupportTicket.id)
        ).where(
            SupportTicket.status != "deleted"
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_new_tickets(self) -> int:

        stmt = select(
            func.count(SupportTicket.id)
        ).where(
            SupportTicket.status == "new"
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_open_tickets(self) -> int:

        stmt = select(
            func.count(SupportTicket.id)
        ).where(
            SupportTicket.status == "open"
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()

    async def count_closed_tickets(self) -> int:

        stmt = select(
            func.count(SupportTicket.id)
        ).where(
            SupportTicket.status == "closed"
        )

        result = await self.session.execute(stmt)

        return result.scalar_one()
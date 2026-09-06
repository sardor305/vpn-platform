from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subscription import Subscription
from app.utils.datetime import utc_now


class SubscriptionRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_active_by_user(
        self,
        user_id: int,
    ) -> Subscription | None:

        now = utc_now()

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_latest_by_user(
        self,
        user_id: int,
    ) -> Subscription | None:

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == user_id,
            )
            .order_by(
                Subscription.id.desc()
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_all_by_user(
        self,
        user_id: int,
    ) -> list[Subscription]:

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == user_id,
            )
            .order_by(
                Subscription.id.desc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_by_user_paginated(
        self,
        user_id: int,
        page: int,
        page_size: int,
    ) -> tuple[list[Subscription], int]:

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 5

        count_stmt = (
            select(func.count(Subscription.id))
            .where(
                Subscription.user_id == user_id,
            )
        )

        count_result = await self.session.execute(
            count_stmt
        )

        total = count_result.scalar_one()

        offset = (
            (page - 1) * page_size
        )

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.plan)
            )
            .where(
                Subscription.user_id == user_id,
            )
            .order_by(
                Subscription.id.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(stmt)

        subscriptions = list(
            result.scalars().all()
        )

        return subscriptions, total

    async def get_all_paginated(
        self,
        page: int,
        page_size: int,
    ) -> tuple[list[Subscription], int]:

        if page < 1:
            page = 1

        if page_size < 1:
            page_size = 5

        count_stmt = (
            select(func.count(Subscription.id))
        )

        count_result = await self.session.execute(
            count_stmt
        )

        total = count_result.scalar_one()

        offset = (
            (page - 1) * page_size
        )

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.plan),
            )
            .order_by(
                Subscription.id.desc()
            )
            .offset(offset)
            .limit(page_size)
        )

        result = await self.session.execute(stmt)

        subscriptions = list(
            result.scalars().all()
        )

        return subscriptions, total

    async def get_all_active(
        self,
    ) -> list[Subscription]:

        now = utc_now()

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.plan),
            )
            .where(
                Subscription.status == "active",
                Subscription.end_date > now,
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_all_active_for_expiry_check(
        self,
    ) -> list[Subscription]:

        stmt = (
            select(Subscription)
            .options(
                selectinload(Subscription.user),
                selectinload(Subscription.plan),
            )
            .where(
                Subscription.status == "active",
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def create(
        self,
        user_id: int,
        plan_id: int,
        start_date,
        end_date,
        status: str = "active",
    ) -> Subscription:

        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            start_date=start_date,
            end_date=end_date,
            status=status,
        )

        self.session.add(subscription)

        await self.session.flush()

        await self.session.refresh(subscription)

        return subscription

    async def update(
        self,
        subscription: Subscription,
    ) -> Subscription:

        await self.session.flush()

        await self.session.refresh(subscription)

        return subscription

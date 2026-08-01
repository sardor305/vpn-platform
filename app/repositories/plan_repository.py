from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan


class PlanRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> list[Plan]:

        stmt = select(Plan).where(
            Plan.is_active == True
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_by_id(
        self,
        plan_id: int
    ) -> Plan | None:

        stmt = select(Plan).where(
            Plan.id == plan_id
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_name(
        self,
        name: str,
    ) -> Plan | None:

        stmt = select(Plan).where(
            Plan.name == name
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()
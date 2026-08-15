from sqlalchemy.ext.asyncio import AsyncSession

from app.models.plan import Plan
from app.repositories.plan_repository import PlanRepository


class PlanService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.plan_repository = PlanRepository(session)

    async def get_all_active_plans(
        self,
    ) -> list[Plan]:

        return await self.plan_repository.get_all_active()

    async def get_all_plans(
        self,
    ) -> list[Plan]:

        return await self.plan_repository.get_all()

    async def get_plan(
        self,
        plan_id: int,
    ) -> Plan | None:

        return await self.plan_repository.get_by_id(
            plan_id
        )

    async def create_plan(
        self,
        name: str,
        price: int,
        duration_days: int,
    ) -> Plan:

        return await self.plan_repository.create(
            name=name,
            price=price,
            duration_days=duration_days,
        )

    async def update_plan(
        self,
        plan: Plan,
    ) -> Plan:

        return await self.plan_repository.update(
            plan
        )
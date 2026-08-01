import asyncio

from app.database.database import async_session
from app.models.plan import Plan
from app.repositories.plan_repository import PlanRepository


async def seed_plans():

    async with async_session() as session:

        plan_repository = PlanRepository(session)

        plans = [
            Plan(
                name="🥉 1 oy",
                price=300,
                duration_days=30,
            ),
            Plan(
                name="🥈 3 oy",
                price=800,
                duration_days=90,
            ),
        ]

        for plan in plans:

            existing_plan = await plan_repository.get_by_name(
                plan.name
            )

            if existing_plan is None:
                session.add(plan)

        await session.commit()

        print("✅ Tariflar muvaffaqiyatli qo'shildi!")


if __name__ == "__main__":
    asyncio.run(seed_plans())
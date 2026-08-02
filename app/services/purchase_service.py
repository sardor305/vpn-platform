from sqlalchemy.ext.asyncio import AsyncSession

from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.schemas.purchase_result import PurchaseResult


class PurchaseService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.user_service = UserService(session)
        self.plan_service = PlanService(session)
        self.payment_service = PaymentService()
        self.subscription_service = SubscriptionService(session)

    async def purchase(
        self,
        user_id: int,
        plan_id: int,
    ) -> PurchaseResult:
        plan = await self.plan_service.get_plan(
            plan_id
        )

        if plan is None:
            return PurchaseResult(
                success=False,
                message="Tarif topilmadi.",
            )

        subscription = await self.subscription_service.get_active_subscription(
            user_id
        )

        payment = await self.payment_service.create_test_payment()

        if not payment.success:
            return PurchaseResult(
                success=False,
                message=payment.message,
            )

        if subscription is not None:

            subscription = await self.subscription_service.extend_subscription(
                subscription=subscription,
                plan_id=plan.id,
                duration_days=plan.duration_days,
            )

        else:

            subscription = await self.subscription_service.create_subscription(
                user_id=user_id,
                plan_id=plan.id,
                duration_days=plan.duration_days,
            )

        return PurchaseResult(
            success=True,
            message="Obuna muvaffaqiyatli rasmiylashtirildi.",
            plan=plan,
            subscription=subscription,
        )
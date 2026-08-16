from sqlalchemy.ext.asyncio import AsyncSession

from app.factories.marzban_factory import create_marzban_service
from app.schemas.purchase_result import PurchaseResult
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService
from app.services.vpn_account_service import VPNAccountService


class PurchaseService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.user_service = UserService(session)
        self.plan_service = PlanService(session)
        self.payment_service = PaymentService()
        self.subscription_service = SubscriptionService(session)

        self.marzban_service = create_marzban_service()

        self.vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=self.marzban_service,
        )

    async def purchase(
        self,
        user_id: int,
        plan_id: int,
    ) -> PurchaseResult:

        plan = await self.plan_service.get_plan(plan_id)

        if plan is None:
            return PurchaseResult(
                success=False,
                message="Tarif topilmadi.",
            )

        payment = await self.payment_service.create_test_payment()

        if not payment.success:
            return PurchaseResult(
                success=False,
                message=payment.message,
            )

        subscription = await self.subscription_service.get_active_subscription(
            user_id
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

        user = await self.user_service.get_by_id(user_id)

        if user is None:
            return PurchaseResult(
                success=False,
                message="Foydalanuvchi topilmadi.",
            )

        vpn_account = await self.vpn_account_service.get_or_create(
            subscription_id=subscription.id,
            user_id=user.id,
            end_date=subscription.end_date,
            protocol="vless",
        )

        return PurchaseResult(
            success=True,
            message="Obuna muvaffaqiyatli rasmiylashtirildi.",
            plan=plan,
            subscription=subscription,
            vpn_link=vpn_account.vpn_link,
            subscription_url=vpn_account.subscription_url,
        )
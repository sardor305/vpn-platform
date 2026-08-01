from sqlalchemy.ext.asyncio import AsyncSession

from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.subscription_service import SubscriptionService
from app.services.user_service import UserService


class PurchaseService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.user_service = UserService(session)
        self.plan_service = PlanService(session)
        self.payment_service = PaymentService()
        self.subscription_service = SubscriptionService(session)
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.purchase_result import PurchaseResult
from app.services.daily_subscription_service import (
    DailySubscriptionService,
)
from app.services.payment_service import PaymentService
from app.services.plan_service import PlanService
from app.services.referral_service import ReferralService
from app.services.service_access_service import (
    ServiceAccessService,
)
from app.services.service_period_service import (
    ServicePeriodService,
)
from app.services.subscription_service import (
    SubscriptionService,
)
from app.services.user_service import UserService


class PurchaseService:
    DATA_LIMIT_UNLIMITED = 0
    DATA_LIMIT_RESET_NO_RESET = "no_reset"

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.user_service = UserService(session)
        self.plan_service = PlanService(session)

        self.daily_subscription_service = (
            DailySubscriptionService(session)
        )

        self.payment_service = PaymentService()

        self.subscription_service = (
            SubscriptionService(session)
        )

        self.service_period_service = (
            ServicePeriodService(session)
        )

        self.service_access_service = (
            ServiceAccessService(session)
        )

        self.referral_service = ReferralService(
            session
        )

    async def _sync_vpn_to_current_service(
        self,
        user_id: int,
    ):
        return await self.service_access_service.sync_user(
            user_id=user_id
        )

    async def purchase_plan(
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

        user = await self.user_service.get_by_id(
            user_id
        )

        if user is None:
            return PurchaseResult(
                success=False,
                message="Foydalanuvchi topilmadi.",
            )

        await self.service_period_service.reconcile_user(
            user_id
        )

        active_subscription = (
            await self.subscription_service
            .get_active_subscription(user_id)
        )

        payment = (
            await self.payment_service
            .create_test_payment()
        )

        if not payment.success:
            return PurchaseResult(
                success=False,
                message=payment.message,
            )

        if active_subscription is not None:
            active_subscription = (
                await self.subscription_service
                .extend_subscription(
                    subscription=active_subscription,
                    duration_days=plan.duration_days,
                )
            )

            current_service, vpn_account = (
                await self._sync_vpn_to_current_service(
                    user_id
                )
            )

            if (
                current_service is None
                or vpn_account is None
            ):
                return PurchaseResult(
                    success=False,
                    message=(
                        "To‘lov qabul qilindi, ammo VPN "
                        "xizmatini yangilashda xatolik yuz berdi."
                    ),
                    plan=plan,
                    subscription=active_subscription,
                )

            return PurchaseResult(
                success=True,
                message=(
                    "Obuna muvaffaqiyatli "
                    "rasmiylashtirildi."
                ),
                plan=plan,
                subscription=active_subscription,
                vpn_link=vpn_account.vpn_link,
                subscription_url=(
                    vpn_account.subscription_url
                ),
            )

        subscription = (
            await self.subscription_service
            .create_subscription(
                user_id=user.id,
                plan_id=plan.id,
                duration_days=plan.duration_days,
            )
        )

        # Referral reward is processed only here:
        # this is the path for a newly created paid
        # subscription. Renewals/extensions above do not
        # trigger referral rewards, and Daily purchases
        # never reach this block.
        await self.referral_service.process_first_monthly_purchase(
            invited_user_id=user.id,
            subscription_id=subscription.id,
        )

        # Persist the paid subscription and its referral reward before
        # contacting Marzban. Marzban is an external system and cannot
        # participate in the PostgreSQL transaction. Committing here
        # prevents a Marzban sync failure from rolling back the referral
        # reward that was earned by the completed monthly purchase.
        await self.session.commit()

        current_service, vpn_account = (
            await self._sync_vpn_to_current_service(
                user_id
            )
        )

        if (
            current_service is None
            or vpn_account is None
        ):
            return PurchaseResult(
                success=False,
                message=(
                    "Obuna yaratildi, ammo xizmatni "
                    "faollashtirishda xatolik yuz berdi."
                ),
                plan=plan,
                subscription=subscription,
            )

        return PurchaseResult(
            success=True,
            message=(
                "Obuna muvaffaqiyatli "
                "rasmiylashtirildi."
            ),
            plan=plan,
            subscription=subscription,
            vpn_link=vpn_account.vpn_link,
            subscription_url=vpn_account.subscription_url,
        )

    async def purchase_daily(
        self,
        user_id: int,
        duration_days: int,
    ) -> PurchaseResult:
        if duration_days <= 0:
            return PurchaseResult(
                success=False,
                message="Obuna muddati noto‘g‘ri.",
            )

        user = await self.user_service.get_by_id(
            user_id
        )

        if user is None:
            return PurchaseResult(
                success=False,
                message="Foydalanuvchi topilmadi.",
            )

        current_service = (
            await self.service_period_service
            .reconcile_user(user_id)
        )

        if current_service is not None:
            if current_service.end_date is None:
                return PurchaseResult(
                    success=False,
                    message=(
                        "Hozirgi xizmat muddati "
                        "aniqlanmadi."
                    ),
                )

            now = (
                datetime.now(
                    current_service.end_date.tzinfo
                )
                if current_service.end_date.tzinfo
                else datetime.now()
            )

            remaining_seconds = (
                current_service.end_date - now
            ).total_seconds()

            remaining_days = (
                remaining_seconds / 86400
            )

            pending_queue = (
                await self.service_period_service
                .get_pending_queue(
                    user_id=user_id,
                    start_date=current_service.end_date,
                )
            )

            if pending_queue:
                return PurchaseResult(
                    success=False,
                    message=(
                        "🟢 Hozirgi xizmatdan keyin navbatda "
                        "boshqa xizmat mavjud.\n\n"
                        "Kunlik obunani faqat hozirgi xizmat "
                        "navbatdagi oxirgi xizmat bo‘lsa va "
                        "3 kun yoki undan kam muddat qolganida "
                        "sotib olish mumkin."
                    ),
                )

            if remaining_days > 3:
                return PurchaseResult(
                    success=False,
                    message=(
                        "🟢 Faol xizmat mavjud.\n\n"
                        f"📅 Tugash sanasi: "
                        f"{current_service.end_date.strftime('%d.%m.%Y')}\n\n"
                        "Kunlik obunani hozircha sotib olish mumkin emas. "
                        "Faol xizmat tugashiga 3 kun yoki undan kam "
                        "qolganda kunlik obuna olish mumkin."
                    ),
                )

        payment = (
            await self.payment_service
            .create_test_payment()
        )

        if not payment.success:
            return PurchaseResult(
                success=False,
                message=payment.message,
            )

        daily_subscription = (
            await self.daily_subscription_service
            .create_subscription(
                user_id=user.id,
                duration_days=duration_days,
            )
        )

        current_service, vpn_account = (
            await self._sync_vpn_to_current_service(
                user_id
            )
        )

        if vpn_account is None:
            return PurchaseResult(
                success=False,
                message=(
                    "Kunlik obuna yaratildi, ammo VPN xizmatini "
                    "sinxronlashda xatolik yuz berdi."
                ),
                daily_subscription=daily_subscription,
            )

        return PurchaseResult(
            success=True,
            message=(
                "Kunlik obuna muvaffaqiyatli "
                "rasmiylashtirildi."
            ),
            daily_subscription=daily_subscription,
            vpn_link=vpn_account.vpn_link,
            subscription_url=vpn_account.subscription_url,
        )
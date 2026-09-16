import asyncio

from aiogram import Bot

from app.database.database import async_session
from app.repositories.daily_subscription_repository import (
    DailySubscriptionRepository,
)
from app.repositories.subscription_repository import (
    SubscriptionRepository,
)
from app.repositories.user_bonus_repository import (
    UserBonusRepository,
)
from app.repositories.vpn_account_repository import (
    VPNAccountRepository,
)
from app.services.service_access_service import ServiceAccessService
from app.services.subscription_reminder_service import (
    SubscriptionReminderService,
)
from app.services.welcome_traffic_monitor_service import (
    WelcomeTrafficMonitorService,
)


SCHEDULER_INTERVAL_SECONDS = 5 * 60


async def collect_reconciliation_user_ids(
    session,
) -> set[int]:
    """Collect users whose service state may need reconciliation."""

    user_ids: set[int] = set()

    vpn_account_repository = VPNAccountRepository(session)
    subscription_repository = SubscriptionRepository(session)
    daily_repository = DailySubscriptionRepository(session)
    bonus_repository = UserBonusRepository(session)

    accounts = await vpn_account_repository.get_all()
    for account in accounts:
        user_ids.add(account.user_id)

    subscriptions = await subscription_repository.get_all_active()
    for subscription in subscriptions:
        user_ids.add(subscription.user_id)

    pending_subscriptions = (
        await subscription_repository.get_all_pending()
    )
    for subscription in pending_subscriptions:
        user_ids.add(subscription.user_id)

    daily_subscriptions = await daily_repository.get_all_active()
    for daily in daily_subscriptions:
        user_ids.add(daily.user_id)

    pending_daily_subscriptions = (
        await daily_repository.get_all_pending()
    )
    for daily in pending_daily_subscriptions:
        user_ids.add(daily.user_id)

    active_bonuses = await bonus_repository.get_all_active()
    for bonus in active_bonuses:
        user_ids.add(bonus.user_id)

    pending_bonuses = await bonus_repository.get_all_pending()
    for bonus in pending_bonuses:
        user_ids.add(bonus.user_id)

    return user_ids


async def reconcile_service_access(
    session,
) -> int:
    """Synchronize every relevant user with the current service period."""

    user_ids = await collect_reconciliation_user_ids(
        session
    )

    service_access_service = ServiceAccessService(
        session
    )

    success_count = 0

    for user_id in sorted(user_ids):
        try:
            # Isolate each user's DB mutations in a SAVEPOINT. A failed
            # user can therefore be rolled back without losing successful
            # changes already made for previous users in this scheduler pass.
            async with session.begin_nested():
                await service_access_service.sync_user(
                    user_id=user_id
                )

            success_count += 1
        except Exception as exc:
            # begin_nested() rolls back the user's SAVEPOINT automatically.
            # The outer transaction remains usable for the next user.
            print(
                "SERVICE ACCESS RECONCILIATION ERROR: "
                f"user_id={user_id} error={exc}"
            )

    return success_count


async def subscription_reminder_scheduler(
    bot: Bot,
) -> None:
    """
    Central five-minute service reconciliation loop.

    The scheduler is a repair/reconciliation layer. Business decisions
    remain inside ServicePeriodService and ServiceAccessService.
    """

    print(
        "SERVICE SCHEDULER: "
        f"interval={SCHEDULER_INTERVAL_SECONDS} seconds "
        "(5 minutes)"
    )

    while True:
        try:
            async with async_session() as session:
                # =================================================
                # 1. SERVICE ACCESS / QUEUE RECONCILIATION
                # =================================================

                reconciled_count = (
                    await reconcile_service_access(
                        session=session
                    )
                )

                # =================================================
                # 2. WELCOME TRAFFIC MONITOR
                # =================================================

                welcome_traffic_service = (
                    WelcomeTrafficMonitorService(
                        session=session,
                        bot=bot,
                    )
                )

                exhausted_count = (
                    await welcome_traffic_service
                    .check_active_welcome_bonuses()
                )

                # =================================================
                # 3. SUBSCRIPTION REMINDERS
                # =================================================

                reminder_service = (
                    SubscriptionReminderService(
                        session=session,
                        bot=bot,
                    )
                )

                sent_count = (
                    await reminder_service
                    .send_due_reminders()
                )

                # =================================================
                # 4. COMMIT
                # =================================================

                await session.commit()

                # =================================================
                # 5. LOG
                # =================================================

                print(
                    "SERVICE SCHEDULER: "
                    f"reconciled={reconciled_count}, "
                    f"welcome_exhausted={exhausted_count}, "
                    f"reminders={sent_count}"
                )

        except asyncio.CancelledError:
            print(
                "SERVICE SCHEDULER: cancelled."
            )
            raise

        except Exception as exc:
            print(
                "SERVICE SCHEDULER ERROR:",
                repr(exc),
            )

        await asyncio.sleep(
            SCHEDULER_INTERVAL_SECONDS
        )
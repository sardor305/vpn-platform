import asyncio
from datetime import datetime, timezone

from aiogram import Bot

from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.services.subscription_reminder_service import (
    SubscriptionReminderService,
)
from app.services.vpn_account_service import VPNAccountService


async def check_expired_vpn_accounts(
    session,
    bot: Bot,
) -> int:

    marzban_service = create_marzban_service()

    vpn_account_service = VPNAccountService(
        session=session,
        marzban_service=marzban_service,
    )

    accounts = await vpn_account_service.get_all_accounts()

    now = datetime.now(timezone.utc)

    deactivated_count = 0

    for account in accounts:

        if not account.is_active:
            continue

        try:

            user = account.user

            subscription = None

            active_subscriptions = [
                item
                for item in user.subscriptions
                if item.status == "active"
            ]

            if active_subscriptions:

                subscription = max(
                    active_subscriptions,
                    key=lambda item: item.end_date,
                )

            daily_subscription = None

            active_daily_subscriptions = [
                item
                for item in user.daily_subscriptions
                if item.status == "active"
            ]

            if active_daily_subscriptions:

                daily_subscription = max(
                    active_daily_subscriptions,
                    key=lambda item: item.end_date,
                )

            # Oddiy Subscription ustun.
            # Agar oddiy Subscription mavjud bo'lmasa,
            # DailySubscription ishlatiladi.

            if subscription is not None:

                end_date = subscription.end_date

            elif daily_subscription is not None:

                end_date = daily_subscription.end_date

            else:

                print(
                    "VPN EXPIRY CHECK: "
                    f"User uchun faol obuna topilmadi: "
                    f"{account.marzban_username}"
                )

                continue

            if end_date.tzinfo is None:

                subscription_expire = end_date.replace(
                    tzinfo=timezone.utc
                )

            else:

                subscription_expire = end_date

            # Marzban expire faqat sekund aniqligida saqlanadi.
            # PostgreSQL esa mikrosekundlarni saqlashi mumkin.
            # Shuning uchun subscription sanasini sekundgacha
            # normalize qilamiz.

            subscription_expire = subscription_expire.replace(
                microsecond=0
            )

            # 1. Platformadagi obuna muddati tugagan bo'lsa,
            # VPN accountni deaktivatsiya qilamiz.

            if subscription_expire <= now:

                print(
                    "VPN EXPIRY: "
                    f"{account.marzban_username} "
                    f"platforma obunasi muddati tugagan. "
                    f"Expire: "
                    f"{subscription_expire.isoformat()}"
                )

                await vpn_account_service.deactivate_account(
                    account_id=account.id,
                )

                deactivated_count += 1

                print(
                    "VPN DEACTIVATED: "
                    f"{account.marzban_username}"
                )

                continue

            # 2. Subscription hali faol.
            # Marzban expire sanasini platformadagi
            # subscription end_date bilan sinxronlaymiz.

            marzban_user = await marzban_service.get_user(
                username=account.marzban_username,
            )

            if marzban_user is None:

                print(
                    "VPN EXPIRY CHECK: "
                    "Marzban user topilmadi: "
                    f"{account.marzban_username}"
                )

                continue

            expire_timestamp = marzban_user.get(
                "expire"
            )

            if expire_timestamp is None:

                print(
                    "VPN EXPIRY CHECK: "
                    "Marzban expire mavjud emas: "
                    f"{account.marzban_username}"
                )

                continue

            expire_date = datetime.fromtimestamp(
                expire_timestamp,
                timezone.utc,
            )

            # Marzban expire va platforma obunasi
            # bir-biridan farq qilsa, platforma sanasi
            # asosida Marzban'ni yangilaymiz.

            if expire_date != subscription_expire:

                print(
                    "VPN SYNC: "
                    f"{account.marzban_username} "
                    "Marzban expire yangilanmoqda."
                )

                print(
                    "VPN SYNC OLD: "
                    f"{expire_date.isoformat()}"
                )

                print(
                    "VPN SYNC NEW: "
                    f"{subscription_expire.isoformat()}"
                )

                await marzban_service.update_user_expire(
                    username=account.marzban_username,
                    expire=subscription_expire,
                )

        except Exception as e:

            print(
                "VPN EXPIRY CHECK ERROR:",
                repr(e),
                "account_id=",
                account.id,
                "username=",
                account.marzban_username,
            )

    return deactivated_count


async def subscription_reminder_scheduler(
    bot: Bot,
) -> None:

    while True:

        try:

            async with async_session() as session:

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

                deactivated_count = (
                    await check_expired_vpn_accounts(
                        session=session,
                        bot=bot,
                    )
                )

                await session.commit()

                if sent_count > 0:

                    print(
                        "SUBSCRIPTION REMINDER: "
                        f"{sent_count} ta xabar yuborildi."
                    )

                if deactivated_count > 0:

                    print(
                        "VPN EXPIRY: "
                        f"{deactivated_count} ta account "
                        "deaktivatsiya qilindi."
                    )

        except Exception as e:

            print(
                "SUBSCRIPTION SCHEDULER ERROR:",
                repr(e),
            )

        await asyncio.sleep(60 * 60)
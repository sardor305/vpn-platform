import asyncio
from datetime import datetime, timezone

from aiogram import Bot

from app.database.database import async_session
from app.factories.marzban_factory import create_marzban_service
from app.services.daily_subscription_service import (
    DailySubscriptionService,
)
from app.services.subscription_reminder_service import (
    SubscriptionReminderService,
)
from app.services.subscription_service import (
    SubscriptionService,
)
from app.services.vpn_account_service import VPNAccountService


async def check_expired_subscriptions(
    session,
) -> int:
    """
    Muddati tugagan oddiy va kunlik obunalarni
    avtomatik expired holatiga o'tkazadi.

    Service -> Repository arxitekturasi ishlatiladi.
    """

    now = datetime.now(timezone.utc)

    expired_count = 0

    subscription_service = SubscriptionService(
        session
    )

    daily_subscription_service = (
        DailySubscriptionService(session)
    )

    # =========================================================
    # 1. ODDIY SUBSCRIPTIONLARNI TEKSHIRISH
    # =========================================================

    subscriptions = (
        await subscription_service
        .get_all_active_for_expiry_check()
    )

    for subscription in subscriptions:

        end_date = subscription.end_date

        if end_date.tzinfo is None:

            expire_date = end_date.replace(
                tzinfo=timezone.utc
            )

        else:

            expire_date = end_date

        if expire_date <= now:

            subscription.status = "expired"

            expired_count += 1

            print(
                "SUBSCRIPTION EXPIRED: "
                f"id={subscription.id} "
                f"user_id={subscription.user_id} "
                f"expire={expire_date.isoformat()}"
            )

    # =========================================================
    # 2. DAILY SUBSCRIPTIONLARNI TEKSHIRISH
    # =========================================================

    daily_subscriptions = (
        await daily_subscription_service
        .get_all_active_for_expiry_check()
    )

    for daily_subscription in daily_subscriptions:

        end_date = daily_subscription.end_date

        if end_date.tzinfo is None:

            expire_date = end_date.replace(
                tzinfo=timezone.utc
            )

        else:

            expire_date = end_date

        if expire_date <= now:

            daily_subscription.status = "expired"

            expired_count += 1

            print(
                "DAILY SUBSCRIPTION EXPIRED: "
                f"id={daily_subscription.id} "
                f"user_id={daily_subscription.user_id} "
                f"expire={expire_date.isoformat()}"
            )

    # =========================================================
    # 3. NATIJA
    # =========================================================

    if expired_count > 0:

        print(
            "SUBSCRIPTION EXPIRY: "
            f"{expired_count} ta obuna expired qilindi."
        )

    return expired_count


async def check_expired_vpn_accounts(
    session,
    bot: Bot,
) -> int:
    """
    VPN accountlarni foydalanuvchining haqiqiy faol
    obunasi bilan sinxronlaydi.

    Faol obuna bo'lmasa:
        VPN account -> inactive

    Faol obuna bo'lsa:
        Marzban expire -> subscription end_date
    """

    marzban_service = create_marzban_service()

    vpn_account_service = VPNAccountService(
        session=session,
        marzban_service=marzban_service,
    )

    accounts = (
        await vpn_account_service
        .get_all_accounts()
    )

    now = datetime.now(timezone.utc)

    deactivated_count = 0

    for account in accounts:

        if not account.is_active:
            continue

        try:

            user = account.user

            # =================================================
            # 1. HAQIQATAN FAOL ODDIY SUBSCRIPTIONLAR
            # =================================================

            active_subscriptions = [
                subscription
                for subscription in user.subscriptions
                if (
                    subscription.status == "active"
                    and (
                        (
                            subscription.end_date.replace(
                                tzinfo=timezone.utc
                            )
                            if subscription.end_date.tzinfo is None
                            else subscription.end_date
                        )
                        > now
                    )
                )
            ]

            # =================================================
            # 2. HAQIQATAN FAOL DAILY SUBSCRIPTIONLAR
            # =================================================

            active_daily_subscriptions = [
                daily_subscription
                for daily_subscription
                in user.daily_subscriptions
                if (
                    daily_subscription.status == "active"
                    and (
                        (
                            daily_subscription.end_date.replace(
                                tzinfo=timezone.utc
                            )
                            if daily_subscription.end_date.tzinfo is None
                            else daily_subscription.end_date
                        )
                        > now
                    )
                )
            ]

            # =================================================
            # 3. ENG KECH TUGAYDIGAN FAOL OBUNANI ANIQLASH
            # =================================================

            subscription = None

            if active_subscriptions:

                subscription = max(
                    active_subscriptions,
                    key=lambda item: item.end_date,
                )

            daily_subscription = None

            if active_daily_subscriptions:

                daily_subscription = max(
                    active_daily_subscriptions,
                    key=lambda item: item.end_date,
                )

            # =================================================
            # 4. VPN UCHUN QAYSI OBUNA ISHLATILADI?
            # =================================================
            #
            # Agar oddiy Subscription va DailySubscription
            # ikkalasi ham faol bo'lsa, muddati uzoqrog'i olinadi.
            #

            selected_subscription = None
            subscription_type = None

            if (
                subscription is not None
                and daily_subscription is not None
            ):

                subscription_end = (
                    subscription.end_date
                )

                if subscription_end.tzinfo is None:

                    subscription_end = (
                        subscription_end.replace(
                            tzinfo=timezone.utc
                        )
                    )

                daily_end = (
                    daily_subscription.end_date
                )

                if daily_end.tzinfo is None:

                    daily_end = (
                        daily_end.replace(
                            tzinfo=timezone.utc
                        )
                    )

                if subscription_end >= daily_end:

                    selected_subscription = (
                        subscription
                    )

                    subscription_type = (
                        "subscription"
                    )

                else:

                    selected_subscription = (
                        daily_subscription
                    )

                    subscription_type = (
                        "daily_subscription"
                    )

            elif subscription is not None:

                selected_subscription = (
                    subscription
                )

                subscription_type = (
                    "subscription"
                )

            elif daily_subscription is not None:

                selected_subscription = (
                    daily_subscription
                )

                subscription_type = (
                    "daily_subscription"
                )

            # =================================================
            # 5. FAOL OBUNA UMUMAN QOLMAGAN
            # =================================================

            if selected_subscription is None:

                print(
                    "VPN EXPIRY: "
                    f"{account.marzban_username} "
                    "uchun faol obuna qolmagan."
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

            # =================================================
            # 6. SUBSCRIPTION END DATE
            # =================================================

            end_date = (
                selected_subscription.end_date
            )

            if end_date.tzinfo is None:

                subscription_expire = (
                    end_date.replace(
                        tzinfo=timezone.utc
                    )
                )

            else:

                subscription_expire = end_date

            # Marzban sekund aniqligida ishlaydi.

            subscription_expire = (
                subscription_expire.replace(
                    microsecond=0
                )
            )

            # =================================================
            # 7. OBUNA MUDDATI TUGAGAN BO'LSA
            # =================================================

            if subscription_expire <= now:

                print(
                    "VPN EXPIRY: "
                    f"{account.marzban_username} "
                    "platforma obunasi muddati tugagan."
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

            # =================================================
            # 8. MARZBAN USERNI OLISH
            # =================================================

            marzban_user = (
                await marzban_service.get_user(
                    username=account.marzban_username,
                )
            )

            if marzban_user is None:

                print(
                    "VPN EXPIRY CHECK: "
                    "Marzban user topilmadi: "
                    f"{account.marzban_username}"
                )

                continue

            # =================================================
            # 9. MARZBAN EXPIRE
            # =================================================

            expire_timestamp = (
                marzban_user.get("expire")
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

            # =================================================
            # 10. MARZBANNI PLATFORMAGA SINXRONLASH
            # =================================================

            if expire_date != subscription_expire:

                print(
                    "VPN SYNC: "
                    f"{account.marzban_username} "
                    "Marzban expire yangilanmoqda."
                )

                print(
                    "VPN SYNC TYPE: "
                    f"{subscription_type}"
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

                # =================================================
                # 1. EXPIRED SUBSCRIPTIONLAR
                # =================================================

                expired_subscription_count = (
                    await check_expired_subscriptions(
                        session=session,
                    )
                )

                # =================================================
                # 2. SUBSCRIPTION REMINDER
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
                # 3. VPN ACCOUNT EXPIRY / SYNC
                # =================================================

                deactivated_count = (
                    await check_expired_vpn_accounts(
                        session=session,
                        bot=bot,
                    )
                )

                # =================================================
                # 4. DATABASE COMMIT
                # =================================================

                await session.commit()

                # =================================================
                # 5. LOG
                # =================================================

                if expired_subscription_count > 0:

                    print(
                        "SUBSCRIPTION EXPIRY: "
                        f"{expired_subscription_count} ta "
                        "obuna expired qilindi."
                    )

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
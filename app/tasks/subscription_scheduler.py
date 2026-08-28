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

            marzban_user = await marzban_service.get_user(
                username=account.marzban_username,
            )

            if marzban_user is None:
                print(
                    "VPN EXPIRY CHECK: "
                    f"Marzban user topilmadi: "
                    f"{account.marzban_username}"
                )
                continue

            expire_timestamp = marzban_user.get("expire")

            if expire_timestamp is None:
                continue

            expire_date = datetime.fromtimestamp(
                expire_timestamp,
                timezone.utc,
            )

            if expire_date > now:
                continue

            print(
                "VPN EXPIRY: "
                f"{account.marzban_username} muddati tugagan. "
                f"Expire: {expire_date.isoformat()}"
            )

            await vpn_account_service.deactivate_account(
                account_id=account.id,
            )

            deactivated_count += 1

            print(
                "VPN DEACTIVATED: "
                f"{account.marzban_username}"
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
                        f"deaktivatsiya qilindi."
                    )

        except Exception as e:

            print(
                "SUBSCRIPTION SCHEDULER ERROR:",
                repr(e),
            )

        await asyncio.sleep(60 * 60)
from __future__ import annotations

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.user_bonus_repository import UserBonusRepository
from app.services.service_access_service import ServiceAccessService
from app.services.vpn_account_service import VPNAccountService
from app.factories.marzban_factory import create_marzban_service
from app.utils.datetime import utc_now


class WelcomeTrafficMonitorService:
    """
    Monitors traffic usage of active Welcome Bonuses.

    Responsibilities:
    - Read current used_traffic from Marzban.
    - Store the Welcome traffic usage in BonusTraffic.
    - Send a one-time 500 MiB warning.
    - Expire Welcome immediately at the 3 GiB limit.
    - Reconcile the user's service queue so the next service starts
      immediately after Welcome traffic is exhausted.

    This service does not grant bonuses and does not decide business
    priorities. ServicePeriodService remains responsible for queue
    ordering and activation.
    """

    WARNING_BYTES = 500 * 1024 * 1024

    def __init__(
        self,
        session: AsyncSession,
        bot: Bot,
    ):
        self.bot = bot
        self.user_bonus_repository = UserBonusRepository(
            session
        )
        self.marzban_service = create_marzban_service()
        self.vpn_account_service = VPNAccountService(
            session=session,
            marzban_service=self.marzban_service,
        )
        self.service_access_service = ServiceAccessService(
            session
        )

    async def _send_message(
        self,
        telegram_id: int,
        text: str,
    ) -> None:
        try:
            await self.bot.send_message(
                chat_id=telegram_id,
                text=text,
            )
        except Exception as exc:
            print(
                "WELCOME TRAFFIC NOTIFICATION ERROR: "
                f"user={telegram_id} error={exc}"
            )

    async def _process_bonus(
        self,
        bonus,
    ) -> bool:
        """
        Process one active Welcome bonus.

        Returns True when the bonus became exhausted during this check.
        """
        traffic = bonus.traffic

        if traffic is None:
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} traffic record not found."
            )
            return False

        user = bonus.user

        if user is None:
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} user not found."
            )
            return False

        vpn_account = await self.vpn_account_service.get_existing(
            user_id=bonus.user_id,
            protocol="vless",
        )

        if vpn_account is None:
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} VPN account not found."
            )
            return False

        marzban_user = await self.marzban_service.get_user(
            username=vpn_account.marzban_username,
        )

        if marzban_user is None:
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} Marzban user not found."
            )
            return False

        used_traffic = marzban_user.get(
            "used_traffic",
            0,
        )

        if used_traffic is None:
            used_traffic = 0

        try:
            used_traffic = int(used_traffic)
        except (TypeError, ValueError):
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} invalid used_traffic="
                f"{used_traffic!r}"
            )
            return False

        if used_traffic < 0:
            used_traffic = 0

        limit = int(
            traffic.traffic_limit_bytes
        )

        if limit <= 0:
            print(
                "WELCOME TRAFFIC MONITOR: "
                f"bonus_id={bonus.id} invalid traffic limit."
            )
            return False

        stored_usage = min(
            used_traffic,
            limit,
        )

        if stored_usage > traffic.traffic_used_bytes:
            traffic.traffic_used_bytes = stored_usage

        telegram_id = user.telegram_id

        remaining_bytes = limit - stored_usage

        if (
            0 < remaining_bytes <= self.WARNING_BYTES
            and not traffic.warning_500mb_sent
        ):
            traffic.warning_500mb_sent = True

            await self._send_message(
                telegram_id=telegram_id,
                text=(
                    "⚠️ <b>Welcome Bonus trafik ogohlantirishi</b>\n\n"
                    "Welcome Bonus trafikining 500 MB yoki undan kam "
                    "qismi qoldi.\n\n"
                    f"📊 Qolgan: "
                    f"{remaining_bytes / (1024 * 1024):.0f} MB\n"
                    f"🎁 Limit: "
                    f"{limit / (1024 * 1024 * 1024):.0f} GB"
                ),
            )

        if stored_usage < limit:
            return False

        traffic.traffic_used_bytes = limit

        if traffic.exhausted_notified:
            return True

        traffic.exhausted_notified = True

        bonus.status = "expired"
        bonus.end_date = utc_now()

        await self._send_message(
            telegram_id=telegram_id,
            text=(
                "⛔ <b>Welcome Bonus trafik limiti tugadi</b>\n\n"
                "Sizga berilgan 3 GB Welcome Bonus trafik "
                "to'liq ishlatildi.\n\n"
                "🔄 Agar navbatda boshqa xizmat bo'lsa, u "
                "avtomatik ravishda ishga tushiriladi."
            ),
        )

        return True

    async def check_active_welcome_bonuses(self) -> int:
        """
        Check all currently active Welcome bonuses.

        Returns the number of bonuses that reached their traffic limit.
        """
        bonuses = (
            await self.user_bonus_repository.get_all_active_welcome()
        )

        exhausted_count = 0

        for bonus in bonuses:
            try:
                exhausted = await self._process_bonus(
                    bonus
                )

                if exhausted:
                    exhausted_count += 1
                    await self.service_access_service.sync_user(
                        user_id=bonus.user_id
                    )

            except Exception as exc:
                print(
                    "WELCOME TRAFFIC MONITOR ERROR: "
                    f"bonus_id={bonus.id} "
                    f"user_id={bonus.user_id} "
                    f"error={exc}"
                )

        return exhausted_count
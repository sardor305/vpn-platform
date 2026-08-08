from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support_message import SupportMessage


class SupportMessageRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_message(
        self,
        ticket_id: int,
        sender_id: int,
        sender_type: str,
        message: str,
    ) -> SupportMessage:

        support_message = SupportMessage(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message,
        )

        self.session.add(support_message)

        await self.session.flush()
        await self.session.refresh(support_message)

        return support_message

    async def get_by_id(
        self,
        message_id: int,
    ) -> SupportMessage | None:

        stmt = (
            select(SupportMessage)
            .where(
                SupportMessage.id == message_id
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_by_ticket_id(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        stmt = (
            select(SupportMessage)
            .where(
                SupportMessage.ticket_id == ticket_id
            )
            .order_by(
                SupportMessage.created_at.asc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_user_messages(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        stmt = (
            select(SupportMessage)
            .where(
                SupportMessage.ticket_id == ticket_id,
                SupportMessage.sender_type == "user",
            )
            .order_by(
                SupportMessage.created_at.asc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_admin_messages(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        stmt = (
            select(SupportMessage)
            .where(
                SupportMessage.ticket_id == ticket_id,
                SupportMessage.sender_type == "admin",
            )
            .order_by(
                SupportMessage.created_at.asc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())
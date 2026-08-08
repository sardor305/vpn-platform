from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support_message import SupportMessage
from app.repositories.support_message_repository import (
    SupportMessageRepository,
)


class SupportMessageService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.message_repository = SupportMessageRepository(
            session
        )

    async def create_message(
        self,
        ticket_id: int,
        sender_id: int,
        sender_type: str,
        message: str,
    ) -> SupportMessage:

        return await self.message_repository.create_message(
            ticket_id=ticket_id,
            sender_id=sender_id,
            sender_type=sender_type,
            message=message,
        )

    async def get_by_id(
        self,
        message_id: int,
    ) -> SupportMessage | None:

        return await self.message_repository.get_by_id(
            message_id
        )

    async def get_by_ticket_id(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        return await self.message_repository.get_by_ticket_id(
            ticket_id
        )

    async def get_user_messages(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        return await self.message_repository.get_user_messages(
            ticket_id
        )

    async def get_admin_messages(
        self,
        ticket_id: int,
    ) -> list[SupportMessage]:

        return await self.message_repository.get_admin_messages(
            ticket_id
        )
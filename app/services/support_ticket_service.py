from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support_ticket import SupportTicket
from app.repositories.support_ticket_repository import (
    SupportTicketRepository,
)
from app.utils.datetime import utc_now


class SupportTicketService:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.repository = SupportTicketRepository(
            session
        )

    async def create_ticket(
        self,
        user_id: int,
        message: str,
    ) -> SupportTicket:

        return await self.repository.create_ticket(
            user_id=user_id,
            message=message,
        )

    async def get_by_id(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        return await self.repository.get_by_id(
            ticket_id=ticket_id
        )

    async def get_user_tickets(
        self,
        user_id: int,
    ) -> list[SupportTicket]:

        return await self.repository.get_user_tickets(
            user_id=user_id
        )

    async def get_active_tickets(
        self,
    ) -> list[SupportTicket]:

        return await self.repository.get_active_tickets()

    async def get_new_tickets(
        self,
    ) -> list[SupportTicket]:

        return await self.repository.get_new_tickets()

    async def assign_admin(
        self,
        ticket_id: int,
        admin_id: int,
    ) -> SupportTicket | None:

        return await self.repository.assign_admin(
            ticket_id=ticket_id,
            admin_id=admin_id,
        )

    async def close_ticket(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        ticket = await self.repository.close_ticket(
            ticket_id=ticket_id
        )

        if ticket is not None:
            ticket.closed_at = utc_now()

        return ticket

    async def delete_ticket(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        ticket = await self.repository.delete_ticket(
            ticket_id=ticket_id
        )

        if ticket is not None:
            ticket.deleted_at = utc_now()

        return ticket
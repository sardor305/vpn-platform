from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.support_ticket import SupportTicket


class SupportTicketRepository:

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_ticket(
        self,
        user_id: int,
        message: str,
    ) -> SupportTicket:

        ticket = SupportTicket(
            user_id=user_id,
            message=message,
            status="new",
        )

        self.session.add(ticket)

        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket

    async def get_by_id(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.id == ticket_id
            )
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_user_tickets(
        self,
        user_id: int,
    ) -> list[SupportTicket]:

        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.user_id == user_id,
                SupportTicket.status != "deleted",
            )
            .order_by(
                SupportTicket.created_at.desc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_active_tickets(
        self,
    ) -> list[SupportTicket]:

        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.status != "deleted"
            )
            .order_by(
                SupportTicket.created_at.desc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_new_tickets(
        self,
    ) -> list[SupportTicket]:

        stmt = (
            select(SupportTicket)
            .where(
                SupportTicket.status == "new"
            )
            .order_by(
                SupportTicket.created_at.asc()
            )
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def assign_admin(
        self,
        ticket_id: int,
        admin_id: int,
    ) -> SupportTicket | None:

        ticket = await self.get_by_id(
            ticket_id
        )

        if ticket is None:
            return None

        ticket.admin_id = admin_id
        ticket.status = "open"

        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket

    async def close_ticket(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        ticket = await self.get_by_id(
            ticket_id
        )

        if ticket is None:
            return None

        ticket.status = "closed"

        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket

    async def delete_ticket(
        self,
        ticket_id: int,
    ) -> SupportTicket | None:

        ticket = await self.get_by_id(
            ticket_id
        )

        if ticket is None:
            return None

        ticket.status = "deleted"

        await self.session.flush()
        await self.session.refresh(ticket)

        return ticket
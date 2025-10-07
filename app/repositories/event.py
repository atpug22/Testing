from datetime import datetime, timedelta

from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import Event
from core.repository import BaseRepository


class EventRepository(BaseRepository[Event]):
    """
    Event repository provides all the database operations for the Event model.
    """

    async def get_by_team_member(
        self, team_member_id: int, limit: int = 50, join_: set[str] | None = None
    ) -> list[Event]:
        """
        Get events for a team member, ordered by timestamp desc.

        :param team_member_id: TeamMember ID.
        :param limit: Maximum number of events to return.
        :param join_: Join relations.
        :return: List of Events.
        """
        query = self._query(join_)
        query = query.filter(Event.team_member_id == team_member_id)
        query = query.order_by(Event.timestamp.desc())
        query = query.limit(limit)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def get_by_date_range(
        self,
        team_member_id: int,
        start_date: datetime,
        end_date: datetime,
        join_: set[str] | None = None,
    ) -> list[Event]:
        """
        Get events within a date range.

        :param team_member_id: TeamMember ID.
        :param start_date: Start date.
        :param end_date: End date.
        :param join_: Join relations.
        :return: List of Events.
        """
        query = self._query(join_)
        query = query.filter(
            Event.team_member_id == team_member_id,
            Event.timestamp >= start_date,
            Event.timestamp <= end_date,
        )
        query = query.order_by(Event.timestamp.desc())

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    async def get_recent_events(
        self, team_member_id: int, days: int = 7, join_: set[str] | None = None
    ) -> list[Event]:
        """
        Get recent events for the last N days.

        :param team_member_id: TeamMember ID.
        :param days: Number of days to look back.
        :param join_: Join relations.
        :return: List of Events.
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        return await self.get_by_date_range(team_member_id, start_date, end_date, join_)

    def _join_team_member(self, query: Select) -> Select:
        """Join team member."""
        return query.options(joinedload(Event.team_member))

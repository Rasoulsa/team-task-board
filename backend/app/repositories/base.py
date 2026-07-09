from operator import attrgetter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository[T]:
    model: type[T]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @property
    def id_column(self) -> Any:
        return attrgetter("id")(self.model)

    async def get_by_id(self, obj_id: Any) -> T | None:
        stmt = select(self.model).where(self.id_column == obj_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(self) -> list[T]:
        stmt = select(self.model).order_by(self.id_column)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T) -> T:
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: T) -> None:
        await self.session.delete(obj)
        await self.session.flush()

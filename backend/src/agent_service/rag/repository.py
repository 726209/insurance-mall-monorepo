# src/agent_service/rag/repository.py

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agent_service.rag.models import ParentChunk


class ParentChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def add_all(self, parent_chunks: list[ParentChunk]):
        self.session.add_all(parent_chunks)

    async def delete_by_product_id(self, product_id: int):
        # DELETE FROM parent_chunks WHERE product_id = 1
        await self.session.execute(delete(ParentChunk).where(ParentChunk.product_id == product_id))

    async def query_by_ids(self, ids: list[str]):
        # SELECT * FROM parent_chunks WHERE id IN (1, 2, 3)
        result = await self.session.scalars(select(ParentChunk).where(ParentChunk.id.in_(ids)))
        return result.all()

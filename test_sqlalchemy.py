from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("postgresql+asyncpg://postgres:ktoeto1243@localhost:5432/TutorBook")

async def test():
    async with engine.connect() as conn:
        result = await conn.execute("SELECT 1")
        print(result.scalar())

import asyncio
asyncio.run(test())
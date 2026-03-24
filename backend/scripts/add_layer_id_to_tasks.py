#!/usr/bin/env python3
"""
Add layer_id field to existing tasks (JSONB).
Run after creating the tasks table.
"""

import asyncio
import asyncpg
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            UPDATE tasks
            SET data = data || jsonb_build_object(
                'layerId', COALESCE(data->'layerId', 'core')
            )
            WHERE data ? 'id' AND NOT data ? 'layerId'
        """)
        print("Added layerId field to tasks.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

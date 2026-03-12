#!/usr/bin/env python3
"""
Remove the 'agent_ids' field from all hive JSON data.
Run once after deploying the new architecture.
"""

import asyncio
import json
import asyncpg
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Fetch all hives
        rows = await conn.fetch("SELECT id, data FROM hives")
        updated = 0
        for row in rows:
            hive_id = row['id']
            data = json.loads(row['data'])
            if 'agent_ids' in data:
                del data['agent_ids']
                await conn.execute(
                    "UPDATE hives SET data = $1 WHERE id = $2",
                    json.dumps(data), hive_id
                )
                updated += 1
        print(f"Removed agent_ids from {updated} hives.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

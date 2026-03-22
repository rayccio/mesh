#!/usr/bin/env python3
"""
Add new fields to existing tasks and artifacts (JSONB).
Run after create_layer_tables.py.
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
        # Update tasks: add loop_handler, project_id, sandbox_level if missing
        await conn.execute("""
            UPDATE tasks
            SET data = data || jsonb_build_object(
                'loopHandler', COALESCE(data->'loopHandler', null),
                'projectId', COALESCE(data->'projectId', null),
                'sandboxLevel', COALESCE(data->'sandboxLevel', 'task')
            )
            WHERE data ? 'id'
        """)
        print("Updated tasks with new fields.")

        # Update artifacts: add status, parent_artifact_id, layer_id if missing
        await conn.execute("""
            UPDATE artifacts
            SET data = data || jsonb_build_object(
                'status', COALESCE(data->'status', 'draft'),
                'parentArtifactId', COALESCE(data->'parentArtifactId', null),
                'layerId', COALESCE(data->'layerId', null)
            )
            WHERE data ? 'id'
        """)
        print("Updated artifacts with new fields.")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

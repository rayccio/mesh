#!/usr/bin/env python3
"""
Convert all JSON columns to JSONB in existing tables.
Run this once after updating the codebase.
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
        tables = [
            'agents', 'hives', 'tasks', 'skills', 'skill_versions',
            'users', 'global_settings', 'evaluation_tasks', 'goals', 'artifacts',
            'economy_accounts', 'transactions', 'strategies', 'risk_policies'
        ]
        for table in tables:
            # Check if table exists and column 'data' is of type json
            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = $1 AND column_name = 'data' AND data_type = 'json'
                )
            """, table)
            if result:
                print(f"Converting table {table}.data from json to jsonb...")
                await conn.execute(f"ALTER TABLE {table} ALTER COLUMN data TYPE jsonb USING data::jsonb")
                print(f"  Done.")
            else:
                print(f"Table {table}.data is already jsonb or not present.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

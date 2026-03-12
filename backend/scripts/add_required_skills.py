#!/usr/bin/env python3
"""
Add the required_skills column to the tasks table if it doesn't exist.
Run this after updating the codebase.
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
        # Check if column exists
        result = await conn.fetchrow("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tasks' AND column_name='required_skills'
        """)
        if not result:
            print("Adding column required_skills to tasks table...")
            await conn.execute("ALTER TABLE tasks ADD COLUMN required_skills JSON DEFAULT '[]'")
            print("Column added successfully.")
        else:
            print("Column required_skills already exists.")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

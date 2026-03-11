#!/usr/bin/env python3
"""
Seed the evaluation_tasks table with sample tasks for the meta‑agent.
Run this once after database migration.
"""

import asyncio
import json
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import os
import sys

# Adjust path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

DATABASE_URL = f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

SAMPLE_TASKS = [
    {
        "description": "Summarize the following text in one sentence: 'Artificial intelligence is transforming industries by automating routine tasks and enabling new levels of efficiency.'",
        "input_data": {},
        "tags": ["summarization", "nlp"]
    },
    {
        "description": "Calculate 15% of 234.",
        "input_data": {},
        "tags": ["math", "calculation"]
    },
    {
        "description": "Search the web for 'latest developments in quantum computing' and provide a brief summary.",
        "input_data": {},
        "tags": ["search", "research"]
    },
    {
        "description": "Write a short poem about a cat.",
        "input_data": {},
        "tags": ["creative", "writing"]
    },
    {
        "description": "Translate 'Hello, how are you?' into French.",
        "input_data": {},
        "tags": ["translation"]
    },
    {
        "description": "List three benefits of using Docker for development.",
        "input_data": {},
        "tags": ["devops", "knowledge"]
    },
    {
        "description": "Extract all email addresses from the following text: 'Contact us at info@example.com or support@hivebot.io for assistance.'",
        "input_data": {},
        "tags": ["extraction", "regex"]
    },
]

async def seed():
    async with AsyncSessionLocal() as session:
        for task in SAMPLE_TASKS:
            task_id = f"et-{uuid.uuid4().hex[:8]}"
            await session.execute(
                text("""
                    INSERT INTO evaluation_tasks (id, description, input_data, tags, active)
                    VALUES (:id, :description, :input_data, :tags, true)
                """),
                {
                    "id": task_id,
                    "description": task["description"],
                    "input_data": json.dumps(task["input_data"]),
                    "tags": json.dumps(task["tags"])
                }
            )
        await session.commit()
    print(f"Seeded {len(SAMPLE_TASKS)} evaluation tasks.")

if __name__ == "__main__":
    asyncio.run(seed())

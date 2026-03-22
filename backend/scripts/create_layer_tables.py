#!/usr/bin/env python3
"""
Create tables for the layered architecture: layers, layer_roles, layer_skills,
layer_configs, planner_templates, loop_handlers, projects.
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
        # layers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS layers (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                description TEXT,
                version VARCHAR NOT NULL,
                author VARCHAR,
                dependencies JSONB DEFAULT '[]',
                enabled BOOLEAN DEFAULT TRUE,
                lifecycle JSONB,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'layers' ensured.")

        # layer_roles table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS layer_roles (
                layer_id VARCHAR REFERENCES layers(id) ON DELETE CASCADE,
                role_name VARCHAR NOT NULL,
                soul_md TEXT NOT NULL,
                identity_md TEXT NOT NULL,
                tools_md TEXT NOT NULL,
                role_type VARCHAR DEFAULT 'specialized',
                priority INT DEFAULT 0,
                PRIMARY KEY (layer_id, role_name)
            )
        """)
        print("Table 'layer_roles' ensured.")

        # layer_skills table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS layer_skills (
                layer_id VARCHAR REFERENCES layers(id) ON DELETE CASCADE,
                skill_id VARCHAR REFERENCES skills(id) ON DELETE CASCADE,
                PRIMARY KEY (layer_id, skill_id)
            )
        """)
        print("Table 'layer_skills' ensured.")

        # layer_configs table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS layer_configs (
                id VARCHAR PRIMARY KEY,
                layer_id VARCHAR REFERENCES layers(id) ON DELETE CASCADE,
                hive_id VARCHAR REFERENCES hives(id) ON DELETE CASCADE,
                config_data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'layer_configs' ensured.")

        # planner_templates table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS planner_templates (
                id VARCHAR PRIMARY KEY,
                layer_id VARCHAR REFERENCES layers(id) ON DELETE CASCADE,
                goal_pattern TEXT,
                template TEXT,
                priority INT DEFAULT 0
            )
        """)
        print("Table 'planner_templates' ensured.")

        # loop_handlers table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS loop_handlers (
                id VARCHAR PRIMARY KEY,
                layer_id VARCHAR REFERENCES layers(id) ON DELETE CASCADE,
                name VARCHAR NOT NULL,
                class_path VARCHAR NOT NULL
            )
        """)
        print("Table 'loop_handlers' ensured.")

        # projects table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id VARCHAR PRIMARY KEY,
                hive_id VARCHAR NOT NULL REFERENCES hives(id),
                name VARCHAR NOT NULL,
                description TEXT,
                goal VARCHAR NOT NULL,
                root_goal_id VARCHAR REFERENCES goals(id),
                state VARCHAR DEFAULT 'active',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'projects' ensured.")

        # Add foreign key to tasks and artifacts later
        # Already done in update_tasks_artifacts.py

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

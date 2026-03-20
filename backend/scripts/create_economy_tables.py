#!/usr/bin/env python3
"""
Create economy tables: economy_accounts, transactions, strategies, risk_policies.
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
        # Create economy_accounts table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS economy_accounts (
                id VARCHAR PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'economy_accounts' ensured.")

        # Create transactions table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id VARCHAR PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'transactions' ensured.")

        # Create strategies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS strategies (
                id VARCHAR PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'strategies' ensured.")

        # Create risk_policies table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_policies (
                id VARCHAR PRIMARY KEY,
                data JSONB NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        print("Table 'risk_policies' ensured.")

        # Ensure existing tables have jsonb
        for table in ['economy_accounts', 'transactions', 'strategies', 'risk_policies']:
            await conn.execute(f"""
                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name='{table}' AND column_name='data' AND data_type='json'
                    ) THEN
                        ALTER TABLE {table} ALTER COLUMN data TYPE jsonb USING data::jsonb;
                    END IF;
                END
                $$;
            """)
        print("Checked/updated economy tables to jsonb.")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

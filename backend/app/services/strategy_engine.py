import uuid
import asyncio
import random
from datetime import datetime
from typing import Optional, List
from sqlalchemy import text
from ..core.database import AsyncSessionLocal
from ..models.types import Strategy, StrategyType, AccountType
import logging

logger = logging.getLogger(__name__)

class StrategyEngine:
    """Executes trading/growth strategies."""

    async def create_strategy(self, name: str, type: StrategyType, owner_id: str, owner_type: AccountType, config: dict = None) -> Strategy:
        strat_id = f"strat-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        strategy = Strategy(
            id=strat_id,
            name=name,
            type=type,
            owner_id=owner_id,
            owner_type=owner_type,
            config=config or {},
            active=True,
            last_run=None,
            created_at=now,
            updated_at=now
        )
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("INSERT INTO strategies (id, data) VALUES (:id, :data)"),
                {"id": strat_id, "data": strategy.model_dump_json()}
            )
            await session.commit()
        logger.info(f"Created strategy {strat_id} for {owner_type} {owner_id}")
        return strategy

    async def get_strategy(self, strat_id: str) -> Optional[Strategy]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT data FROM strategies WHERE id = :id"),
                {"id": strat_id}
            )
            row = result.fetchone()
            if row:
                return Strategy.model_validate_json(row[0])
        return None

    async def list_strategies(self, owner_id: Optional[str] = None, owner_type: Optional[AccountType] = None) -> List[Strategy]:
        async with AsyncSessionLocal() as session:
            if owner_id and owner_type:
                result = await session.execute(
                    text("SELECT data FROM strategies WHERE data->>'owner_id' = :owner_id AND data->>'owner_type' = :owner_type"),
                    {"owner_id": owner_id, "owner_type": owner_type.value}
                )
            else:
                result = await session.execute(text("SELECT data FROM strategies"))
            rows = result.fetchall()
            return [Strategy.model_validate_json(r[0]) for r in rows]

    async def update_strategy(self, strat_id: str, **updates) -> Optional[Strategy]:
        strat = await self.get_strategy(strat_id)
        if not strat:
            return None
        for k, v in updates.items():
            if hasattr(strat, k):
                setattr(strat, k, v)
        strat.updated_at = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE strategies SET data = :data WHERE id = :id"),
                {"data": strat.model_dump_json(), "id": strat_id}
            )
            await session.commit()
        return strat

    async def execute_strategy(self, strat_id: str) -> dict:
        """Simulate strategy execution. Returns result dict."""
        strat = await self.get_strategy(strat_id)
        if not strat or not strat.active:
            return {"error": "Strategy not found or inactive"}

        # Simulate different strategy behaviors
        if strat.type == StrategyType.TRADING:
            # Random profit/loss
            pnl = random.uniform(-10, 10)
            strat.last_run = datetime.utcnow()
            await self.update_strategy(strat_id, last_run=strat.last_run)
            return {
                "strategy_id": strat_id,
                "type": "trading",
                "pnl": round(pnl, 2),
                "timestamp": strat.last_run.isoformat()
            }
        elif strat.type == StrategyType.GROWTH:
            # Simulate growth (e.g., staking rewards)
            growth = random.uniform(0.5, 2.0)
            strat.last_run = datetime.utcnow()
            await self.update_strategy(strat_id, last_run=strat.last_run)
            return {
                "strategy_id": strat_id,
                "type": "growth",
                "growth": round(growth, 2),
                "timestamp": strat.last_run.isoformat()
            }
        elif strat.type == StrategyType.OPTIMIZATION:
            # Simulate cost reduction
            saved = random.uniform(1, 5)
            strat.last_run = datetime.utcnow()
            await self.update_strategy(strat_id, last_run=strat.last_run)
            return {
                "strategy_id": strat_id,
                "type": "optimization",
                "saved": round(saved, 2),
                "timestamp": strat.last_run.isoformat()
            }
        else:
            return {"error": "Unknown strategy type"}

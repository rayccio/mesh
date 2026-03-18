import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.strategy_engine import StrategyEngine
from app.models.types import StrategyType, AccountType
from datetime import datetime
import json

@pytest.mark.asyncio
async def test_create_strategy():
    engine = StrategyEngine()
    with patch('app.services.strategy_engine.AsyncSessionLocal') as mock_session:
        mock_conn = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        strat = await engine.create_strategy(
            name="Test Strategy",
            type=StrategyType.TRADING,
            owner_id="owner1",
            owner_type=AccountType.HIVE,
            config={"param": 1}
        )
        assert strat.id.startswith("strat-")
        assert strat.name == "Test Strategy"
        assert strat.type == StrategyType.TRADING
        mock_conn.execute.assert_awaited_once()
        mock_conn.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_execute_strategy_trading():
    engine = StrategyEngine()
    mock_strat = MagicMock()
    mock_strat.id = "strat-123"
    mock_strat.type = StrategyType.TRADING
    mock_strat.active = True
    mock_strat.last_run = None
    with patch.object(engine, 'get_strategy', return_value=mock_strat), \
         patch.object(engine, 'update_strategy', new_callable=AsyncMock) as mock_update:

        result = await engine.execute_strategy("strat-123")
        assert "pnl" in result
        assert result["strategy_id"] == "strat-123"
        mock_update.assert_awaited_once()

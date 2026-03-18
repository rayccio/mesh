import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.risk_manager import RiskManager
from app.models.types import AccountType, RiskPolicy, EconomyAccount, TransactionType, Transaction
from datetime import datetime, timedelta
import json

@pytest.mark.asyncio
async def test_check_trade_allowed_no_policy():
    risk = RiskManager()
    account = EconomyAccount(
        id="acc-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        currency="sim",
        balance=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    with patch.object(risk, 'get_policy', return_value=None):
        allowed, msg = await risk.check_trade_allowed(account, -10)
        assert allowed is True
        assert msg == "No policy"

@pytest.mark.asyncio
async def test_check_trade_allowed_kill_switch():
    risk = RiskManager()
    account = EconomyAccount(
        id="acc-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        currency="sim",
        balance=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    policy = RiskPolicy(
        id="pol-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        kill_switch_enabled=True,
        kill_switch_triggered=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    with patch.object(risk, 'get_policy', return_value=policy):
        allowed, msg = await risk.check_trade_allowed(account, -10)
        assert allowed is False
        assert "Kill switch triggered" in msg

@pytest.mark.asyncio
async def test_check_trade_allowed_max_loss():
    risk = RiskManager()
    account = EconomyAccount(
        id="acc-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        currency="sim",
        balance=100,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    policy = RiskPolicy(
        id="pol-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        max_loss_per_trade=5,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    with patch.object(risk, 'get_policy', return_value=policy):
        allowed, msg = await risk.check_trade_allowed(account, -10)
        assert allowed is False
        assert "Loss exceeds max per trade" in msg

@pytest.mark.asyncio
async def test_trigger_kill_switch():
    risk = RiskManager()
    policy = RiskPolicy(
        id="pol-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        kill_switch_enabled=True,
        kill_switch_triggered=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    with patch.object(risk, 'get_policy', return_value=policy), \
         patch('app.services.risk_manager.AsyncSessionLocal') as mock_session:

        mock_conn = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_conn
        mock_conn.execute = AsyncMock()
        mock_conn.commit = AsyncMock()

        result = await risk.trigger_kill_switch("owner1", AccountType.HIVE)
        assert result is True
        assert policy.kill_switch_triggered is True
        mock_conn.execute.assert_awaited_once()
        mock_conn.commit.assert_awaited_once()

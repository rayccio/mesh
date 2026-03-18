import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app as fastapi_app
from app.models.types import EconomyAccount, AccountType, Currency, Transaction, TransactionType, TransactionStatus, Strategy, StrategyType, RiskPolicy
from datetime import datetime
import json

# Import dependency functions to override
from app.api.v1.endpoints.economy import get_economy_engine, get_risk_manager, get_strategy_engine

@pytest.mark.asyncio
async def test_create_account_api(client: AsyncClient):
    mock_econ = AsyncMock()
    mock_account = EconomyAccount(
        id="acc-123",
        owner_id="owner1",
        owner_type=AccountType.HIVE,
        currency=Currency.SIM,
        balance=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    mock_econ.create_account.return_value = mock_account
    mock_econ.get_account_by_owner.return_value = None

    fastapi_app.dependency_overrides[get_economy_engine] = lambda: mock_econ

    payload = {
        "owner_id": "owner1",
        "owner_type": "hive",
        "currency": "sim"
    }
    response = await client.post("/api/v1/economy/accounts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "acc-123"
    assert data["owner_id"] == "owner1"

    fastapi_app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_transfer_api(client: AsyncClient):
    mock_econ = AsyncMock()
    mock_risk = AsyncMock()
    mock_tx = Transaction(
        id="tx-123",
        account_id="from",
        type=TransactionType.TRANSFER,
        amount=50,
        currency=Currency.SIM,
        status=TransactionStatus.COMPLETED,
        created_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    mock_econ.transfer.return_value = mock_tx
    mock_econ.get_account.return_value = MagicMock()
    mock_risk.check_trade_allowed.return_value = (True, "OK")

    fastapi_app.dependency_overrides[get_economy_engine] = lambda: mock_econ
    fastapi_app.dependency_overrides[get_risk_manager] = lambda: mock_risk

    payload = {
        "from_account": "from",
        "to_account": "to",
        "amount": 50,
        "description": "test"
    }
    response = await client.post("/api/v1/economy/transactions/transfer", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "tx-123"

    fastapi_app.dependency_overrides.clear()

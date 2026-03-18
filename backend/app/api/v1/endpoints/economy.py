from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from ....services.economy_engine import EconomyEngine
from ....services.risk_manager import RiskManager
from ....services.strategy_engine import StrategyEngine
from ....models.types import (
    EconomyAccount, Transaction, TransactionType, TransactionStatus, Currency,
    Strategy, StrategyType, AccountType, RiskPolicy
)
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/economy", tags=["economy"])

# ----- Dependencies -----
async def get_economy_engine():
    return EconomyEngine()

async def get_risk_manager():
    return RiskManager()

async def get_strategy_engine():
    return StrategyEngine()

# ----- Request/Response Models -----
class CreateAccountRequest(BaseModel):
    owner_id: str
    owner_type: AccountType
    currency: Currency = Currency.SIM

class TransferRequest(BaseModel):
    from_account: str
    to_account: str
    amount: float
    description: Optional[str] = None

class CreateStrategyRequest(BaseModel):
    name: str
    type: StrategyType
    owner_id: str
    owner_type: AccountType
    config: dict = {}

class CreatePolicyRequest(BaseModel):
    owner_id: str
    owner_type: AccountType
    max_loss_per_trade: float = 0.0
    max_daily_loss: float = 0.0
    max_position_size: float = 0.0
    kill_switch_enabled: bool = False

class ExecuteStrategyRequest(BaseModel):
    strategy_id: str

# ----- Account Endpoints -----
@router.post("/accounts", response_model=EconomyAccount)
async def create_account(
    req: CreateAccountRequest,
    econ: EconomyEngine = Depends(get_economy_engine)
):
    # Check if account already exists
    existing = await econ.get_account_by_owner(req.owner_id, req.owner_type)
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists")
    account = await econ.create_account(req.owner_id, req.owner_type, req.currency)
    return account

@router.get("/accounts", response_model=List[EconomyAccount])
async def list_accounts(
    owner_type: Optional[AccountType] = Query(None),
    econ: EconomyEngine = Depends(get_economy_engine)
):
    return await econ.list_accounts(owner_type)

@router.get("/accounts/{account_id}", response_model=EconomyAccount)
async def get_account(
    account_id: str,
    econ: EconomyEngine = Depends(get_economy_engine)
):
    account = await econ.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

# ----- Transaction Endpoints -----
@router.post("/transactions/transfer", response_model=Transaction)
async def transfer(
    req: TransferRequest,
    econ: EconomyEngine = Depends(get_economy_engine),
    risk: RiskManager = Depends(get_risk_manager)
):
    # Check source account
    from_acc = await econ.get_account(req.from_account)
    if not from_acc:
        raise HTTPException(status_code=404, detail="Source account not found")
    # Check risk policy
    allowed, msg = await risk.check_trade_allowed(from_acc, -req.amount)
    if not allowed:
        raise HTTPException(status_code=400, detail=f"Transfer not allowed: {msg}")
    # Perform transfer
    tx = await econ.transfer(req.from_account, req.to_account, req.amount, req.description)
    if not tx:
        raise HTTPException(status_code=400, detail="Transfer failed (insufficient funds or invalid accounts)")
    return tx

@router.get("/transactions", response_model=List[Transaction])
async def list_transactions(
    account_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    econ: EconomyEngine = Depends(get_economy_engine)
):
    return await econ.list_transactions(account_id, limit)

@router.get("/transactions/{tx_id}", response_model=Transaction)
async def get_transaction(
    tx_id: str,
    econ: EconomyEngine = Depends(get_economy_engine)
):
    # Since we don't have a direct get, we'll list and filter
    txs = await econ.list_transactions(limit=1000)
    for tx in txs:
        if tx.id == tx_id:
            return tx
    raise HTTPException(status_code=404, detail="Transaction not found")

# ----- Strategy Endpoints -----
@router.post("/strategies", response_model=Strategy)
async def create_strategy(
    req: CreateStrategyRequest,
    strat_engine: StrategyEngine = Depends(get_strategy_engine)
):
    strategy = await strat_engine.create_strategy(
        name=req.name,
        type=req.type,
        owner_id=req.owner_id,
        owner_type=req.owner_type,
        config=req.config
    )
    return strategy

@router.get("/strategies", response_model=List[Strategy])
async def list_strategies(
    owner_id: Optional[str] = Query(None),
    owner_type: Optional[AccountType] = Query(None),
    strat_engine: StrategyEngine = Depends(get_strategy_engine)
):
    return await strat_engine.list_strategies(owner_id, owner_type)

@router.get("/strategies/{strategy_id}", response_model=Strategy)
async def get_strategy(
    strategy_id: str,
    strat_engine: StrategyEngine = Depends(get_strategy_engine)
):
    strat = await strat_engine.get_strategy(strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strat

@router.post("/strategies/{strategy_id}/execute")
async def execute_strategy(
    strategy_id: str,
    strat_engine: StrategyEngine = Depends(get_strategy_engine)
):
    result = await strat_engine.execute_strategy(strategy_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# ----- Risk Policy Endpoints -----
@router.post("/policies", response_model=RiskPolicy)
async def create_policy(
    req: CreatePolicyRequest,
    risk: RiskManager = Depends(get_risk_manager)
):
    # Check if policy already exists
    existing = await risk.get_policy(req.owner_id, req.owner_type)
    if existing:
        raise HTTPException(status_code=400, detail="Policy already exists")
    policy = await risk.create_policy(
        owner_id=req.owner_id,
        owner_type=req.owner_type,
        max_loss_per_trade=req.max_loss_per_trade,
        max_daily_loss=req.max_daily_loss,
        max_position_size=req.max_position_size,
        kill_switch_enabled=req.kill_switch_enabled
    )
    return policy

@router.get("/policies/{owner_id}", response_model=RiskPolicy)
async def get_policy(
    owner_id: str,
    owner_type: AccountType = Query(...),
    risk: RiskManager = Depends(get_risk_manager)
):
    policy = await risk.get_policy(owner_id, owner_type)
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy

@router.post("/policies/{owner_id}/trigger-kill-switch")
async def trigger_kill_switch(
    owner_id: str,
    owner_type: AccountType = Query(...),
    risk: RiskManager = Depends(get_risk_manager)
):
    triggered = await risk.trigger_kill_switch(owner_id, owner_type)
    if not triggered:
        raise HTTPException(status_code=400, detail="Kill switch not enabled or already triggered")
    return {"status": "kill switch triggered"}

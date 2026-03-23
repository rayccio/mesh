import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from ..core.database import AsyncSessionLocal
from ..models.types import EconomyAccount, Transaction, TransactionType, TransactionStatus, Currency, AccountType
import logging

logger = logging.getLogger(__name__)

class EconomyEngine:
    """Manages financial accounts and transactions."""

    async def create_account(self, owner_id: str, owner_type: AccountType, currency: Currency = Currency.SIM) -> EconomyAccount:
        """Create a new economy account."""
        account_id = f"acc-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        account = EconomyAccount(
            id=account_id,
            owner_id=owner_id,
            owner_type=owner_type,
            currency=currency,
            balance=0.0,
            created_at=now,
            updated_at=now
        )
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("INSERT INTO economy_accounts (id, data) VALUES (:id, :data)"),
                {"id": account_id, "data": account.model_dump_json()}
            )
            await session.commit()
        logger.info(f"Created economy account {account_id} for {owner_type} {owner_id}")
        return account

    async def get_account(self, account_id: str) -> Optional[EconomyAccount]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT data FROM economy_accounts WHERE id = :id"),
                {"id": account_id}
            )
            row = result.fetchone()
            if row:
                return EconomyAccount.model_validate_json(row[0])
        return None

    async def get_account_by_owner(self, owner_id: str, owner_type: AccountType) -> Optional[EconomyAccount]:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT data FROM economy_accounts WHERE data->>'owner_id' = :owner_id AND data->>'owner_type' = :owner_type"),
                {"owner_id": owner_id, "owner_type": owner_type.value}
            )
            row = result.fetchone()
            if row:
                return EconomyAccount.model_validate_json(row[0])
        return None

    async def list_accounts(self, owner_type: Optional[AccountType] = None) -> List[EconomyAccount]:
        async with AsyncSessionLocal() as session:
            if owner_type:
                result = await session.execute(
                    text("SELECT data FROM economy_accounts WHERE data->>'owner_type' = :owner_type"),
                    {"owner_type": owner_type.value}
                )
            else:
                result = await session.execute(text("SELECT data FROM economy_accounts"))
            rows = result.fetchall()
            return [EconomyAccount.model_validate_json(r[0]) for r in rows]

    async def update_balance(self, account_id: str, delta: float) -> Optional[EconomyAccount]:
        """Add delta to balance (can be negative). Returns updated account or None if insufficient funds."""
        account = await self.get_account(account_id)
        if not account:
            return None
        new_balance = account.balance + delta
        if new_balance < 0:
            return None  # insufficient funds
        account.balance = new_balance
        account.updated_at = datetime.utcnow()
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("UPDATE economy_accounts SET data = :data WHERE id = :id"),
                {"data": account.model_dump_json(), "id": account_id}
            )
            await session.commit()
        logger.info(f"Updated account {account_id} balance by {delta} to {new_balance}")
        return account

    async def create_transaction(
        self,
        account_id: str,
        type: TransactionType,
        amount: float,
        currency: Currency,
        description: Optional[str] = None,
        metadata: dict = None
    ) -> Transaction:
        """Create a transaction record (does not affect balance)."""
        tx_id = f"tx-{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow()
        transaction = Transaction(
            id=tx_id,
            account_id=account_id,
            type=type,
            amount=amount,
            currency=currency,
            status=TransactionStatus.PENDING,
            description=description,
            metadata=metadata or {},
            created_at=now,
            completed_at=None
        )
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("INSERT INTO transactions (id, data) VALUES (:id, :data)"),
                {"id": tx_id, "data": transaction.model_dump_json()}
            )
            await session.commit()
        return transaction

    async def complete_transaction(self, tx_id: str, success: bool = True) -> Optional[Transaction]:
        """Mark transaction as completed or failed."""
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT data FROM transactions WHERE id = :id"),
                {"id": tx_id}
            )
            row = result.fetchone()
            if not row:
                return None
            tx = Transaction.model_validate_json(row[0])
            tx.status = TransactionStatus.COMPLETED if success else TransactionStatus.FAILED
            tx.completed_at = datetime.utcnow()
            await session.execute(
                text("UPDATE transactions SET data = :data WHERE id = :id"),
                {"data": tx.model_dump_json(), "id": tx_id}
            )
            await session.commit()
        return tx

    async def list_transactions(self, account_id: Optional[str] = None, limit: int = 100) -> List[Transaction]:
        async with AsyncSessionLocal() as session:
            if account_id:
                result = await session.execute(
                    text("SELECT data FROM transactions WHERE data->>'account_id' = :account_id ORDER BY (data->>'created_at')::timestamptz DESC LIMIT :limit"),
                    {"account_id": account_id, "limit": limit}
                )
            else:
                result = await session.execute(
                    text("SELECT data FROM transactions ORDER BY (data->>'created_at')::timestamptz DESC LIMIT :limit"),
                    {"limit": limit}
                )
            rows = result.fetchall()
            return [Transaction.model_validate_json(r[0]) for r in rows]

    async def transfer(self, from_account_id: str, to_account_id: str, amount: float, description: Optional[str] = None) -> Optional[Transaction]:
        """Transfer funds between two accounts. Returns the transfer transaction if successful."""
        # Check both accounts exist
        from_acc = await self.get_account(from_account_id)
        to_acc = await self.get_account(to_account_id)
        if not from_acc or not to_acc:
            return None
        if from_acc.currency != to_acc.currency:
            logger.warning(f"Currency mismatch: {from_acc.currency} vs {to_acc.currency}")
            return None

        # Create pending transaction
        tx = await self.create_transaction(
            account_id=from_account_id,
            type=TransactionType.TRANSFER,
            amount=amount,
            currency=from_acc.currency,
            description=description,
            metadata={"to_account": to_account_id}
        )

        # Deduct from source
        updated_from = await self.update_balance(from_account_id, -amount)
        if not updated_from:
            # Insufficient funds
            await self.complete_transaction(tx.id, success=False)
            return None

        # Add to destination
        await self.update_balance(to_account_id, amount)

        # Mark transaction completed
        await self.complete_transaction(tx.id, success=True)
        return tx

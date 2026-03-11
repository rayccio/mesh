import json
import os
from typing import Dict, Optional, List
from datetime import datetime
from ..models.types import UserAccount, UserCreate, UserUpdate, UserRole
from ..core.config import settings
from ..core.database import AsyncSessionLocal
from ..repositories.user_repository import UserRepository
import uuid
import logging
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserManager:
    def __init__(self):
        self.repo = UserRepository

    async def _get_repo(self):
        session = AsyncSessionLocal()
        return UserRepository(session), session

    def hash_password(self, password: str) -> str:
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    async def create_user(self, user_in: UserCreate) -> UserAccount:
        user_id = f"u-{uuid.uuid4().hex[:4]}"
        now = datetime.utcnow()
        user = UserAccount(
            id=user_id,
            username=user_in.username,
            password_hash=self.hash_password(user_in.password),
            role=user_in.role,
            assigned_hive_ids=user_in.assigned_hive_ids,
            password_changed=False,
            created_at=now,
            updated_at=now
        )
        repo, session = await self._get_repo()
        try:
            created = await repo.create(user)
        finally:
            await session.close()
        logger.info(f"Created user {user_id}")
        return created

    async def get_user(self, user_id: str) -> Optional[UserAccount]:
        repo, session = await self._get_repo()
        try:
            return await repo.get(user_id)
        finally:
            await session.close()

    async def get_user_by_username(self, username: str) -> Optional[UserAccount]:
        repo, session = await self._get_repo()
        try:
            users = await repo.get_all()
            for u in users:
                if u.username == username:
                    return u
            return None
        finally:
            await session.close()

    async def list_users(self) -> List[UserAccount]:
        repo, session = await self._get_repo()
        try:
            return await repo.get_all()
        finally:
            await session.close()

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserAccount]:
        repo, session = await self._get_repo()
        try:
            user = await repo.get(user_id)
            if not user:
                return None
            update_data = user_update.dict(exclude_unset=True)
            if "password" in update_data:
                user.password_hash = self.hash_password(update_data.pop("password"))
                user.password_changed = True
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            user.updated_at = datetime.utcnow()
            await repo.update(user_id, user.dict(by_alias=True))
            return user
        finally:
            await session.close()

    async def delete_user(self, user_id: str) -> bool:
        repo, session = await self._get_repo()
        try:
            return await repo.delete(user_id)
        finally:
            await session.close()

    async def authenticate_user(self, username: str, password: str) -> Optional[UserAccount]:
        user = await self.get_user_by_username(username)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user

    async def update_last_login(self, user_id: str):
        repo, session = await self._get_repo()
        try:
            user = await repo.get(user_id)
            if user:
                user.last_login = datetime.utcnow()
                await repo.update(user_id, user.dict(by_alias=True))
        finally:
            await session.close()

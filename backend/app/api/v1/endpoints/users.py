from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ....services.user_manager import UserManager
from ....models.types import UserAccount, UserCreate, UserUpdate, UserRole, GlobalSettings
from ....core.config import settings
from .auth import get_current_user, require_global_admin

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=List[UserAccount])
async def list_users(
    admin = Depends(require_global_admin)
):
    user_manager = UserManager()
    return await user_manager.list_users()

@router.post("", response_model=UserAccount)
async def create_user(
    user_in: UserCreate,
    admin = Depends(require_global_admin)
):
    user_manager = UserManager()
    existing = await user_manager.get_user_by_username(user_in.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Load global settings
    global_settings_data = settings.secrets.get("GLOBAL_SETTINGS")
    if global_settings_data:
        global_settings = GlobalSettings(**global_settings_data)
    else:
        global_settings = GlobalSettings()
    
    # If gateway is disabled, require admin to have changed password before creating a user
    if not global_settings.login_enabled:
        admin_user = await user_manager.get_user(admin.id)
        if not admin_user.password_changed:
            raise HTTPException(
                status_code=400,
                detail="Admin must change password before creating users."
            )
    
    # Create the user
    user = await user_manager.create_user(user_in)
    
    # If gateway was disabled, automatically enable it after user creation
    if not global_settings.login_enabled:
        global_settings.login_enabled = True
        settings.secrets.set("GLOBAL_SETTINGS", global_settings.dict())
    
    return user

@router.get("/{user_id}", response_model=UserAccount)
async def get_user(
    user_id: str,
    admin = Depends(require_global_admin)
):
    user_manager = UserManager()
    user = await user_manager.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.patch("/{user_id}", response_model=UserAccount)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    admin = Depends(require_global_admin)
):
    user_manager = UserManager()
    user = await user_manager.update_user(user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    admin = Depends(require_global_admin)
):
    user_manager = UserManager()
    deleted = await user_manager.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List
from pydantic import BaseModel
from ....core.database import get_db
from ....models.types import Layer, LayerRole, LayerSkill
from .auth import get_current_user

router = APIRouter(prefix="/layers", tags=["layers"])

# Response models (simpler than full models for brevity)
class LayerResponse(BaseModel):
    id: str
    name: str
    description: str
    version: str
    author: str | None
    dependencies: List[str]
    enabled: bool
    created_at: str
    updated_at: str

class LayerRoleResponse(BaseModel):
    layer_id: str
    role_name: str
    soul_md: str
    identity_md: str
    tools_md: str
    role_type: str
    priority: int

class LayerSkillResponse(BaseModel):
    layer_id: str
    skill_id: str
    skill_name: str
    skill_description: str
    skill_type: str


@router.get("", response_model=List[LayerResponse])
async def list_layers(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List all installed layers."""
    result = await db.execute(
        text("SELECT id, name, description, version, author, dependencies, enabled, created_at, updated_at FROM layers ORDER BY created_at")
    )
    rows = result.fetchall()
    layers = []
    for r in rows:
        layers.append(LayerResponse(
            id=r[0],
            name=r[1],
            description=r[2],
            version=r[3],
            author=r[4],
            dependencies=r[5] or [],
            enabled=r[6],
            created_at=r[7].isoformat(),
            updated_at=r[8].isoformat()
        ))
    return layers


@router.get("/{layer_id}/roles", response_model=List[LayerRoleResponse])
async def list_layer_roles(
    layer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List roles defined in a layer."""
    result = await db.execute(
        text("SELECT layer_id, role_name, soul_md, identity_md, tools_md, role_type, priority FROM layer_roles WHERE layer_id = :layer_id ORDER BY priority DESC"),
        {"layer_id": layer_id}
    )
    rows = result.fetchall()
    if not rows:
        # Check if layer exists
        exists = await db.execute(text("SELECT 1 FROM layers WHERE id = :layer_id"), {"layer_id": layer_id})
        if not exists.fetchone():
            raise HTTPException(status_code=404, detail="Layer not found")
        # If layer exists but no roles, return empty list
        return []
    roles = []
    for r in rows:
        roles.append(LayerRoleResponse(
            layer_id=r[0],
            role_name=r[1],
            soul_md=r[2],
            identity_md=r[3],
            tools_md=r[4],
            role_type=r[5],
            priority=r[6]
        ))
    return roles


@router.get("/{layer_id}/skills", response_model=List[LayerSkillResponse])
async def list_layer_skills(
    layer_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """List skills provided by a layer."""
    result = await db.execute(
        text("""
            SELECT ls.layer_id, s.id, s.data->>'name' as skill_name, s.data->>'description' as skill_description, s.data->>'type' as skill_type
            FROM layer_skills ls
            JOIN skills s ON ls.skill_id = s.id
            WHERE ls.layer_id = :layer_id
        """),
        {"layer_id": layer_id}
    )
    rows = result.fetchall()
    if not rows:
        # Check if layer exists
        exists = await db.execute(text("SELECT 1 FROM layers WHERE id = :layer_id"), {"layer_id": layer_id})
        if not exists.fetchone():
            raise HTTPException(status_code=404, detail="Layer not found")
        return []
    skills = []
    for r in rows:
        skills.append(LayerSkillResponse(
            layer_id=r[0],
            skill_id=r[1],
            skill_name=r[2],
            skill_description=r[3] or "",
            skill_type=r[4] or "tool"
        ))
    return skills

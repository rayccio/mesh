from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ....core.database import get_db
from ....models.db_models import EvaluationTaskModel
from pydantic import BaseModel
import json
import uuid

router = APIRouter(prefix="/evaluation", tags=["evaluation"])

class EvaluationTaskResponse(BaseModel):
    id: str
    description: str
    input_data: dict
    tags: List[str]

@router.get("/tasks", response_model=List[EvaluationTaskResponse])
async def get_evaluation_tasks(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get random evaluation tasks for meta-agent testing."""
    result = await db.execute(
        select(EvaluationTaskModel).where(EvaluationTaskModel.active == True).order_by(func.random()).limit(limit)
    )
    tasks = result.scalars().all()
    return [
        EvaluationTaskResponse(
            id=t.id,
            description=t.description,
            input_data=t.input_data,
            tags=t.tags
        ) for t in tasks
    ]

@router.post("/tasks")
async def create_evaluation_task(
    description: str,
    input_data: dict = {},
    tags: List[str] = [],
    db: AsyncSession = Depends(get_db)
):
    """Create a new evaluation task (admin only)."""
    task_id = f"et-{uuid.uuid4().hex[:8]}"
    task = EvaluationTaskModel(
        id=task_id,
        description=description,
        input_data=input_data,
        tags=tags,
        active=True
    )
    db.add(task)
    await db.commit()
    return {"id": task_id}

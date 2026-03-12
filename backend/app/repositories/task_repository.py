from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from ..models.db_models import TaskModel
from ..models.task import Task
from ..utils.json_encoder import prepare_json_data
import json

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, task: Task) -> Task:
        data = prepare_json_data(task.model_dump(by_alias=True))
        db_task = TaskModel(
            id=task.id,
            data=data
        )
        self.db.add(db_task)
        await self.db.commit()
        await self.db.refresh(db_task)
        return task

    async def get(self, task_id: str) -> Task | None:
        result = await self.db.execute(
            select(TaskModel).where(TaskModel.id == task_id)
        )
        db_task = result.scalar_one_or_none()
        if db_task:
            return Task(**db_task.data)
        return None

    async def get_all(self) -> list[Task]:
        result = await self.db.execute(select(TaskModel))
        db_tasks = result.scalars().all()
        return [Task(**t.data) for t in db_tasks]

    async def update(self, task_id: str, updates: dict) -> Task | None:
        task = await self.get(task_id)
        if not task:
            return None
        data = prepare_json_data(updates)
        await self.db.execute(
            update(TaskModel)
            .where(TaskModel.id == task_id)
            .values(data=data)
        )
        await self.db.commit()
        return task

    async def delete(self, task_id: str) -> bool:
        result = await self.db.execute(
            delete(TaskModel).where(TaskModel.id == task_id)
        )
        await self.db.commit()
        return result.rowcount > 0

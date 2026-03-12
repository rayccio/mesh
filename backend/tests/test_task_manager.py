import pytest
from app.services.task_manager import TaskManager
from app.models.task import Task, TaskStatus
from datetime import datetime

@pytest.mark.asyncio
async def test_create_task_graph(session):
    task_manager = TaskManager()
    tasks = [
        Task(
            id="t-1",
            hive_id="h-test",
            goal_id="",
            description="Task 1",
            created_at=datetime.utcnow()
        )
    ]
    edges = []
    graph = await task_manager.create_task_graph("h-test", "Test goal", tasks, edges)
    assert graph.goal_id.startswith("g-")
    assert graph.goal_description == "Test goal"
    # No explicit cleanup needed; session rollback will discard

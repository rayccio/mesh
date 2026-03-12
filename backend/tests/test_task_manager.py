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
    # Clean up (task_manager doesn't have delete_task_graph; we'll delete tasks individually)
    for task in tasks:
        await task_manager.update_task(task.id, status=TaskStatus.COMPLETED)  # or delete? not implemented
        # For simplicity, we'll skip deletion in test; tasks will be cleaned by session rollback.

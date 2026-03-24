from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from ....services.project_manager import ProjectManager
from ....services.hive_manager import HiveManager
from ....services.agent_manager import AgentManager
from ....services.docker_service import DockerService
from ....models.types import Project
from .auth import get_current_user

router = APIRouter(prefix="/hives/{hive_id}/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    goal: str
    root_goal_id: Optional[str] = None

class ProjectUpdate(BaseModel):
    state: Optional[str] = None

async def get_project_manager():
    return ProjectManager()

async def get_hive_manager():
    docker = DockerService()
    agent_manager = AgentManager(docker)
    return HiveManager(agent_manager)

@router.get("", response_model=List[Project])
async def list_projects(
    hive_id: str,
    project_manager: ProjectManager = Depends(get_project_manager),
    hive_manager: HiveManager = Depends(get_hive_manager),
    current_user=Depends(get_current_user)
):
    hive = await hive_manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    return await project_manager.list_projects(hive_id)

@router.post("", response_model=Project, status_code=201)
async def create_project(
    hive_id: str,
    project_data: ProjectCreate,
    project_manager: ProjectManager = Depends(get_project_manager),
    hive_manager: HiveManager = Depends(get_hive_manager),
    current_user=Depends(get_current_user)
):
    hive = await hive_manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    project = await project_manager.create_project(
        hive_id=hive_id,
        name=project_data.name,
        description=project_data.description,
        goal=project_data.goal,
        root_goal_id=project_data.root_goal_id
    )
    return project

@router.get("/{project_id}", response_model=Project)
async def get_project(
    hive_id: str,
    project_id: str,
    project_manager: ProjectManager = Depends(get_project_manager),
    hive_manager: HiveManager = Depends(get_hive_manager),
    current_user=Depends(get_current_user)
):
    hive = await hive_manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    project = await project_manager.get_project(project_id)
    if not project or project.hive_id != hive_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=Project)
async def update_project(
    hive_id: str,
    project_id: str,
    updates: ProjectUpdate,
    project_manager: ProjectManager = Depends(get_project_manager),
    hive_manager: HiveManager = Depends(get_hive_manager),
    current_user=Depends(get_current_user)
):
    hive = await hive_manager.get_hive(hive_id)
    if not hive:
        raise HTTPException(status_code=404, detail="Hive not found")
    project = await project_manager.update_project_state(project_id, updates.state)
    if not project or project.hive_id != hive_id:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

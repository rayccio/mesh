from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from ..core.database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class AgentModel(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    container_id = Column(String, nullable=True)
    status = Column(String, default="IDLE")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class HiveModel(Base):
    __tablename__ = "hives"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SkillModel(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SkillVersionModel(Base):
    __tablename__ = "skill_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    skill_id = Column(String, ForeignKey("skills.id"), nullable=False)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class SkillSuggestionModel(Base):
    __tablename__ = "skill_suggestions"

    id = Column(String, primary_key=True, default=generate_uuid)
    skill_name = Column(String, nullable=False)
    goal_id = Column(String, nullable=False)
    goal_description = Column(Text, nullable=False)
    task_id = Column(String, nullable=False)
    task_description = Column(Text, nullable=False)
    suggested_by = Column(String, nullable=True)
    resolved = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

class UserModel(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class GlobalSettingsModel(Base):
    __tablename__ = "global_settings"

    id = Column(Integer, primary_key=True, default=1)
    data = Column(JSONB, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class EvaluationTaskModel(Base):
    __tablename__ = "evaluation_tasks"

    id = Column(String, primary_key=True, default=generate_uuid)
    description = Column(Text, nullable=False)
    input_data = Column(JSONB, default={})
    tags = Column(JSONB, default=[])
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# New models
class GoalModel(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TaskEdgeModel(Base):
    __tablename__ = "task_edges"

    from_task = Column(String, primary_key=True)
    to_task = Column(String, primary_key=True)

class EconomyAccountModel(Base):
    __tablename__ = "economy_accounts"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class StrategyModel(Base):
    __tablename__ = "strategies"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RiskPolicyModel(Base):
    __tablename__ = "risk_policies"

    id = Column(String, primary_key=True, default=generate_uuid)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class ExecutionLogModel(Base):
    __tablename__ = "execution_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    goal_id = Column(String, nullable=False, index=True)
    task_id = Column(String, nullable=True)
    agent_id = Column(String, nullable=True)
    level = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    iteration = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ========== New models for layered architecture ==========

class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    hive_id = Column(String, ForeignKey("hives.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    goal = Column(String, nullable=False)
    root_goal_id = Column(String, ForeignKey("goals.id"), nullable=True)
    state = Column(String, default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LayerModel(Base):
    __tablename__ = "layers"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text)
    version = Column(String, nullable=False)
    author = Column(String, nullable=True)
    dependencies = Column(JSONB, default=[])
    enabled = Column(Boolean, default=True)
    lifecycle = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class LayerRoleModel(Base):
    __tablename__ = "layer_roles"

    layer_id = Column(String, ForeignKey("layers.id", ondelete="CASCADE"), primary_key=True)
    role_name = Column(String, primary_key=True)
    soul_md = Column(Text, nullable=False)
    identity_md = Column(Text, nullable=False)
    tools_md = Column(Text, nullable=False)
    role_type = Column(String, default="specialized")
    priority = Column(Integer, default=0)

class LayerSkillModel(Base):
    __tablename__ = "layer_skills"

    layer_id = Column(String, ForeignKey("layers.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(String, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)

class LayerConfigModel(Base):
    __tablename__ = "layer_configs"

    id = Column(String, primary_key=True, default=generate_uuid)
    layer_id = Column(String, ForeignKey("layers.id", ondelete="CASCADE"), nullable=False)
    hive_id = Column(String, ForeignKey("hives.id", ondelete="CASCADE"), nullable=False)
    config_data = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("ix_layer_configs_layer_hive", "layer_id", "hive_id"),
    )

class PlannerTemplateModel(Base):
    __tablename__ = "planner_templates"

    id = Column(String, primary_key=True, default=generate_uuid)
    layer_id = Column(String, ForeignKey("layers.id", ondelete="CASCADE"), nullable=False)
    goal_pattern = Column(Text, nullable=True)
    template = Column(Text, nullable=True)
    custom_planner_class = Column(String, nullable=True)
    priority = Column(Integer, default=0)

class LoopHandlerModel(Base):
    __tablename__ = "loop_handlers"

    id = Column(String, primary_key=True, default=generate_uuid)
    layer_id = Column(String, ForeignKey("layers.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    class_path = Column(String, nullable=False)

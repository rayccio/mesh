from sqlalchemy import Column, String, DateTime, Boolean, Text, Integer, ForeignKey
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

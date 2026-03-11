import pytest
from app.services.skill_manager import SkillManager
from app.models.skill import SkillCreate, SkillType, SkillVisibility

@pytest.mark.asyncio
async def test_create_skill(session):
    skill_manager = SkillManager()
    skill_in = SkillCreate(
        name="Test Skill",
        description="A test skill",
        type=SkillType.TOOL,
        visibility=SkillVisibility.PRIVATE,
        tags=["test"]
    )
    skill = await skill_manager.create_skill(skill_in)
    assert skill.id.startswith("sk-")
    assert skill.name == "Test Skill"
    await skill_manager.delete_skill(skill.id)

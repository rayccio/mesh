import pytest
from app.services.skill_manager import SkillManager
from app.models.skill import SkillCreate, SkillType, SkillVisibility
from unittest.mock import patch
from app.core.config import settings

@pytest.mark.asyncio
async def test_create_skill(session):
    # Mock internal API key (not used directly, but to avoid any accidental lookups)
    with patch.object(settings.secrets, 'get', return_value="test-internal-key"):
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
        # Clean up
        await skill_manager.delete_skill(skill.id)

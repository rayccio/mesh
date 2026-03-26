import asyncio
import json
import re
import logging
from typing import Dict, Any, Optional
from worker.loop_handler import BaseLoopHandler
from worker.constants import (
    BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS,
    TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS,
    REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS,
    FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS
)

logger = logging.getLogger(__name__)

class CodingLoopHandler(BaseLoopHandler):
    """Custom loop handler for coding tasks with a review step."""

    MAX_ITERATIONS = 5

    async def run(
        self,
        agent_id: str,
        task_id: str,
        description: str,
        input_data: Dict[str, Any],
        goal_id: str,
        hive_id: str,
        project_id: Optional[str],
        skill_executor,
        call_ai_delta,
        save_artifact,
        update_artifact_status,
        layer_id: Optional[str] = "coding"
    ) -> Dict[str, Any]:
        # Helper to build prompts
        def make_system_prompt(soul, identity, tools):
            return f"""You are an AI agent with the following STRICT IDENTITY. You must follow this identity exactly.

IDENTITY:
{identity}

SOUL:
{soul}

TOOLS:
{tools}

IMPORTANT: You are NOT a generic AI assistant. You are the entity described above. Always respond in character.
"""

        builder_prompt = make_system_prompt(BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS)
        tester_prompt = make_system_prompt(TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS)
        reviewer_prompt = make_system_prompt(REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS)
        fixer_prompt = make_system_prompt(FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS)

        async def call_with_role(role_prompt, user_prompt):
            return await call_ai_delta(
                agent_id,
                user_prompt,
                {},  # config will be taken from agent in the backend
                system_prompt_override=role_prompt,
                retries=1
            )

        def extract_json(text: str) -> Optional[dict]:
            code_block_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
            if code_block_match:
                try:
                    return json.loads(code_block_match.group(1))
                except:
                    pass
            json_match = re.search(r'\{.*?\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            return None

        current_code = None
        final_artifact_id = None
        for iteration in range(1, self.MAX_ITERATIONS + 1):
            logger.info(f"Agent {agent_id} – Iteration {iteration} for task {task_id}")

            # Builder
            builder_input = f"""Task: {description}
Additional input: {json.dumps(input_data, indent=2)}
Previous code (if any): {current_code or 'None'}
Generate the code for this task. Output only the code, no explanations."""
            code = await call_with_role(builder_prompt, builder_input)
            file_path = f"task_{task_id}/iteration_{iteration}/code.py"
            code_artifact = await save_artifact(hive_id, goal_id, task_id, file_path, code.encode(), status="draft", layer_id=layer_id)
            if code_artifact and code_artifact.get('id'):
                await update_artifact_status(hive_id, goal_id, code_artifact['id'], "built")
            current_code = code

            # Tester
            tester_input = f"""Task: {description}
Code to test:
{code}
Write and run tests for this code. Output the test results **in JSON format only** with keys "passed" (bool) and "errors" (list of strings). Do not include any other text.
Example: {{"passed": true, "errors": []}}"""
            test_result_text = await call_with_role(tester_prompt, tester_input)
            test_result = extract_json(test_result_text)
            if test_result is None:
                test_result = {"passed": False, "errors": ["Failed to parse test output"]}
            await save_artifact(hive_id, goal_id, task_id, f"task_{task_id}/iteration_{iteration}/test_result.json", json.dumps(test_result).encode(), status="tested", layer_id=layer_id)
            if code_artifact and code_artifact.get('id'):
                await update_artifact_status(hive_id, goal_id, code_artifact['id'], "tested")

            # If tests pass, go to reviewer
            if test_result.get("passed"):
                # Reviewer
                reviewer_input = f"""Task: {description}
Code:
{code}
Review the code for style, best practices, security, and maintainability. Provide a list of issues (if any) and a final verdict. Output in JSON format with keys "issues" (list of strings) and "approved" (bool)."""
                review_text = await call_with_role(reviewer_prompt, reviewer_input)
                review = extract_json(review_text)
                if review is None:
                    review = {"issues": ["Failed to parse review"], "approved": False}
                await save_artifact(hive_id, goal_id, task_id, f"task_{task_id}/iteration_{iteration}/review.json", json.dumps(review).encode(), status="reviewed", layer_id=layer_id)
                if code_artifact and code_artifact.get('id'):
                    await update_artifact_status(hive_id, goal_id, code_artifact['id'], "reviewed")

                if review.get("approved"):
                    # Final
                    final_artifact = await save_artifact(hive_id, goal_id, task_id, f"task_{task_id}/final_code.py", current_code.encode(), status="final", layer_id=layer_id)
                    if final_artifact and final_artifact.get('id'):
                        await update_artifact_status(hive_id, goal_id, final_artifact['id'], "final")
                    return {
                        "success": True,
                        "iterations": iteration,
                        "output": {
                            "final_artifact": final_artifact.get('id') if final_artifact else None,
                            "message": "Task completed and approved"
                        }
                    }
                else:
                    # Not approved: fixer
                    fixer_input = f"""Task: {description}
Code:
{code}
Review issues:
{json.dumps(review.get('issues', []), indent=2)}
Provide the fixed code addressing the issues. Output only the corrected code, no explanations."""
                    fixed_code = await call_with_role(fixer_prompt, fixer_input)
                    current_code = fixed_code
                    fixed_artifact = await save_artifact(hive_id, goal_id, task_id, f"task_{task_id}/iteration_{iteration}/fixed_code.py", fixed_code.encode(), status="fixed", layer_id=layer_id)
                    # Continue loop
            else:
                # Tests failed: fixer
                fixer_input = f"""Task: {description}
Code:
{code}
Test errors:
{json.dumps(test_result.get('errors', []), indent=2)}
Provide the fixed code addressing the test failures. Output only the corrected code, no explanations."""
                fixed_code = await call_with_role(fixer_prompt, fixer_input)
                current_code = fixed_code
                fixed_artifact = await save_artifact(hive_id, goal_id, task_id, f"task_{task_id}/iteration_{iteration}/fixed_code.py", fixed_code.encode(), status="fixed", layer_id=layer_id)

        # Max iterations reached
        logger.warning(f"Task {task_id} failed after {self.MAX_ITERATIONS} iterations")
        return {
            "success": False,
            "iterations": self.MAX_ITERATIONS,
            "output": {"message": "Max iterations exceeded"}
        }

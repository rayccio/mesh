import re
from typing import Any, Dict, Tuple
from abc import ABC, abstractmethod

class BaseEvaluator(ABC):
    """Base class for all evaluators."""

    @abstractmethod
    async def evaluate(self, agent_output: Any, expected_output: Any, input_data: Dict) -> Tuple[float, str]:
        """
        Evaluate the agent's output against expected output.
        Returns a tuple (score, message) where score is a float between 0 and 1.
        """
        pass

class WebEvaluator(BaseEvaluator):
    """Evaluator for web frontend tasks (HTML/CSS/JS)."""

    async def evaluate(self, agent_output: Any, expected_output: Any, input_data: Dict) -> Tuple[float, str]:
        # This is a simplified example. In production, you might use a headless browser.
        # For now, we'll do basic checks.
        score = 0.0
        issues = []
        if not agent_output:
            return 0.0, "No output produced"

        # Check for required tags (example: should have <html>, <body>)
        if "html" in agent_output.lower() and "body" in agent_output.lower():
            score += 0.3
        else:
            issues.append("Missing <html> or <body> tags")

        # Check for responsive meta tag
        if 'meta name="viewport"' in agent_output.lower():
            score += 0.2
        else:
            issues.append("Missing viewport meta tag")

        # Check for CSS inclusion (could be inline or external)
        if "<style>" in agent_output or "link rel=\"stylesheet\"" in agent_output:
            score += 0.3
        else:
            issues.append("No CSS styling found")

        # Check for JavaScript
        if "<script>" in agent_output or "src=\"" in agent_output:
            score += 0.2
        else:
            issues.append("No JavaScript found")

        message = f"Score: {score:.1f}. " + "; ".join(issues) if issues else "Good job!"
        return score, message

class BackendEvaluator(BaseEvaluator):
    """Evaluator for backend code (Python/FastAPI)."""

    async def evaluate(self, agent_output: Any, expected_output: Any, input_data: Dict) -> Tuple[float, str]:
        score = 0.0
        issues = []
        if not agent_output:
            return 0.0, "No output produced"

        # Check for FastAPI import
        if "from fastapi import FastAPI" in agent_output:
            score += 0.4
        else:
            issues.append("Missing FastAPI import")

        # Check for route definition
        if "@app.get" in agent_output or "@app.post" in agent_output:
            score += 0.3
        else:
            issues.append("No route definitions found")

        # Check for return statement
        if "return" in agent_output:
            score += 0.3
        else:
            issues.append("No return statement in route handlers")

        message = f"Score: {score:.1f}. " + "; ".join(issues) if issues else "Good job!"
        return score, message

class DatabaseEvaluator(BaseEvaluator):
    """Evaluator for database schema tasks."""

    async def evaluate(self, agent_output: Any, expected_output: Any, input_data: Dict) -> Tuple[float, str]:
        score = 0.0
        issues = []
        if not agent_output:
            return 0.0, "No output produced"

        # Check for CREATE TABLE
        if "CREATE TABLE" in agent_output.upper():
            score += 0.5
        else:
            issues.append("No CREATE TABLE statements")

        # Check for PRIMARY KEY
        if "PRIMARY KEY" in agent_output.upper():
            score += 0.3
        else:
            issues.append("No primary key defined")

        # Check for foreign key (optional)
        if "FOREIGN KEY" in agent_output.upper():
            score += 0.2

        message = f"Score: {score:.1f}. " + "; ".join(issues) if issues else "Good job!"
        return score, message

# Map evaluator names to classes
EVALUATORS = {
    "WebEvaluator": WebEvaluator,
    "BackendEvaluator": BackendEvaluator,
    "DatabaseEvaluator": DatabaseEvaluator,
}

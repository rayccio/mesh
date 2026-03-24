#!/usr/bin/env python3
"""
Seed the core layer with default roles, skills, and other data.
Run after create_layer_tables.py.
"""

import asyncio
import asyncpg
import os
import sys
import uuid
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings
from app.constants import (
    BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS,
    TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS,
    REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS,
    FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS,
    ARCHITECT_SOUL, ARCHITECT_IDENTITY, ARCHITECT_TOOLS,
    RESEARCHER_SOUL, RESEARCHER_IDENTITY, RESEARCHER_TOOLS,
    INITIAL_SOUL, INITIAL_IDENTITY, INITIAL_TOOLS
)

DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOST}/{settings.POSTGRES_DB}"

async def migrate():
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        # Insert core layer
        core_layer_id = "core"
        now = datetime.utcnow()
        await conn.execute("""
            INSERT INTO layers (id, name, description, version, author, enabled, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (id) DO NOTHING
        """, core_layer_id, "HiveBot Core", "Core system roles and skills", "1.0.0", "system", True, now, now)
        print("Core layer inserted.")

        # Insert core roles
        roles = [
            ("builder", BUILDER_SOUL, BUILDER_IDENTITY, BUILDER_TOOLS, "core"),
            ("tester", TESTER_SOUL, TESTER_IDENTITY, TESTER_TOOLS, "core"),
            ("reviewer", REVIEWER_SOUL, REVIEWER_IDENTITY, REVIEWER_TOOLS, "core"),
            ("fixer", FIXER_SOUL, FIXER_IDENTITY, FIXER_TOOLS, "core"),
            ("architect", ARCHITECT_SOUL, ARCHITECT_IDENTITY, ARCHITECT_TOOLS, "core"),
            ("researcher", RESEARCHER_SOUL, RESEARCHER_IDENTITY, RESEARCHER_TOOLS, "core"),
            ("generic", INITIAL_SOUL, INITIAL_IDENTITY, INITIAL_TOOLS, "core"),
        ]
        for role_name, soul, identity, tools, role_type in roles:
            await conn.execute("""
                INSERT INTO layer_roles (layer_id, role_name, soul_md, identity_md, tools_md, role_type)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (layer_id, role_name) DO NOTHING
            """, core_layer_id, role_name, soul, identity, tools, role_type)
        print("Core roles inserted.")

        # Insert core skills (existing tools) into skills table
        # First, check if skills already exist
        core_skills = [
            ("web_search", "Search the web using a search engine", "tool"),
            ("ssh_execute", "Execute a command on a remote server via SSH", "tool"),
            ("browser_action", "Perform browser automation (goto, click, type, screenshot)", "tool"),
            ("run_code", "Execute code in an isolated container", "tool"),
            ("api_call", "Make an HTTP request to an external API", "tool"),
        ]
        skill_ids = {}
        for skill_name, skill_desc, skill_type in core_skills:
            # Insert skill if not exists
            skill_id = f"sk-{uuid.uuid4().hex[:8]}"
            # Check if skill already exists by name
            existing = await conn.fetchval("SELECT id FROM skills WHERE data->>'name' = $1", skill_name)
            if existing:
                print(f"Skill {skill_name} already exists, skipping.")
                skill_ids[skill_name] = existing
                continue
            skill_data = {
                "id": skill_id,
                "name": skill_name,
                "description": skill_desc,
                "type": skill_type,
                "visibility": "public",
                "author_id": "system",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
                "tags": [],
                "metadata": {}
            }
            await conn.execute(
                "INSERT INTO skills (id, data) VALUES ($1, $2)",
                skill_id, asyncpg.types.json.dumps(skill_data)
            )
            # Link to core layer
            await conn.execute(
                "INSERT INTO layer_skills (layer_id, skill_id) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                core_layer_id, skill_id
            )
            skill_ids[skill_name] = skill_id
            print(f"Skill {skill_name} inserted.")
        print("Core skills inserted.")

        # Insert skill versions for core skills
        core_skill_versions = [
            {
                "skill_name": "web_search",
                "version": "1.0.0",
                "code": """
import os
import httpx

async def run(input, config):
    query = input.get("query", "")
    if not query:
        return {"error": "Missing query"}
    api_key = os.getenv("SEARCH_API_KEY")
    engine = os.getenv("SEARCH_ENGINE", "google").lower()
    if engine == "serpapi" and api_key:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "engine": "google"}
            )
            resp.raise_for_status()
            data = resp.json()
            results = []
            for r in data.get("organic_results", []):
                results.append({
                    "title": r.get("title"),
                    "link": r.get("link"),
                    "snippet": r.get("snippet")
                })
            return {"results": results}
    else:
        return {
            "results": [
                {"title": f"Mock result for {query}", "url": "http://example.com", "snippet": "This is a mock result."}
            ]
        }
""",
                "language": "python",
                "entry_point": "run"
            },
            {
                "skill_name": "run_code",
                "version": "1.0.0",
                "code": """
import docker

def run(input, config):
    code = input.get("code", "")
    language = input.get("language", "python").lower()
    client = docker.from_env()
    image_map = {
        "python": "python:3.11-slim",
        "node": "node:18-slim",
        "bash": "alpine:latest",
    }
    image = image_map.get(language, "alpine:latest")
    try:
        if language == "python":
            cmd = ["python", "-c", code]
        elif language == "node":
            cmd = ["node", "-e", code]
        elif language == "bash":
            cmd = ["sh", "-c", code]
        else:
            return {"error": f"Unsupported language: {language}"}
        container = client.containers.run(
            image=image,
            command=cmd,
            detach=False,
            remove=True,
            mem_limit="128m",
            cpu_shares=512,
            network_disabled=True,
            read_only=True
        )
        logs = container.decode() if isinstance(container, bytes) else str(container)
        return {"stdout": logs, "stderr": ""}
    except Exception as e:
        return {"error": str(e)}
""",
                "language": "python",
                "entry_point": "run"
            },
            {
                "skill_name": "ssh_execute",
                "version": "1.0.0",
                "code": """
import asyncssh

async def run(input, config):
    host = input.get("host")
    port = input.get("port", 22)
    username = input.get("username")
    password = input.get("password")
    command = input.get("command")
    if not all([host, username, command]):
        return {"error": "Missing required parameters"}
    try:
        async with asyncssh.connect(
            host=host,
            port=port,
            username=username,
            password=password,
            known_hosts=None
        ) as conn:
            result = await conn.run(command, check=True)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.exit_code
            }
    except Exception as e:
        return {"error": str(e)}
""",
                "language": "python",
                "entry_point": "run"
            },
            {
                "skill_name": "browser_action",
                "version": "1.0.0",
                "code": """
from playwright.async_api import async_playwright

async def run(input, config):
    action = input.get("action")
    url = input.get("url")
    selector = input.get("selector")
    value = input.get("value")
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    try:
        if action == "goto":
            await page.goto(url)
            content = await page.content()
            return {"html": content, "title": await page.title()}
        elif action == "click":
            await page.goto(url)
            await page.click(selector)
            await page.wait_for_load_state()
            return {"success": True, "html": await page.content()}
        elif action == "type":
            await page.goto(url)
            await page.fill(selector, value)
            return {"success": True}
        elif action == "screenshot":
            await page.goto(url)
            screenshot = await page.screenshot(full_page=True)
            import base64
            return {"screenshot": base64.b64encode(screenshot).decode()}
        else:
            return {"error": f"Unknown action: {action}"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        await browser.close()
        await p.stop()
""",
                "language": "python",
                "entry_point": "run"
            },
            {
                "skill_name": "api_call",
                "version": "1.0.0",
                "code": """
import httpx

async def run(input, config):
    method = input.get("method", "GET").upper()
    url = input.get("url")
    headers = input.get("headers", {})
    body = input.get("body")
    if not url:
        return {"error": "Missing URL"}
    async with httpx.AsyncClient() as client:
        if method == "GET":
            resp = await client.get(url, headers=headers)
        elif method == "POST":
            resp = await client.post(url, json=body, headers=headers)
        elif method == "PUT":
            resp = await client.put(url, json=body, headers=headers)
        elif method == "DELETE":
            resp = await client.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}
        content_type = resp.headers.get("content-type", "")
        if "application/json" in content_type:
            data = resp.json()
        else:
            data = resp.text
        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": data
        }
""",
                "language": "python",
                "entry_point": "run"
            },
        ]

        for version_info in core_skill_versions:
            skill_name = version_info["skill_name"]
            skill_id = skill_ids.get(skill_name)
            if not skill_id:
                print(f"Skill {skill_name} not found, skipping version insertion.")
                continue
            # Check if version already exists
            existing_version = await conn.fetchval(
                "SELECT id FROM skill_versions WHERE skill_id = $1 AND data->>'version' = $2",
                skill_id, version_info["version"]
            )
            if existing_version:
                print(f"Version {version_info['version']} for skill {skill_name} already exists, skipping.")
                continue
            version_id = f"sv-{uuid.uuid4().hex[:8]}"
            version_data = {
                "id": version_id,
                "skill_id": skill_id,
                "version": version_info["version"],
                "code": version_info["code"],
                "language": version_info["language"],
                "entry_point": version_info["entry_point"],
                "requirements": [],
                "config_schema": None,
                "created_at": now.isoformat(),
                "is_active": True,
                "changelog": "Initial version"
            }
            await conn.execute(
                "INSERT INTO skill_versions (id, skill_id, data) VALUES ($1, $2, $3)",
                version_id, skill_id, asyncpg.types.json.dumps(version_data)
            )
            print(f"Version {version_info['version']} for skill {skill_name} inserted.")
        print("Core skill versions inserted.")

        # Insert a default lifecycle for core layer
        lifecycle = {
            "states": ["draft", "built", "tested", "final"],
            "transitions": {
                "draft": ["built"],
                "built": ["tested"],
                "tested": ["final"],
            }
        }
        await conn.execute("UPDATE layers SET lifecycle = $1 WHERE id = $2", asyncpg.types.json.dumps(lifecycle), core_layer_id)
        print("Default lifecycle set.")

        # Insert a default loop handler (generic)
        loop_id = "default_loop"
        await conn.execute("""
            INSERT INTO loop_handlers (id, layer_id, name, class_path)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (id) DO NOTHING
        """, loop_id, core_layer_id, "default", "worker.loop_handler.DefaultLoopHandler")
        print("Default loop handler registered.")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(migrate())

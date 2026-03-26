import os
import httpx

async def run(input: dict, config: dict) -> dict:
    description = input.get("description", "")
    if not description:
        return {"error": "Missing description"}

    internal_api_key = os.getenv("INTERNAL_API_KEY")
    orchestrator_url = os.getenv("ORCHESTRATOR_URL", "http://backend:8000")
    if not internal_api_key:
        return {"error": "INTERNAL_API_KEY not set"}

    prompt = f"""You are an expert database designer. Generate SQL schema (CREATE TABLE statements) for the following description.
Only output the SQL code, no explanations.

Description: {description}

SQL:"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{orchestrator_url}/api/v1/internal/ai/generate-delta",
            json={"agent_id": "system", "input": prompt, "config": {}},
            headers={"Authorization": f"Bearer {internal_api_key}"},
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()
        sql = data.get("response", "")
    return {"sql": sql}

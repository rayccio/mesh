from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from ....core.database import get_db
from ....models.db_models import AgentModel, TaskModel
import json

router = APIRouter(prefix="/meta", tags=["meta"])

@router.get("/status")
async def get_meta_status(db: AsyncSession = Depends(get_db)):
    """Get current meta-agent status and last run time."""
    result = await db.execute(
        text("""
            SELECT created_at FROM agents 
            WHERE data->'meta'->>'improved' = 'true' 
            ORDER BY created_at DESC LIMIT 1
        """)
    )
    last_activity = result.scalar_one_or_none()
    return {
        "status": "active",
        "last_run": last_activity.isoformat() if last_activity else None,
        "version": "2.0"
    }

@router.get("/test-agents")
async def list_test_agents(
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List all test agents (agents created by meta-agent for evaluation)."""
    result = await db.execute(
        text("""
            SELECT id, data, created_at FROM agents 
            WHERE data->'meta'->>'improved' = 'true' 
               OR data->'meta'->>'simulation' = 'true'
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    rows = result.fetchall()
    agents = []
    for row in rows:
        agent_data = json.loads(row[1])
        agents.append({
            "id": row[0],
            "name": agent_data.get("name", "Unnamed"),
            "parent_id": agent_data.get("meta", {}).get("parent_agent"),
            "improved": agent_data.get("meta", {}).get("improved", False),
            "simulation": agent_data.get("meta", {}).get("simulation", False),
            "created_at": row[2].isoformat() if row[2] else None,
            "status": agent_data.get("status", "unknown"),
            "mutation": agent_data.get("meta", {}).get("mutation"),
            "promoted": agent_data.get("meta", {}).get("promoted_at") is not None
        })
    return agents

@router.get("/performance")
async def get_performance_stats(
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get performance statistics for test agents vs production agents."""
    since = datetime.utcnow() - timedelta(hours=hours)
    
    # Get test agent tasks performance
    test_result = await db.execute(
        text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN data->>'status' = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE data->>'assigned_agent_id' IN (
                SELECT id FROM agents WHERE data->'meta'->>'improved' = 'true'
            )
            AND (data->>'created_at')::timestamptz >= :since
        """),
        {"since": since}  # Pass datetime object, not string
    )
    test_row = test_result.fetchone()
    test_total = test_row[0] or 0
    test_completed = test_row[1] or 0
    test_success_rate = (test_completed / test_total) if test_total > 0 else 0

    # Get production agent tasks performance
    prod_result = await db.execute(
        text("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN data->>'status' = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks
            WHERE data->>'assigned_agent_id' NOT IN (
                SELECT id FROM agents WHERE data->'meta'->>'improved' = 'true'
            )
            AND (data->>'created_at')::timestamptz >= :since
        """),
        {"since": since}  # Pass datetime object, not string
    )
    prod_row = prod_result.fetchone()
    prod_total = prod_row[0] or 0
    prod_completed = prod_row[1] or 0
    prod_success_rate = (prod_completed / prod_total) if prod_total > 0 else 0

    return {
        "period_hours": hours,
        "test_agents": {
            "total_tasks": test_total,
            "completed": test_completed,
            "success_rate": round(test_success_rate, 3)
        },
        "production_agents": {
            "total_tasks": prod_total,
            "completed": prod_completed,
            "success_rate": round(prod_success_rate, 3)
        }
    }

@router.get("/metrics/agent/{agent_id}")
async def get_agent_metrics(
    agent_id: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed performance metrics for a specific agent."""
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        text("""
            SELECT data FROM tasks
            WHERE data->>'assigned_agent_id' = :agent_id
            AND (data->>'created_at')::timestamptz >= :since
            ORDER BY (data->>'created_at')::timestamptz DESC
        """),
        {"agent_id": agent_id, "since": since}  # Pass datetime object, not string
    )
    tasks = [json.loads(r[0]) for r in result.fetchall()]
    
    total = len(tasks)
    completed = sum(1 for t in tasks if t.get("status") == "completed")
    success_rate = completed / total if total > 0 else 0
    
    # Calculate average response time
    timed_tasks = [t for t in tasks if t.get("started_at") and t.get("completed_at")]
    avg_time = 0
    if timed_tasks:
        total_time = sum(
            (datetime.fromisoformat(t["completed_at"]) - datetime.fromisoformat(t["started_at"])).total_seconds()
            for t in timed_tasks
        )
        avg_time = total_time / len(timed_tasks)
    
    return {
        "agent_id": agent_id,
        "period_hours": hours,
        "total_tasks": total,
        "completed": completed,
        "success_rate": round(success_rate, 3),
        "avg_response_time_seconds": round(avg_time, 2),
        "tasks": [
            {
                "id": t.get("id"),
                "status": t.get("status"),
                "created_at": t.get("created_at"),
                "completed_at": t.get("completed_at")
            } for t in tasks[:20]  # last 20 tasks
        ]
    }

@router.get("/ab-tests")
async def list_ab_tests(
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """List all A/B test results (parent/child pairs)."""
    result = await db.execute(
        text("""
            SELECT id, data FROM agents 
            WHERE data->'meta'->>'improved' = 'true' 
              AND data->'meta'->>'parent_agent' IS NOT NULL
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    rows = result.fetchall()
    tests = []
    for row in rows:
        agent_data = json.loads(row[1])
        parent_id = agent_data["meta"]["parent_agent"]
        # Fetch parent data for comparison
        parent_result = await db.execute(
            text("SELECT data FROM agents WHERE id = :id"),
            {"id": parent_id}
        )
        parent_row = parent_result.fetchone()
        parent_data = json.loads(parent_row[0]) if parent_row else {}
        
        tests.append({
            "test_agent_id": row[0],
            "test_agent_name": agent_data.get("name"),
            "parent_agent_id": parent_id,
            "parent_agent_name": parent_data.get("name"),
            "mutation": agent_data.get("meta", {}).get("mutation"),
            "created_at": agent_data.get("created_at"),
            "promoted": agent_data.get("meta", {}).get("promoted_at") is not None,
            "promoted_at": agent_data.get("meta", {}).get("promoted_at")
        })
    return tests

@router.get("/logs")
async def get_meta_logs(
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db)
):
    """Get recent meta-agent activity logs."""
    result = await db.execute(
        text("""
            SELECT id, data, created_at FROM agents 
            WHERE data->'meta'->>'improved' = 'true' 
            ORDER BY created_at DESC
            LIMIT :limit
        """),
        {"limit": limit}
    )
    rows = result.fetchall()
    logs = []
    for row in rows:
        agent_data = json.loads(row[1])
        logs.append({
            "timestamp": row[2].isoformat() if row[2] else None,
            "event": "test_agent_created",
            "agent_id": row[0],
            "agent_name": agent_data.get("name"),
            "parent_agent": agent_data.get("meta", {}).get("parent_agent"),
            "mutation": agent_data.get("meta", {}).get("mutation"),
            "promoted": agent_data.get("meta", {}).get("promoted_at") is not None
        })
    return logs

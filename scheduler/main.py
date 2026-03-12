import os
import asyncio
import asyncpg
import redis.asyncio as redis
import logging
import json
from datetime import datetime
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("scheduler")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql://hivebot:hivebot@postgres/hivebot")
AUTO_ASSIGN = os.getenv("SCHEDULER_AUTO_ASSIGN", "false").lower() == "true"
ENABLED = os.getenv("SCHEDULER_ENABLED", "false").lower() == "true"

async def health_check(request):
    return web.json_response({"status": "ok", "service": "scheduler"})

async def start_health_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8087)
    await site.start()
    logger.info("Health server started on port 8087")

async def populate_pending_tasks(pg_pool, redis_client):
    """Load all pending tasks from DB and add to Redis sorted set."""
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, created_at FROM tasks WHERE data->>'status' = 'pending'")
        for row in rows:
            score = row['created_at'].timestamp() * 1000
            await redis_client.zadd("tasks:pending", {row['id']: score})
    logger.info(f"Populated {len(rows)} pending tasks into Redis")

async def populate_idle_agents(pg_pool, redis_client):
    """Load all idle agents from DB and add to Redis set."""
    async with pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT id FROM agents WHERE data->>'status' = 'IDLE'")
        for row in rows:
            await redis_client.sadd("agents:idle", row['id'])
    logger.info(f"Populated {len(rows)} idle agents into Redis")

async def maintenance_loop(pg_pool, redis_client):
    """Periodically remove tasks that are no longer pending from Redis."""
    while True:
        await asyncio.sleep(30)
        task_ids = await redis_client.zrange("tasks:pending", 0, -1)
        if not task_ids:
            continue
        async with pg_pool.acquire() as conn:
            for task_id in task_ids:
                status = await conn.fetchval("SELECT data->>'status' FROM tasks WHERE id = $1", task_id)
                if status and status != "pending":
                    await redis_client.zrem("tasks:pending", task_id)
                    logger.debug(f"Removed {task_id} from pending queue (status {status})")

async def assignment_loop(pg_pool, redis_client):
    """Main assignment loop – matches pending tasks to idle agents."""
    while True:
        # Get highest priority pending task
        tasks = await redis_client.zrange("tasks:pending", 0, 0, withscores=True)
        if not tasks:
            await asyncio.sleep(1)
            continue
        task_id, score = tasks[0]

        # Fetch task from DB
        async with pg_pool.acquire() as conn:
            task_row = await conn.fetchrow("SELECT data, required_skills FROM tasks WHERE id = $1", task_id)
            if not task_row:
                await redis_client.zrem("tasks:pending", task_id)
                continue
            task_data = json.loads(task_row['data'])
            if task_data['status'] != 'pending':
                await redis_client.zrem("tasks:pending", task_id)
                continue
            required_skills = task_row['required_skills'] or []

            # Get idle agent ids
            idle_agent_ids = await redis_client.smembers("agents:idle")
            if not idle_agent_ids:
                await asyncio.sleep(1)
                continue

            # Fetch all idle agents' data in one query
            agents_rows = await conn.fetch(
                "SELECT id, data FROM agents WHERE id = ANY($1)",
                list(idle_agent_ids)
            )
            matching_agent = None
            for agent_row in agents_rows:
                agent_id = agent_row['id']
                agent_data = json.loads(agent_row['data'])
                agent_skills = [s['skillId'] for s in agent_data.get('skills', [])]
                if set(required_skills).issubset(set(agent_skills)):
                    matching_agent = agent_id
                    break

            if not matching_agent:
                await asyncio.sleep(1)
                continue

            # Assign task
            task_data['status'] = 'assigned'
            task_data['assigned_agent_id'] = matching_agent
            task_data['started_at'] = datetime.utcnow().isoformat()
            await conn.execute(
                "UPDATE tasks SET data = $1 WHERE id = $2",
                json.dumps(task_data), task_id
            )

            # Update agent status in DB
            agent_data = await conn.fetchval("SELECT data FROM agents WHERE id = $1", matching_agent)
            agent_data = json.loads(agent_data)
            agent_data['status'] = 'ASSIGNED'
            await conn.execute(
                "UPDATE agents SET data = $1 WHERE id = $2",
                json.dumps(agent_data), matching_agent
            )

            # Remove from Redis queues
            await redis_client.zrem("tasks:pending", task_id)
            await redis_client.srem("agents:idle", matching_agent)

            # Notify agent
            await redis_client.publish(
                f"agent:{matching_agent}",
                json.dumps({
                    'type': 'task_assign',
                    'task_id': task_id,
                    'description': task_data['description'],
                    'input_data': task_data.get('input_data', {}),
                    'goal_id': task_data.get('goal_id'),
                    'hive_id': task_data.get('hive_id')
                })
            )
            logger.info(f"Assigned task {task_id} to agent {matching_agent}")

async def main():
    if not ENABLED:
        logger.info("Scheduler disabled, exiting.")
        return

    pg_pool = await asyncpg.create_pool(POSTGRES_DSN)
    redis_client = await redis.from_url(f"redis://{REDIS_HOST}:{REDIS_PORT}", decode_responses=True)

    # Start health server
    asyncio.create_task(start_health_server())

    # Initial population
    await populate_pending_tasks(pg_pool, redis_client)
    await populate_idle_agents(pg_pool, redis_client)

    # Start maintenance loop
    asyncio.create_task(maintenance_loop(pg_pool, redis_client))

    if AUTO_ASSIGN:
        logger.info("Auto-assign enabled, starting assignment loop")
        asyncio.create_task(assignment_loop(pg_pool, redis_client))
    else:
        logger.info("Auto-assign disabled, scheduler running in maintenance mode")

    # Keep running
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        await redis_client.close()
        await pg_pool.close()

if __name__ == "__main__":
    asyncio.run(main())

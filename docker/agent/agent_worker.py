import os
import json
import redis
import requests
import logging
import sys
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger("agent_worker")

AGENT_ID = os.environ.get("AGENT_ID")
PARENT_ID = os.environ.get("PARENT_ID")
REPORTING_TARGET = os.environ.get("REPORTING_TARGET", "PARENT_AGENT")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY")
ORCHESTRATOR_URL = os.environ.get("ORCHESTRATOR_URL", "http://backend:8000")

DATA_DIR = Path("/data")
SOUL_PATH = DATA_DIR / "soul.md"
IDENTITY_PATH = DATA_DIR / "identity.md"
TOOLS_PATH = DATA_DIR / "tools.md"

def read_file(path):
    try:
        with open(path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def load_agent_files():
    return {
        "soul": read_file(SOUL_PATH),
        "identity": read_file(IDENTITY_PATH),
        "tools": read_file(TOOLS_PATH),
    }

def call_ai_delta(agent_id, user_input, model_config):
    url = f"{ORCHESTRATOR_URL}/api/v1/internal/ai/generate-delta"
    headers = {
        "Authorization": f"Bearer {INTERNAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "agent_id": agent_id,
        "input": user_input,
        "config": model_config
    }
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        return resp.json()["response"]
    except Exception as e:
        logger.error(f"AI call failed: {e}", exc_info=True)
        return f"Error: {str(e)}"

def get_agent_config():
    url = f"{ORCHESTRATOR_URL}/api/v1/agents/{AGENT_ID}"
    headers = {"Authorization": f"Bearer {INTERNAL_API_KEY}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.error(f"Failed to fetch agent config: {e}")
        return None

def connect_redis():
    retries = 5
    while retries > 0:
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
            r.ping()
            return r
        except Exception as e:
            retries -= 1
            logger.error(f"Redis connection failed, retries left {retries}: {e}")
            time.sleep(2)
    raise Exception("Could not connect to Redis")

def main():
    logger.info(f"Agent {AGENT_ID} starting...")
    while True:
        try:
            r = connect_redis()
            pubsub = r.pubsub()
            channel = f"agent:{AGENT_ID}"
            pubsub.subscribe(channel)
            logger.info(f"Subscribed to {channel}")

            for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                try:
                    data = json.loads(message["data"])
                    cmd = data.get("type")
                    logger.info(f"Received command: {cmd}")

                    if cmd == "think":
                        user_input = data.get("input", "")
                        model_config = data.get("config", {})
                        response = call_ai_delta(AGENT_ID, user_input, model_config)

                        agent_config = get_agent_config()
                        if agent_config is None:
                            current_parent_id = PARENT_ID
                            current_reporting = REPORTING_TARGET
                        else:
                            current_parent_id = agent_config.get("parentId")
                            current_reporting = agent_config.get("reportingTarget", "PARENT_AGENT")

                        channels_to_publish = []
                        if current_reporting == "PARENT_AGENT" and current_parent_id:
                            channels_to_publish.append(f"report:parent:{current_parent_id}")
                        elif current_reporting == "OWNER_DIRECT":
                            channels_to_publish.append("report:owner")
                        elif current_reporting == "HYBRID":
                            if current_parent_id:
                                channels_to_publish.append(f"report:parent:{current_parent_id}")
                            channels_to_publish.append("report:owner")
                        else:
                            channels_to_publish.append("report:owner")

                        result = {
                            "agent_id": AGENT_ID,
                            "response": response,
                            "timestamp": data.get("timestamp", "")
                        }
                        for ch in channels_to_publish:
                            r.publish(ch, json.dumps(result))

                    elif cmd == "task_assign":
                        task_id = data.get("task_id")
                        description = data.get("description")
                        goal_id = data.get("goal_id")
                        input_data = data.get("input_data", {})

                        logger.info(f"Executing task {task_id}: {description}")

                        agent_files = load_agent_files()
                        prompt = f"""You are an autonomous bot with the following identity and tools.

IDENTITY:
{agent_files['identity']}

SOUL:
{agent_files['soul']}

TOOLS:
{agent_files['tools']}

You have been assigned a task:
Task Description: {description}
Additional input: {json.dumps(input_data, indent=2)}

Carry out the task. Use your tools if needed. When you are done, provide the final output in a clear format.
"""

                        # Use the AI with a generic config (primary model will be used by backend)
                        config = {}  # backend will fill in from agent reasoning
                        response = call_ai_delta(AGENT_ID, prompt, config)

                        result = {
                            "agent_id": AGENT_ID,
                            "task_id": task_id,
                            "goal_id": goal_id,
                            "output": response,
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        r.publish(f"task:{goal_id}:completed", json.dumps(result))
                        logger.info(f"Task {task_id} completed")

                    else:
                        logger.warning(f"Unknown command: {cmd}")

                except Exception as e:
                    logger.exception("Error processing message")

        except (redis.exceptions.ConnectionError, redis.exceptions.TimeoutError) as e:
            logger.error(f"Redis connection lost: {e}. Reconnecting...")
            time.sleep(5)
            continue
        except Exception as e:
            logger.exception("Fatal error, restarting loop")
            time.sleep(5)
            continue

if __name__ == "__main__":
    main()

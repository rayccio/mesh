#!/usr/bin/env python3
import os
import json
import sys
import traceback
import asyncio
import importlib.util
import subprocess

async def main():
    skill_code = os.environ.get("SKILL_CODE")
    input_data = os.environ.get("INPUT")
    config_data = os.environ.get("CONFIG")

    if not skill_code:
        print(json.dumps({"error": "No skill code provided"}))
        return 1

    # Write skill code to a temporary file
    with open("/tmp/skill.py", "w") as f:
        f.write(skill_code)

    # Load the module
    spec = importlib.util.spec_from_file_location("skill", "/tmp/skill.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Parse input and config
    try:
        input_dict = json.loads(input_data) if input_data else {}
    except:
        input_dict = {}
    try:
        config_dict = json.loads(config_data) if config_data else {}
    except:
        config_dict = {}

    # Find the run function
    if hasattr(module, "run"):
        run_func = module.run
    else:
        print(json.dumps({"error": "No run function found in skill"}))
        return 1

    # Execute
    try:
        if asyncio.iscoroutinefunction(run_func):
            result = await run_func(input_dict, config_dict)
        else:
            result = run_func(input_dict, config_dict)
        print(json.dumps(result))
    except Exception as e:
        traceback.print_exc()
        print(json.dumps({"error": str(e)}))
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

import docker
import logging
import uuid
from pathlib import Path
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ContainerManager:
    """
    Manages Docker containers for skill execution with different sandbox levels.
    """

    def __init__(self, docker_client=None, network="hivebot_network"):
        self.docker_client = docker_client or docker.from_env()
        self.network = network
        self.task_containers: Dict[str, str] = {}  # task_id -> container_id
        self.project_containers: Dict[str, str] = {}  # project_id -> container_id

    def _ensure_image(self) -> str:
        """Ensure the skill‑runner image exists; build if necessary."""
        image_tag = "hivebot/skill-runner:latest"
        try:
            self.docker_client.images.get(image_tag)
        except docker.errors.ImageNotFound:
            logger.info(f"Building skill‑runner image {image_tag}...")
            # Build a simple image that can run Python code
            dockerfile = """
FROM python:3.11-slim
RUN pip install --no-cache-dir docker
COPY runner.py /runner.py
ENTRYPOINT ["python", "/runner.py"]
"""
            # We need to write a temporary Dockerfile and build
            # For simplicity, we'll assume the image is built elsewhere.
            # In production, this image should be built in docker-compose.
            # For now, we'll raise an error.
            raise RuntimeError(f"Skill-runner image {image_tag} not found. Please build it using the agent-builder profile.")
        return image_tag

    async def run_skill_in_container(
        self,
        skill_code: str,
        input_data: dict,
        config: dict,
        sandbox_level: str,
        task_id: Optional[str] = None,
        project_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> dict:
        """
        Execute skill code in a container appropriate for the sandbox level.
        Returns the result dict.
        """
        image = self._ensure_image()
        # Prepare environment variables to pass to the container
        environment = {
            "SKILL_CODE": skill_code,
            "INPUT": json.dumps(input_data),
            "CONFIG": json.dumps(config),
        }

        if sandbox_level == "skill":
            # Run a fresh container that exits immediately
            container = self.docker_client.containers.run(
                image=image,
                environment=environment,
                network=self.network,
                detach=True,
                remove=True,
                mem_limit="128m",
                cpu_shares=512,
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"},
            )
            # Wait for completion and get logs
            exit_code = container.wait()
            logs = container.logs(stdout=True, stderr=True).decode()
            container.remove()
            # Parse the output (expected JSON)
            try:
                # The runner script should print a JSON result on stdout
                result = json.loads(logs.strip().split("\n")[-1])
                return result
            except Exception as e:
                logger.error(f"Failed to parse skill output: {e}")
                return {"error": f"Skill execution failed: {logs}"}

        elif sandbox_level == "task":
            # Reuse a container for the duration of the task
            container_id = self.task_containers.get(task_id)
            if not container_id:
                # Create a new container for this task
                container = self.docker_client.containers.run(
                    image=image,
                    environment=environment,
                    network=self.network,
                    detach=True,
                    mem_limit="256m",
                    cpu_shares=512,
                    read_only=False,  # we might need to write temporary files
                    tmpfs={"/tmp": "rw,noexec,nosuid,size=128m"},
                    name=f"hivebot_task_{task_id}",
                )
                self.task_containers[task_id] = container.id
                container_id = container.id
            else:
                # Reuse existing container
                container = self.docker_client.containers.get(container_id)
                # Restart if stopped
                if container.status != "running":
                    container.start()

            # Execute the skill in the existing container
            # We'll use exec to run the runner with the new environment
            exec_cmd = ["python", "/runner.py"]
            exec_instance = self.docker_client.api.exec_create(
                container_id,
                exec_cmd,
                environment=environment,
            )
            output = self.docker_client.api.exec_start(exec_instance["Id"])
            exit_code = self.docker_client.api.exec_inspect(exec_instance["Id"])["ExitCode"]
            try:
                result = json.loads(output.decode().strip().split("\n")[-1])
                return result
            except Exception as e:
                logger.error(f"Failed to parse skill output: {e}")
                return {"error": f"Skill execution failed: {output.decode()}"}

        elif sandbox_level == "project":
            # Reuse a container per project, with a persistent volume
            container_id = self.project_containers.get(project_id)
            if not container_id:
                # Create a volume for the project
                volume_name = f"hivebot_project_{project_id}"
                try:
                    self.docker_client.volumes.get(volume_name)
                except docker.errors.NotFound:
                    self.docker_client.volumes.create(volume_name)
                # Create container with volume mounted
                container = self.docker_client.containers.run(
                    image=image,
                    environment=environment,
                    network=self.network,
                    detach=True,
                    mem_limit="512m",
                    cpu_shares=1024,
                    volumes={volume_name: {"bind": "/data", "mode": "rw"}},
                    name=f"hivebot_project_{project_id}",
                )
                self.project_containers[project_id] = container.id
                container_id = container.id
            else:
                container = self.docker_client.containers.get(container_id)
                if container.status != "running":
                    container.start()

            # Execute the skill in the existing container
            exec_cmd = ["python", "/runner.py"]
            exec_instance = self.docker_client.api.exec_create(
                container_id,
                exec_cmd,
                environment=environment,
            )
            output = self.docker_client.api.exec_start(exec_instance["Id"])
            exit_code = self.docker_client.api.exec_inspect(exec_instance["Id"])["ExitCode"]
            try:
                result = json.loads(output.decode().strip().split("\n")[-1])
                return result
            except Exception as e:
                logger.error(f"Failed to parse skill output: {e}")
                return {"error": f"Skill execution failed: {output.decode()}"}

        else:
            raise ValueError(f"Unknown sandbox level: {sandbox_level}")

    async def cleanup_task(self, task_id: str):
        """Stop and remove the task container."""
        container_id = self.task_containers.pop(task_id, None)
        if container_id:
            try:
                container = self.docker_client.containers.get(container_id)
                container.stop(timeout=5)
                container.remove()
            except Exception as e:
                logger.warning(f"Failed to clean up task container {container_id}: {e}")

    async def cleanup_project(self, project_id: str, remove_volume: bool = False):
        """Stop and optionally remove the project container and its volume."""
        container_id = self.project_containers.pop(project_id, None)
        if container_id:
            try:
                container = self.docker_client.containers.get(container_id)
                container.stop(timeout=5)
                container.remove()
            except Exception as e:
                logger.warning(f"Failed to clean up project container {container_id}: {e}")
        if remove_volume:
            volume_name = f"hivebot_project_{project_id}"
            try:
                self.docker_client.volumes.get(volume_name).remove()
            except Exception as e:
                logger.warning(f"Failed to remove volume {volume_name}: {e}")


# Global instance
container_manager = ContainerManager()

import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional, Dict, Any
from ..core.config import settings
import os
import logging

logger = logging.getLogger(__name__)

class DockerService:
    def __init__(self):
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Docker client initialized")
        except DockerException as e:
            logger.error(f"Docker connection failed: {e}")
            raise

    def _ensure_image_exists(self) -> str:
        """Check if agent image exists; if not, raise error. Returns image tag."""
        image_tag = "hivebot/agent:latest"
        try:
            self.client.images.get(image_tag)
            logger.info(f"Agent image {image_tag} found.")
            return image_tag
        except NotFound:
            logger.error(f"Agent image {image_tag} not found. Please build it first using the agent-builder service or setup.sh.")
            try:
                images = self.client.images.list()
                image_names = [tag for img in images for tag in img.tags]
                logger.info(f"Available images: {image_names}")
            except Exception as e:
                logger.error(f"Failed to list images: {e}")
            raise RuntimeError(f"Agent image {image_tag} missing. Run the agent-builder service or re-run setup.sh.")
        except APIError as e:
            logger.error(f"Error checking agent image: {e}")
            raise RuntimeError(f"Failed to check agent image: {e}")

    def _set_ownership(self, path: str, uid: int):
        """Recursively change ownership of path to uid:uid."""
        for root, dirs, files in os.walk(path):
            for d in dirs:
                try:
                    os.chown(os.path.join(root, d), uid, uid)
                except Exception as e:
                    logger.warning(f"Failed to chown directory {d}: {e}")
            for f in files:
                try:
                    os.chown(os.path.join(root, f), uid, uid)
                except Exception as e:
                    logger.warning(f"Failed to chown file {f}: {e}")
        try:
            os.chown(path, uid, uid)
        except Exception as e:
            logger.warning(f"Failed to chown root directory {path}: {e}")

    def create_container(self,
                        agent_id: str,
                        user_uid: str,
                        parent_id: Optional[str] = None,
                        reporting_target: str = "PARENT_AGENT",
                        internal_api_key: str = None,
                        redis_host: str = "redis",
                        orchestrator_url: str = "http://backend:8000") -> str:
        image = self._ensure_image_exists()
        host_data_dir = settings.AGENTS_DIR / agent_id
        host_data_dir.mkdir(parents=True, exist_ok=True)

        try:
            uid_int = int(user_uid)
            self._set_ownership(str(host_data_dir), uid_int)
        except ValueError:
            logger.error(f"Invalid user_uid: {user_uid}, not an integer")
            raise RuntimeError(f"Invalid UID: {user_uid}")

        environment = {
            "AGENT_ID": agent_id,
            "PARENT_ID": parent_id or "",
            "REPORTING_TARGET": reporting_target,
            "REDIS_HOST": redis_host,
            "ORCHESTRATOR_URL": orchestrator_url,
            "INTERNAL_API_KEY": internal_api_key,
            "AGENT_UID": user_uid,
        }

        try:
            container = self.client.containers.run(
                image=image,
                name=f"hivebot_agent_{agent_id}",
                detach=True,
                network=settings.DOCKER_NETWORK,
                environment=environment,
                volumes={
                    str(host_data_dir): {"bind": "/data", "mode": "rw"}
                },
                user=f"{user_uid}:{user_uid}",
                mem_limit="128m",
                cpu_shares=512,
                restart_policy={"Name": "unless-stopped"},
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                read_only=True,
                tmpfs={"/tmp": "rw,noexec,nosuid,size=64m"}
            )
            logger.info(f"Created container {container.id} for agent {agent_id}")
            return container.id
        except APIError as e:
            logger.error(f"Docker API error creating container for agent {agent_id}: {e}")
            raise RuntimeError(f"Container creation failed: {e}")

    def get_container_status(self, container_id: str) -> str:
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except NotFound:
            return "not_found"
        except APIError as e:
            logger.error(f"Error getting container {container_id}: {e}")
            return "unknown"

    def stop_container(self, container_id: str):
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=5)
            container.remove()
            logger.info(f"Removed container {container_id}")
        except NotFound:
            logger.warning(f"Container {container_id} not found")
        except APIError as e:
            logger.error(f"Error stopping container {container_id}: {e}")

    def list_containers(self) -> Dict[str, Dict[str, Any]]:
        try:
            containers = self.client.containers.list(all=True, filters={"name": "hivebot_agent_"})
            result = {}
            for c in containers:
                if c.name.startswith("hivebot_agent_"):
                    agent_id = c.name[14:]  # len("hivebot_agent_") = 14
                    result[agent_id] = {
                        "id": c.id,
                        "status": c.status,
                        "created": c.attrs["Created"],
                    }
            return result
        except APIError as e:
            logger.error(f"Failed to list containers: {e}")
            return {}

    def get_container_status_by_name(self, container_name: str) -> str:
        try:
            container = self.client.containers.get(container_name)
            return container.status
        except NotFound:
            return "not_found"
        except APIError as e:
            logger.error(f"Error getting container {container_name}: {e}")
            return "unknown"

    def start_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.start()
            logger.info(f"Started container {container_name}")
        except NotFound:
            logger.error(f"Container {container_name} not found")
            raise RuntimeError(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error starting container {container_name}: {e}")
            raise

    def stop_container_by_name(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.stop(timeout=5)
            logger.info(f"Stopped container {container_name}")
        except NotFound:
            logger.warning(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error stopping container {container_name}: {e}")
            raise

    def restart_container(self, container_name: str):
        try:
            container = self.client.containers.get(container_name)
            container.restart(timeout=5)
            logger.info(f"Restarted container {container_name}")
        except NotFound:
            logger.error(f"Container {container_name} not found")
            raise RuntimeError(f"Container {container_name} not found")
        except APIError as e:
            logger.error(f"Error restarting container {container_name}: {e}")
            raise

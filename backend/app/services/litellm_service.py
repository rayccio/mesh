import logging
from typing import List, Dict, Any
from ..core.config import settings
import litellm
from litellm import acompletion

logger = logging.getLogger(__name__)

async def generate_with_messages(messages: List[Dict[str, str]], config: Dict[str, Any]) -> str:
    """
    Generate a response using LiteLLM with a list of messages.
    config must contain a 'model' string in the format "provider/model" (e.g., "openai/gpt-4o").
    """
    if "model" not in config:
        raise ValueError("Missing 'model' in generation config")

    model = config["model"].replace(":", "/")  # ensure litellm format
    provider = model.split("/")[0]
    api_key = settings.secrets.get(f"PROVIDER_API_KEY_{provider.upper()}")

    litellm.api_key = api_key

    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 200)
    top_p = config.get("top_p", 1.0)

    # Log the messages being sent (for debugging)
    logger.info(f"LiteLLM call with model={model}, messages={messages}")

    try:
        response = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"LiteLLM call failed: {e}")
        raise

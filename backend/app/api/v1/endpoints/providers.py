from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Optional
from ....models.types import (
    GlobalProviderConfig, ProviderConfigUpdate, ProviderStatusResponse,
    ProviderConfig, ProviderModel
)
from ....core.config import settings
from ....known_providers import KNOWN_PROVIDERS
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

def get_provider_config() -> GlobalProviderConfig:
    config_data = settings.secrets.get("PROVIDER_CONFIG")
    if config_data:
        return GlobalProviderConfig(**config_data)
    return GlobalProviderConfig()

def save_provider_config(config: GlobalProviderConfig):
    settings.secrets.set("PROVIDER_CONFIG", config.dict())

@router.get("", response_model=ProviderStatusResponse)
async def get_providers():
    config = get_provider_config()
    # Dynamically set api_key_present based on actual key presence in secrets
    primary_model_id = None
    utility_model_id = None
    for provider_key, provider in config.providers.items():
        key = settings.secrets.get(f"PROVIDER_API_KEY_{provider_key.upper()}")
        provider.api_key_present = key is not None
        # Find primary and utility for response
        for model_id, model in provider.models.items():
            if model.enabled and model.is_primary:
                primary_model_id = f"{provider_key}:{model_id}"
            if model.enabled and model.is_utility:
                utility_model_id = f"{provider_key}:{model_id}"
    return ProviderStatusResponse(
        providers=config.providers,
        primary_model_id=primary_model_id,
        utility_model_id=utility_model_id
    )

@router.post("", response_model=ProviderStatusResponse)
async def update_provider(update: ProviderConfigUpdate):
    config = get_provider_config()
    provider_key = update.provider

    # If provider doesn't exist, create a default entry from known_providers
    if provider_key not in config.providers:
        known = next((kp for kp in KNOWN_PROVIDERS if kp["name"] == provider_key), None)
        if known:
            display_name = known["display_name"]
            models = {}
            for m in known["models"]:
                models[m["id"]] = ProviderModel(
                    id=m["id"],
                    name=m["name"],
                    enabled=True,  # enable all by default? Or only default primary/utility?
                    is_primary=m.get("default_primary", False),
                    is_utility=m.get("default_utility", False)
                )
            config.providers[provider_key] = ProviderConfig(
                name=provider_key,
                display_name=display_name,
                enabled=False,
                api_key_present=False,
                models=models
            )
        else:
            # If unknown provider, create empty entry
            config.providers[provider_key] = ProviderConfig(
                name=provider_key,
                display_name=provider_key.capitalize(),
                enabled=False,
                api_key_present=False,
                models={}
            )

    provider = config.providers[provider_key]

    if update.enabled is not None:
        provider.enabled = update.enabled

    if update.api_key is not None:
        if update.api_key:
            settings.secrets.set(f"PROVIDER_API_KEY_{provider_key.upper()}", update.api_key)
            provider.api_key_present = True
        else:
            settings.secrets.set(f"PROVIDER_API_KEY_{provider_key.upper()}", None)
            provider.api_key_present = False

    # Track if this update explicitly sets a model as primary or utility
    new_primary_provider = None
    new_primary_model = None
    new_utility_provider = None
    new_utility_model = None

    if update.models is not None:
        for model_id, model_updates in update.models.items():
            if model_id in provider.models:
                for field, value in model_updates.dict(exclude_unset=True).items():
                    setattr(provider.models[model_id], field, value)
            else:
                provider.models[model_id] = model_updates
            # Check if this model is being set as primary or utility in this update
            if model_updates.is_primary:
                new_primary_provider = provider_key
                new_primary_model = model_id
            if model_updates.is_utility:
                new_utility_provider = provider_key
                new_utility_model = model_id

    # --- Primary enforcement ---
    # If a new primary was set in this update, clear all other primaries.
    if new_primary_provider and new_primary_model:
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if pkey == new_primary_provider and mid == new_primary_model:
                    mconf.is_primary = True
                else:
                    mconf.is_primary = False
    else:
        # No new primary explicitly set. Ensure there is exactly one primary among enabled models.
        current_primary_provider = None
        current_primary_model = None
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if mconf.is_primary and mconf.enabled:
                    current_primary_provider = pkey
                    current_primary_model = mid
                    break
            if current_primary_provider:
                break

        if current_primary_provider and current_primary_model:
            # Check if the primary model is still enabled
            primary_model = config.providers[current_primary_provider].models.get(current_primary_model)
            if not primary_model or not primary_model.enabled:
                config.providers[current_primary_provider].models[current_primary_model].is_primary = False
                current_primary_provider = None
                current_primary_model = None

        if not current_primary_provider:
            # Pick first enabled model as primary
            for pkey, pconf in config.providers.items():
                for mid, mconf in pconf.models.items():
                    if mconf.enabled:
                        mconf.is_primary = True
                        current_primary_provider = pkey
                        current_primary_model = mid
                        break
                if current_primary_provider:
                    break

    # --- Utility enforcement (similar logic) ---
    if new_utility_provider and new_utility_model:
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if pkey == new_utility_provider and mid == new_utility_model:
                    mconf.is_utility = True
                else:
                    mconf.is_utility = False
    else:
        current_utility_provider = None
        current_utility_model = None
        for pkey, pconf in config.providers.items():
            for mid, mconf in pconf.models.items():
                if mconf.is_utility and mconf.enabled:
                    current_utility_provider = pkey
                    current_utility_model = mid
                    break
            if current_utility_provider:
                break

        if current_utility_provider and current_utility_model:
            utility_model = config.providers[current_utility_provider].models.get(current_utility_model)
            if not utility_model or not utility_model.enabled:
                config.providers[current_utility_provider].models[current_utility_model].is_utility = False
                current_utility_provider = None
                current_utility_model = None

        if not current_utility_provider:
            for pkey, pconf in config.providers.items():
                for mid, mconf in pconf.models.items():
                    if mconf.enabled:
                        mconf.is_utility = True
                        current_utility_provider = pkey
                        current_utility_model = mid
                        break
                if current_utility_provider:
                    break

    save_provider_config(config)
    # After saving, recompute api_key_present dynamically for the response
    for pkey, pconf in config.providers.items():
        key = settings.secrets.get(f"PROVIDER_API_KEY_{pkey.upper()}")
        pconf.api_key_present = key is not None

    # Build response
    primary_model_id = None
    utility_model_id = None
    for pkey, pconf in config.providers.items():
        for mid, mconf in pconf.models.items():
            if mconf.enabled and mconf.is_primary:
                primary_model_id = f"{pkey}:{mid}"
            if mconf.enabled and mconf.is_utility:
                utility_model_id = f"{pkey}:{mid}"

    return ProviderStatusResponse(
        providers=config.providers,
        primary_model_id=primary_model_id,
        utility_model_id=utility_model_id
    )

@router.delete("/{provider}", status_code=204)
async def delete_provider(provider: str):
    config = get_provider_config()
    if provider in config.providers:
        del config.providers[provider]
        settings.secrets.set(f"PROVIDER_API_KEY_{provider.upper()}", None)
        save_provider_config(config)
    return None

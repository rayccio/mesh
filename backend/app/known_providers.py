# backend/app/known_providers.py
KNOWN_PROVIDERS = [
    {
        "name": "openai",
        "display_name": "OpenAI",
        "models": [
            {"id": "gpt-4o", "name": "GPT-4o", "default_primary": True, "default_utility": False},
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "default_primary": False, "default_utility": True},
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo", "default_primary": False, "default_utility": False},
            {"id": "gpt-4", "name": "GPT-4", "default_primary": False, "default_utility": False},
            {"id": "gpt-4-turbo", "name": "GPT-4 Turbo", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "anthropic",
        "display_name": "Anthropic",
        "models": [
            {"id": "claude-3-opus", "name": "Claude 3 Opus", "default_primary": True, "default_utility": False},
            {"id": "claude-3-sonnet", "name": "Claude 3 Sonnet", "default_primary": False, "default_utility": False},
            {"id": "claude-3-haiku", "name": "Claude 3 Haiku", "default_primary": False, "default_utility": True},
            {"id": "claude-2.1", "name": "Claude 2.1", "default_primary": False, "default_utility": False},
            {"id": "claude-instant", "name": "Claude Instant", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "gemini",
        "display_name": "Google Gemini",
        "models": [
            {"id": "gemini-1.5-pro", "name": "Gemini 1.5 Pro", "default_primary": True, "default_utility": False},
            {"id": "gemini-1.5-flash", "name": "Gemini 1.5 Flash", "default_primary": False, "default_utility": True},
            {"id": "gemini-1.0-pro", "name": "Gemini 1.0 Pro", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "deepseek",
        "display_name": "DeepSeek",
        "models": [
            {"id": "deepseek-chat", "name": "DeepSeek Chat", "default_primary": True, "default_utility": False},
            {"id": "deepseek-coder", "name": "DeepSeek Coder", "default_primary": False, "default_utility": False},
            {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "cohere",
        "display_name": "Cohere",
        "models": [
            {"id": "command-r", "name": "Command R", "default_primary": True, "default_utility": False},
            {"id": "command-r-plus", "name": "Command R+", "default_primary": False, "default_utility": False},
            {"id": "command", "name": "Command", "default_primary": False, "default_utility": True},
            {"id": "command-light", "name": "Command Light", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "mistral",
        "display_name": "Mistral AI",
        "models": [
            {"id": "mistral-large", "name": "Mistral Large", "default_primary": True, "default_utility": False},
            {"id": "mistral-medium", "name": "Mistral Medium", "default_primary": False, "default_utility": False},
            {"id": "mistral-small", "name": "Mistral Small", "default_primary": False, "default_utility": True},
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "groq",
        "display_name": "Groq",
        "models": [
            {"id": "llama3-70b", "name": "Llama 3 70B", "default_primary": True, "default_utility": False},
            {"id": "llama3-8b", "name": "Llama 3 8B", "default_primary": False, "default_utility": True},
            {"id": "mixtral-8x7b", "name": "Mixtral 8x7B", "default_primary": False, "default_utility": False},
            {"id": "gemma-7b", "name": "Gemma 7B", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "perplexity",
        "display_name": "Perplexity AI",
        "models": [
            {"id": "pplx-7b-online", "name": "7B Online", "default_primary": True, "default_utility": False},
            {"id": "pplx-70b-online", "name": "70B Online", "default_primary": False, "default_utility": True},
            {"id": "pplx-7b-chat", "name": "7B Chat", "default_primary": False, "default_utility": False},
        ]
    },
    {
        "name": "together",
        "display_name": "Together AI",
        "models": [
            {"id": "together-mix", "name": "Mix", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "fireworks",
        "display_name": "Fireworks AI",
        "models": [
            {"id": "fireworks-llama2", "name": "Llama 2", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "replicate",
        "display_name": "Replicate",
        "models": [
            {"id": "replicate-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "huggingface",
        "display_name": "Hugging Face",
        "models": [
            {"id": "hf-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "azure",
        "display_name": "Azure OpenAI",
        "models": [
            {"id": "azure-gpt4", "name": "GPT-4", "default_primary": True, "default_utility": False},
            {"id": "azure-gpt35", "name": "GPT-3.5", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "aws-bedrock",
        "display_name": "AWS Bedrock",
        "models": [
            {"id": "bedrock-claude", "name": "Claude", "default_primary": True, "default_utility": False},
            {"id": "bedrock-llama2", "name": "Llama 2", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "grok",
        "display_name": "xAI Grok",
        "models": [
            {"id": "grok-1", "name": "Grok-1", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "qwen",
        "display_name": "Qwen (Alibaba)",
        "models": [
            {"id": "qwen-72b", "name": "Qwen 72B", "default_primary": True, "default_utility": False},
            {"id": "qwen-14b", "name": "Qwen 14B", "default_primary": False, "default_utility": True},
        ]
    },
    {
        "name": "yi",
        "display_name": "Yi (01.AI)",
        "models": [
            {"id": "yi-34b", "name": "Yi 34B", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "nvidia",
        "display_name": "NVIDIA",
        "models": [
            {"id": "nemotron", "name": "Nemotron", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "ibm",
        "display_name": "IBM Watsonx",
        "models": [
            {"id": "granite", "name": "Granite", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "oracle",
        "display_name": "Oracle OCI",
        "models": [
            {"id": "oci-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
    {
        "name": "sambanova",
        "display_name": "SambaNova",
        "models": [
            {"id": "sambanova-default", "name": "Default", "default_primary": True, "default_utility": True},
        ]
    },
]

"""Resolve Azure OpenAI or OpenAI settings from the environment."""

import os


def provider_configuration() -> dict[str, str] | None:
    if all(
        os.getenv(name)
        for name in (
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_CHAT_MODEL",
        )
    ):
        return {
            "api_key": os.environ["AZURE_OPENAI_API_KEY"],
            "azure_endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
            "model": os.environ["AZURE_OPENAI_CHAT_MODEL"],
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "preview"),
        }
    if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_MODEL"):
        config = {
            "api_key": os.environ["OPENAI_API_KEY"],
            "model": os.environ["OPENAI_MODEL"],
        }
        if os.getenv("OPENAI_BASE_URL"):
            config["base_url"] = os.environ["OPENAI_BASE_URL"]
        return config
    return None

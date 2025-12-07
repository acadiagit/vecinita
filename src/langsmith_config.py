"""
LangSmith Configuration Module

This module handles the initialization and configuration of LangSmith for tracing,
evaluating, and monitoring agent runs. LangSmith provides comprehensive observability
into LLM applications.

Environment Variables:
    LANGSMITH_TRACING (bool): Enable/disable tracing (default: false)
    LANGSMITH_ENDPOINT (str): LangSmith API endpoint
    LANGSMITH_API_KEY (str): LangSmith API key
    LANGSMITH_PROJECT (str): Project name for organizing runs

Reference:
    https://docs.smith.langchain.com/
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def initialize_langsmith() -> dict:
    """
    Initialize LangSmith configuration from environment variables.

    Sets up LangSmith tracing and monitoring for all LangChain/LanGraph operations.
    When enabled, all agent runs will be automatically traced to the configured project.

    Returns:
        dict: Configuration dictionary with LangSmith settings and status.
              Keys:
                - tracing_enabled (bool): Whether tracing is active
                - endpoint (str): LangSmith API endpoint
                - project (str): Project name for organizing runs
                - status (str): Configuration status message

    Note:
        The environment variables are automatically picked up by LangChain when:
        - LANGSMITH_TRACING=true
        - LANGSMITH_API_KEY is set
        - LANGSMITH_ENDPOINT is configured
    """

    # Read configuration from environment
    tracing_enabled = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
    endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")
    api_key = os.getenv("LANGSMITH_API_KEY", "")
    project = os.getenv("LANGSMITH_PROJECT", "default")

    config = {
        "tracing_enabled": tracing_enabled,
        "endpoint": endpoint,
        "project": project,
        "status": "not_configured"
    }

    # Validate configuration
    if tracing_enabled:
        if not api_key:
            config["status"] = "error: LANGSMITH_API_KEY not set"
            print(
                "[ERROR] LangSmith tracing enabled but LANGSMITH_API_KEY is not set"
            )
        else:
            config["status"] = "configured"
            print(
                f"[INFO] LangSmith tracing enabled for project '{project}'"
            )
    else:
        config["status"] = "tracing_disabled"
        print("[INFO] LangSmith tracing is disabled")

    return config


def get_langsmith_config() -> dict:
    """
    Get the current LangSmith configuration.

    Returns:
        dict: Current LangSmith configuration settings.
    """
    return {
        "tracing_enabled": os.getenv("LANGSMITH_TRACING", "false").lower() == "true",
        "endpoint": os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
        "project": os.getenv("LANGSMITH_PROJECT", "default"),
        "api_key_set": bool(os.getenv("LANGSMITH_API_KEY", "")),
    }


# Initialize on module import
langsmith_config = initialize_langsmith()

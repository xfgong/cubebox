"""
cubebox Configuration Management

Uses dynaconf for environment-based configuration with support for:
- YAML configuration files
- Environment variable overrides
- Development/production/testing environments
"""

import os

import dynaconf

# Load configuration based on environment
env = os.getenv("ENV_FOR_DYNACONF", "development")
settings_files = [
    "config.yaml",  # Base configuration
    f"config.{env}.yaml",
    f"config.{env}.local.yaml",
]

config = dynaconf.Dynaconf(
    env=env,
    envvar_prefix="CUBEBOX",
    environments=True,
    settings_files=settings_files,
    load_dotenv=True,
)

"""
cubebox Configuration Management

Uses dynaconf for environment-based configuration with support for:
- YAML configuration files
- Environment variable overrides
- Development/production/testing environments
"""

import os
from pathlib import Path

import dynaconf

# Get the backend directory (where config files are located)
backend_dir = Path(__file__).parent.parent

# Load configuration based on environment
env = os.getenv("ENV_FOR_DYNACONF", "development")
settings_files = [
    str(backend_dir / "config.yaml"),  # Base configuration
    str(backend_dir / f"config.{env}.yaml"),
]

config = dynaconf.Dynaconf(
    env=env,
    environments=True,
    envvar_prefix="CUBEBOX",
    settings_files=settings_files,
    load_dotenv=True,
)

"""Local Pisama path and permission helpers."""

import os
from pathlib import Path


def get_config_dir() -> Path:
    """Return the configured Pisama data root, preserving the legacy default."""
    configured = os.environ.get("PISAMA_CONFIG_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".claude" / "pisama"


def ensure_private_directory(path: Path) -> None:
    """Create a directory and restrict it to the current user."""
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    path.chmod(0o700)


def write_private_text(path: Path, content: str) -> None:
    """Write a file with user-only read and write permissions."""
    ensure_private_directory(path.parent)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.chmod(path, 0o600)
        with os.fdopen(descriptor, "w") as target:
            descriptor = -1
            target.write(content)
    finally:
        if descriptor >= 0:
            os.close(descriptor)

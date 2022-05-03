"""Get version."""
import os


def string() -> str:
    """Version string."""
    version = None
    with open(os.path.dirname(__file__) + "/VERSION", "r", encoding="utf-8") as handle:
        version = handle.read().strip()
    if version:
        return version
    return "unknown (git checkout)"

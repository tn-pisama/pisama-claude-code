"""PISAMA Claude Code Integration - Trace capture, failure detection, and self-healing."""

__version__ = "0.3.2"

# Lazy imports to avoid loading everything at startup
def install(force: bool = False):
    """Install PISAMA hooks to ~/.claude/hooks/."""
    from .install import install as _install
    return _install(force=force)


def uninstall():
    """Remove PISAMA hooks from ~/.claude/hooks/."""
    from .install import uninstall as _uninstall
    return _uninstall()


__all__ = ["install", "uninstall", "__version__"]

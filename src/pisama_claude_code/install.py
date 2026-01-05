#!/usr/bin/env python3
"""PISAMA Claude Code Installer.

Installs trace capture hooks into ~/.claude/.
"""

import json
import stat
import sys
from pathlib import Path


HOOK_TEMPLATE = '''#!{python_path}
"""Auto-generated PISAMA capture hook."""

from pisama_claude_code.hooks.capture_hook import main
main()
'''


def install(force: bool = False):
    """Install PISAMA hooks to ~/.claude/hooks/.

    Args:
        force: Overwrite existing hooks if True
    """
    claude_dir = Path.home() / ".claude"
    hooks_dir = claude_dir / "hooks"
    pisama_dir = claude_dir / "pisama"

    # Ensure directories exist
    hooks_dir.mkdir(parents=True, exist_ok=True)
    pisama_dir.mkdir(parents=True, exist_ok=True)
    (pisama_dir / "traces").mkdir(exist_ok=True)

    # Use the Python executable that has pisama_claude_code installed
    python_path = sys.executable

    # Install capture hook
    hook_path = hooks_dir / "pisama-capture.py"
    if hook_path.exists() and not force:
        print(f"Skipping pisama-capture.py (exists, use --force to overwrite)")
    else:
        content = HOOK_TEMPLATE.format(python_path=python_path)
        hook_path.write_text(content)
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("Installed pisama-capture.py")

    # Install shell wrappers
    _install_shell_hooks(hooks_dir, force)

    # Install minimal config, preserving connection settings
    config_path = pisama_dir / "config.json"
    default_config = {}

    if config_path.exists():
        # Preserve existing config (especially connection settings)
        try:
            existing = json.loads(config_path.read_text())
            default_config = existing
        except json.JSONDecodeError:
            pass

    if not config_path.exists():
        config_path.write_text(json.dumps(default_config, indent=2))
        print("Installed default config")

    # Update settings.local.json
    _update_settings(claude_dir, hooks_dir)

    print("\nPISAMA installation complete!")
    print(f"Hooks installed to: {hooks_dir}")
    print(f"Traces will be stored in: {pisama_dir / 'traces'}")
    print("\nNext steps:")
    print("  1. Add hooks to settings.local.json (see above)")
    print("  2. Run 'pisama-cc connect --api-key <key>' to enable analysis")


def _install_shell_hooks(hooks_dir: Path, force: bool):
    """Install shell wrapper hooks."""
    # Pre-hook shell script
    pre_script = '''#!/bin/bash
# PISAMA Pre-hook - capture tool calls
PISAMA_HOOK_TYPE=pre ~/.claude/hooks/pisama-capture.py
'''

    pre_path = hooks_dir / "pisama-pre.sh"
    if not pre_path.exists() or force:
        pre_path.write_text(pre_script)
        pre_path.chmod(pre_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("Installed pisama-pre.sh")

    # Post-hook shell script
    post_script = '''#!/bin/bash
# PISAMA Post-hook - capture tool results
PISAMA_HOOK_TYPE=post ~/.claude/hooks/pisama-capture.py
'''

    post_path = hooks_dir / "pisama-post.sh"
    if not post_path.exists() or force:
        post_path.write_text(post_script)
        post_path.chmod(post_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("Installed pisama-post.sh")


def _update_settings(claude_dir: Path, hooks_dir: Path):
    """Update settings.local.json with hook configuration."""
    settings_path = claude_dir / "settings.local.json"

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}

    # Check if hooks already configured
    hooks = settings.get("hooks", {})

    if "PreToolCall" not in hooks:
        print("\nNote: Add the following to your settings.local.json hooks:")
        print('''
  "hooks": {
    "PreToolCall": [
      {
        "command": "~/.claude/hooks/pisama-pre.sh",
        "timeout": 2000
      }
    ],
    "PostToolCall": [
      {
        "command": "~/.claude/hooks/pisama-post.sh",
        "timeout": 2000
      }
    ]
  }
''')


def uninstall():
    """Uninstall PISAMA hooks from ~/.claude/hooks/."""
    hooks_dir = Path.home() / ".claude" / "hooks"

    hooks = [
        "pisama-capture.py",
        "pisama-pre.sh",
        "pisama-post.sh",
    ]

    for filename in hooks:
        hook_path = hooks_dir / filename
        if hook_path.exists():
            hook_path.unlink()
            print(f"Removed {filename}")

    print("\nPISAMA hooks uninstalled.")
    print("Note: Config and traces in ~/.claude/pisama/ were preserved.")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="PISAMA Claude Code Installer")
    parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing hooks")
    parser.add_argument("--uninstall", "-u", action="store_true", help="Uninstall hooks")

    args = parser.parse_args()

    if args.uninstall:
        uninstall()
    else:
        install(force=args.force)


if __name__ == "__main__":
    main()

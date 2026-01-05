# Contributing to pisama-claude-code

Thank you for your interest in contributing to pisama-claude-code! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Your environment (OS, Python version, Claude Code version)
- Any relevant logs or error messages

### Suggesting Features

Feature requests are welcome! Please:

- Check if the feature has already been requested
- Provide a clear description of the feature
- Explain the use case and why it would be valuable
- Consider if it fits the project's scope (lightweight trace capture)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- Claude Code CLI installed

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/pisama-claude-code.git
cd pisama-claude-code

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pisama_claude_code --cov-report=html

# Run specific test file
pytest tests/test_cli.py -v
```

### Code Style

We use [Ruff](https://github.com/astral-sh/ruff) for linting and formatting:

```bash
# Check linting
ruff check src/

# Auto-fix issues
ruff check --fix src/

# Format code
ruff format src/
```

### Type Checking

```bash
# Run mypy
mypy src/pisama_claude_code/
```

## Project Structure

```
pisama-claude-code/
├── src/
│   └── pisama_claude_code/
│       ├── __init__.py      # Package initialization
│       ├── cli.py           # CLI commands (Click)
│       ├── adapter.py       # Trace capture adapter
│       ├── storage.py       # SQLite storage backend
│       ├── trace_types.py   # Pydantic models
│       ├── trace_converter.py
│       ├── guardian.py      # Self-healing guardian
│       ├── install.py       # Hook installation
│       └── hooks/           # Claude Code hooks
│           ├── capture_hook.py
│           └── guardian_hook.py
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_cli.py
│   ├── test_storage.py
│   ├── test_adapter.py
│   └── test_guardian.py
├── pyproject.toml
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
└── py.typed
```

## Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add cost breakdown by date range
fix: handle empty trace files gracefully
docs: update CLI usage examples
```

## Release Process

Releases are managed by maintainers:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create a GitHub release with tag `vX.Y.Z`
4. GitHub Actions automatically publishes to PyPI

## Getting Help

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues and discussions first

## Recognition

Contributors are recognized in:
- GitHub's contributor list
- Release notes for significant contributions

Thank you for contributing!

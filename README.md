# pisama-claude-code

> Lightweight trace capture for Claude Code sessions with token usage and cost tracking.

[![PyPI version](https://img.shields.io/pypi/v/pisama-claude-code.svg)](https://pypi.org/project/pisama-claude-code/)
[![GitHub stars](https://img.shields.io/github/stars/tn-pisama/pisama-claude-code?style=social)](https://github.com/tn-pisama/pisama-claude-code)
[![Python versions](https://img.shields.io/pypi/pyversions/pisama-claude-code.svg)](https://pypi.org/project/pisama-claude-code/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/tn-pisama/pisama-claude-code/actions/workflows/ci.yml/badge.svg)](https://github.com/tn-pisama/pisama-claude-code/actions/workflows/ci.yml)
[![Downloads](https://static.pepy.tech/badge/pisama-claude-code)](https://pepy.tech/project/pisama-claude-code)
[![Downloads/month](https://img.shields.io/pypi/dm/pisama-claude-code)](https://pypistats.org/packages/pisama-claude-code)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## Demo

![pisama-claude-code demo](assets/demo.gif)

## Why PISAMA?

When working with Claude Code, have you ever wondered:

- **How much did that session cost?** Track token usage and costs in real-time
- **What tools were called?** See every Bash, Read, Write, and Edit operation
- **Why did it fail?** Capture traces for debugging and forensics
- **Can I export my sessions?** JSONL export for analysis or compliance

**pisama-claude-code** captures everything Claude Code does, locally and privately.

```
┌─────────────────────┐         ┌─────────────────────┐
│   Claude Code       │         │   PISAMA Platform   │
│   + pisama-cc       │ ──────▶ │   (optional)        │
│   (capture)         │  sync   │   - detection       │
└─────────────────────┘         │   - self-healing    │
        │                       └─────────────────────┘
        │
        ▼
   ~/.claude/pisama/traces/
   (local storage)
```

## Installation

```bash
pip install pisama-claude-code
```

**Requirements:** Python 3.10+ and [Claude Code CLI](https://claude.ai/code)

## Quick Start

```bash
# 1. Install capture hooks
pisama-cc install

# 2. Use Claude Code normally - traces are captured automatically

# 3. View your session data
pisama-cc status        # Summary with token totals and cost
pisama-cc traces        # Recent tool calls
pisama-cc usage         # Detailed breakdown
```

## Features

### Token & Cost Tracking

```bash
$ pisama-cc usage --by-model --by-tool

📊 Token Usage Summary (last 100 traces)
==================================================
Input tokens:           10,234
Output tokens:          85,421
Cache read tokens:   1,234,567
Total cost:        $    52.34

📈 By Model:
--------------------------------------------------
  claude-opus-4-5-20251101            $52.34

🔧 By Tool:
--------------------------------------------------
  Bash                   45 calls  $25.12
  Read                   30 calls  $15.34
  Write                  20 calls  $8.45
  Edit                   5 calls   $3.43
```

### Session Status

```bash
$ pisama-cc status

📊 PISAMA Status
========================================

🔧 Hook Installation:
   ✅ pisama-capture.py
   ✅ pisama-pre.sh
   ✅ pisama-post.sh
   All hooks installed

📁 Local Traces: 1,400
   Input tokens:  9,580
   Output tokens: 79,569
   Total cost:    $43.22
```

### Export & Analysis

```bash
# Export to JSONL
pisama-cc export -o traces.jsonl

# Export compressed
pisama-cc export -o traces.jsonl.gz --compress

# Export to OpenTelemetry format
pisama-cc export --format otel -o traces-otel.json

# Filter by date range
pisama-cc traces --since 2025-01-01 --until 2025-01-04
```

### OpenTelemetry Integration

Export traces to any OTEL-compatible backend (Jaeger, Honeycomb, Datadog, etc.):

```bash
# Install OTEL support
pip install pisama-claude-code[otel]

# Export to local Jaeger
pisama-cc export-otel -e http://localhost:4318/v1/traces

# Export to Honeycomb
pisama-cc export-otel -e https://api.honeycomb.io/v1/traces \
    -H "x-honeycomb-team=YOUR_API_KEY"

# Export to file in OTEL format
pisama-cc export --format otel -o traces.json
```

OTEL export uses [GenAI semantic conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/) for token usage, costs, and model attributes.

## CLI Reference

| Command | Description |
|---------|-------------|
| `pisama-cc install` | Install capture hooks to `~/.claude/hooks/` |
| `pisama-cc uninstall` | Remove hooks |
| `pisama-cc status` | Show status, token totals, and cost |
| `pisama-cc traces` | View recent traces (`-v` for verbose, `-c` for content) |
| `pisama-cc usage` | Token usage breakdown (`--by-model`, `--by-tool`) |
| `pisama-cc export` | Export to JSONL or OTEL (`--format otel`, `--compress`) |
| `pisama-cc export-otel` | Export to OpenTelemetry collector (`-e ENDPOINT`) |
| `pisama-cc connect` | Connect to PISAMA platform (optional) |
| `pisama-cc sync` | Upload traces to platform |
| `pisama-cc analyze` | Run failure detection (requires platform) |
| `pisama-cc vault status` | Show PII tokenization vault status |

## Model Pricing

Supported models and pricing (per 1M tokens):

| Model | Input | Output | Cache Read |
|-------|-------|--------|------------|
| claude-opus-4-5 | $15.00 | $75.00 | $1.50 |
| claude-sonnet-4 | $3.00 | $15.00 | $0.30 |
| claude-3-5-sonnet | $3.00 | $15.00 | $0.30 |
| claude-3-5-haiku | $0.80 | $4.00 | $0.08 |

## Privacy & Security

- **Local-first**: All traces stored in `~/.claude/pisama/traces/`
- **Secrets redacted**: API keys, passwords, and tokens are automatically removed
- **Paths anonymized**: Home directory paths replaced with `~`
- **Platform sync is opt-in**: Nothing leaves your machine without explicit action

See [SECURITY.md](SECURITY.md) for our security policy.

## Configuration

After installation, the hooks are automatically configured. To customize, edit `~/.claude/settings.local.json`:

```json
{
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
}
```

## Platform Integration (Optional)

For advanced features like failure detection and self-healing, connect to the PISAMA platform:

```bash
pisama-cc connect        # Authenticate
pisama-cc sync           # Upload traces
pisama-cc analyze        # Run detection
```

Platform features:
- 28 MAST failure mode detection
- AI-powered fix suggestions
- Self-healing automation
- Visual dashboard

## Part of the PISAMA Platform

`pisama-claude-code` is the Claude Code integration for the broader **PISAMA (Platform for Intelligent Self-healing AI Multi-Agent) Testing Platform**, which supports multiple agent frameworks:

| Framework | Package | Status |
|-----------|---------|--------|
| Claude Code | `pisama-claude-code` | Stable |
| LangChain/LangGraph | `mao-testing` SDK | Available |
| CrewAI | `mao-testing` SDK | Available |
| AutoGen | `mao-testing` SDK | Available |
| n8n | `mao-testing` SDK | Available |

For other frameworks, see the [mao-testing SDK](https://github.com/tn-pisama/mao-testing).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

```bash
# Development setup
git clone https://github.com/tn-pisama/pisama-claude-code.git
cd pisama-claude-code
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://pisama.dev/docs/claude-code)
- [PISAMA Platform](https://pisama.dev)
- [Issue Tracker](https://github.com/tn-pisama/pisama-claude-code/issues)
- [Discussions](https://github.com/tn-pisama/pisama-claude-code/discussions)

---

<p align="center">
  Made with ❤️ for the Claude Code community
</p>

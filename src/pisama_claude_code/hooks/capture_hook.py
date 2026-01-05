#!/usr/bin/env python3
"""PISAMA Trace Capture Hook - Captures all Claude Code tool calls for forensics.

This hook runs on tool calls to capture trace data for analysis.
It stores traces in both SQLite (for querying) and JSONL (for archival).

Now includes:
- AI response capture from transcript
- Token usage tracking
- Cost calculation
- PII tokenization (optional, configurable)

Usage:
    Install in ~/.claude/hooks/ and configure in settings.local.json
"""

import json
import os
import sys
from typing import Any

# PII Tokenization configuration
TOKENIZATION_ENABLED = os.environ.get("PISAMA_TOKENIZATION", "1") == "1"
TOKENIZATION_FIELDS = ["tool_input", "tool_output", "ai_response"]

# Claude model pricing (per 1M tokens) - as of Jan 2025
MODEL_PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00, "cache_read": 0.30},
    "claude-opus-4-5-20251101": {"input": 15.00, "output": 75.00, "cache_read": 1.50},
    "claude-3-5-sonnet-20241022": {"input": 3.00, "output": 15.00, "cache_read": 0.30},
    "claude-3-5-haiku-20241022": {"input": 0.80, "output": 4.00, "cache_read": 0.08},
    # Fallback for unknown models
    "default": {"input": 3.00, "output": 15.00, "cache_read": 0.30},
}


def calculate_cost(model: str, usage: dict) -> float:
    """Calculate cost in USD from token usage."""
    pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    cache_create = usage.get("cache_creation_input_tokens", 0)

    # Cache creation costs same as input
    cost = (
        (input_tokens / 1_000_000) * pricing["input"] +
        (output_tokens / 1_000_000) * pricing["output"] +
        (cache_read / 1_000_000) * pricing["cache_read"] +
        (cache_create / 1_000_000) * pricing["input"]
    )
    return round(cost, 6)


def get_tokenizer(session_id: str) -> Any:
    """Get a Tokenizer instance for PII protection.

    Returns None if tokenization is disabled or unavailable.
    """
    if not TOKENIZATION_ENABLED:
        return None

    try:
        from pisama_core.tokenization import Tokenizer
        return Tokenizer(
            session_id=session_id,
            enabled=True,
            fail_open=True,  # Don't fail if tokenization has issues
        )
    except ImportError:
        return None
    except Exception:
        return None


def tokenize_trace_data(
    trace: dict,
    session_id: str,
    fields: list[str] | None = None,
) -> dict:
    """Tokenize sensitive fields in trace data.

    Args:
        trace: The trace dictionary to tokenize.
        session_id: Session ID for token scoping.
        fields: Fields to tokenize (defaults to TOKENIZATION_FIELDS).

    Returns:
        Trace with PII tokenized (or original if tokenization unavailable).
    """
    if not TOKENIZATION_ENABLED:
        return trace

    tokenizer = get_tokenizer(session_id)
    if tokenizer is None:
        return trace

    fields = fields or TOKENIZATION_FIELDS
    result = trace.copy()

    try:
        for field in fields:
            if field in result and result[field]:
                value = result[field]
                if isinstance(value, str):
                    result[field] = tokenizer.tokenize_string(value)
                elif isinstance(value, dict):
                    result[field] = tokenizer.tokenize_dict(value)
        return result
    except Exception:
        # Fail open - return original trace if tokenization fails
        return trace
    finally:
        try:
            tokenizer.close()
        except Exception:
            pass


def get_last_assistant_message(transcript_path: str) -> dict:
    """Read transcript and get the last assistant message with usage."""
    try:
        from pathlib import Path
        transcript = Path(transcript_path)
        if not transcript.exists():
            return {}

        # Read last 20 lines to find most recent assistant message
        with open(transcript) as f:
            lines = f.readlines()[-20:]

        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant" and "message" in entry:
                    msg = entry["message"]
                    return {
                        "model": msg.get("model"),
                        "usage": msg.get("usage", {}),
                        "content": msg.get("content", []),
                        "stop_reason": msg.get("stop_reason"),
                    }
            except json.JSONDecodeError:
                continue
        return {}
    except Exception:
        return {}


def main():
    """Main hook entry point."""
    # Determine hook type from environment or argv
    hook_type = os.environ.get("PISAMA_HOOK_TYPE", "unknown")
    if len(sys.argv) > 1:
        hook_type = sys.argv[1]

    # Read hook input from stdin
    try:
        raw_input = sys.stdin.read()
        if raw_input.strip():
            hook_data = json.loads(raw_input)
        else:
            hook_data = {}
    except json.JSONDecodeError:
        hook_data = {"raw": raw_input}
    except Exception as e:
        hook_data = {"error": str(e)}

    try:
        # Import and use pisama_claude_code for capture
        from pisama_claude_code.adapter import ClaudeCodeAdapter

        adapter = ClaudeCodeAdapter()
        span = adapter.capture_span(hook_data)
        adapter.store_span(span, hook_data)

    except ImportError:
        # Fall back to basic capture
        _fallback_capture(hook_data, hook_type)
    except Exception as e:
        # Log error but don't fail
        print(f"PISAMA capture error: {e}", file=sys.stderr)

    # Always exit successfully (don't block)
    sys.exit(0)


def _fallback_capture(hook_data: dict, hook_type: str) -> None:
    """Fallback capture when pisama_claude_code is not installed.

    Provides basic trace storage without the full pisama-core stack.
    Now includes AI response, token usage, and cost tracking.
    """
    import sqlite3
    from datetime import datetime, timezone
    from pathlib import Path

    traces_dir = Path.home() / ".claude" / "pisama" / "traces"
    db_path = traces_dir / "pisama.db"

    # Ensure directory exists
    traces_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).isoformat()
    session_id = hook_data.get("session_id", os.environ.get("CLAUDE_SESSION_ID", "unknown"))
    tool_name = hook_data.get("tool_name", hook_data.get("tool", "unknown"))
    tool_input = hook_data.get("tool_input", hook_data.get("input", {}))
    tool_output = hook_data.get("tool_response", hook_data.get("tool_output"))

    # Get AI response and token usage from transcript (PostToolUse only)
    model = None
    usage = {}
    cost = 0.0
    ai_response = None

    transcript_path = hook_data.get("transcript_path")
    if transcript_path and hook_type in ("post", "PostToolUse"):
        assistant_msg = get_last_assistant_message(transcript_path)
        if assistant_msg:
            model = assistant_msg.get("model")
            usage = assistant_msg.get("usage", {})
            cost = calculate_cost(model, usage) if model and usage else 0.0
            # Extract text from content blocks
            content = assistant_msg.get("content", [])
            if isinstance(content, list):
                ai_response = " ".join(
                    block.get("text", "") for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )[:500]  # Limit to 500 chars

    # Write to JSONL
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    jsonl_path = traces_dir / f"traces-{date_str}.jsonl"

    trace = {
        "session_id": session_id,
        "timestamp": timestamp,
        "hook_type": hook_type,
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_output": tool_output,
        "working_dir": os.getcwd(),
        # New fields
        "model": model,
        "usage": usage,
        "cost_usd": cost,
        "ai_response": ai_response,
        "raw": hook_data,
    }

    # Tokenize PII before storage (PostToolUse only to avoid double-tokenization)
    if hook_type in ("post", "PostToolUse"):
        trace = tokenize_trace_data(trace, session_id)

    with open(jsonl_path, "a") as f:
        f.write(json.dumps(trace) + "\n")

    # Write to SQLite
    try:
        conn = sqlite3.connect(str(db_path))
        # Updated schema with new columns
        conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT,
                hook_type TEXT,
                tool_name TEXT,
                tool_input TEXT,
                tool_output TEXT,
                working_dir TEXT,
                model TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cache_read_tokens INTEGER,
                cost_usd REAL,
                ai_response TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_session ON traces(session_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tool ON traces(tool_name)")

        # Add columns if they don't exist (migration for existing DBs)
        for col, col_type in [
            ("model", "TEXT"),
            ("input_tokens", "INTEGER"),
            ("output_tokens", "INTEGER"),
            ("cache_read_tokens", "INTEGER"),
            ("cost_usd", "REAL"),
            ("ai_response", "TEXT"),
        ]:
            try:
                conn.execute(f"ALTER TABLE traces ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError:
                pass  # Column already exists

        # Use tokenized values from trace dict
        conn.execute("""
            INSERT INTO traces (
                session_id, timestamp, hook_type, tool_name, tool_input, tool_output,
                working_dir, model, input_tokens, output_tokens, cache_read_tokens, cost_usd, ai_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            timestamp,
            hook_type,
            tool_name,
            json.dumps(trace.get("tool_input")) if trace.get("tool_input") else None,
            json.dumps(trace.get("tool_output")) if trace.get("tool_output") else None,
            os.getcwd(),
            model,
            usage.get("input_tokens"),
            usage.get("output_tokens"),
            usage.get("cache_read_input_tokens"),
            cost,
            trace.get("ai_response"),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()

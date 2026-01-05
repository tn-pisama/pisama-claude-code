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
# Fields to tokenize - now includes input, reasoning, output
TOKENIZATION_FIELDS = [
    "tool_input",
    "tool_output",
    "user_input",      # User's prompt/message
    "reasoning",       # Extended thinking content
    "ai_output",       # Assistant's text response
    "ai_response",     # Legacy field
]

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


def extract_content_parts(content_blocks: list) -> dict:
    """Extract input, reasoning, and output from content blocks.

    Claude's response contains different block types:
    - type="thinking": Extended thinking/reasoning (antml:thinking blocks)
    - type="text": Regular text output
    - type="tool_use": Tool calls

    Returns:
        {
            "reasoning": {"content": str, "tokens": int},
            "output": {"content": str, "tokens": int},
            "tool_calls": [...]
        }
    """
    reasoning_parts = []
    output_parts = []
    tool_calls = []

    for block in content_blocks:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type", "")

        if block_type == "thinking":
            # Extended thinking block
            thinking_text = block.get("thinking", "")
            if thinking_text:
                reasoning_parts.append(thinking_text)

        elif block_type == "text":
            # Regular text output
            text = block.get("text", "")
            if text:
                output_parts.append(text)

        elif block_type == "tool_use":
            # Tool call
            tool_calls.append({
                "id": block.get("id"),
                "name": block.get("name"),
                "input": block.get("input"),
            })

    return {
        "reasoning": {
            "content": "\n\n".join(reasoning_parts) if reasoning_parts else None,
            "block_count": len(reasoning_parts),
        },
        "output": {
            "content": "\n\n".join(output_parts) if output_parts else None,
            "block_count": len(output_parts),
        },
        "tool_calls": tool_calls if tool_calls else None,
    }


def get_last_user_message(transcript_path: str) -> dict:
    """Read transcript and get the last user message (input)."""
    try:
        from pathlib import Path
        transcript = Path(transcript_path)
        if not transcript.exists():
            return {}

        with open(transcript) as f:
            lines = f.readlines()[-50:]  # Look back further for user message

        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("type") == "human" and "message" in entry:
                    msg = entry["message"]
                    content = msg.get("content", [])

                    # Extract text from content blocks
                    if isinstance(content, list):
                        text_parts = []
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                text_parts.append(block.get("text", ""))
                            elif isinstance(block, str):
                                text_parts.append(block)
                        return {
                            "content": "\n".join(text_parts) if text_parts else None,
                            "role": "user",
                        }
                    elif isinstance(content, str):
                        return {"content": content, "role": "user"}
            except json.JSONDecodeError:
                continue
        return {}
    except Exception:
        return {}


def get_last_assistant_message(transcript_path: str) -> dict:
    """Read transcript and get the last assistant message with usage.

    Now extracts:
    - model: The Claude model used
    - usage: Token counts (input, output, cache)
    - input: User's input message
    - reasoning: Extended thinking content
    - output: Text response content
    - tool_calls: Any tool calls made
    """
    try:
        from pathlib import Path
        transcript = Path(transcript_path)
        if not transcript.exists():
            return {}

        # Read last 50 lines to find messages
        with open(transcript) as f:
            lines = f.readlines()[-50:]

        assistant_msg = None
        for line in reversed(lines):
            try:
                entry = json.loads(line)
                if entry.get("type") == "assistant" and "message" in entry:
                    msg = entry["message"]
                    assistant_msg = msg
                    break
            except json.JSONDecodeError:
                continue

        if not assistant_msg:
            return {}

        # Extract content parts (reasoning, output, tool_calls)
        content = assistant_msg.get("content", [])
        content_parts = extract_content_parts(content) if isinstance(content, list) else {}

        # Get user input
        user_msg = get_last_user_message(transcript_path)

        # Get usage breakdown
        usage = assistant_msg.get("usage", {})

        return {
            "model": assistant_msg.get("model"),
            "usage": usage,
            "stop_reason": assistant_msg.get("stop_reason"),
            # Structured content
            "input": user_msg.get("content"),
            "reasoning": content_parts.get("reasoning", {}).get("content"),
            "output": content_parts.get("output", {}).get("content"),
            "tool_calls": content_parts.get("tool_calls"),
            # Legacy field for backward compatibility
            "content": content,
        }
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
    user_input = None
    reasoning = None
    ai_output = None
    ai_response = None  # Legacy field

    transcript_path = hook_data.get("transcript_path")
    if transcript_path and hook_type in ("post", "PostToolUse"):
        assistant_msg = get_last_assistant_message(transcript_path)
        if assistant_msg:
            model = assistant_msg.get("model")
            usage = assistant_msg.get("usage", {})
            cost = calculate_cost(model, usage) if model and usage else 0.0

            # New structured fields
            user_input = assistant_msg.get("input")
            reasoning = assistant_msg.get("reasoning")
            ai_output = assistant_msg.get("output")

            # Legacy ai_response for backward compatibility (truncated)
            if ai_output:
                ai_response = ai_output[:500] if len(ai_output) > 500 else ai_output

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
        # Model and usage
        "model": model,
        "usage": usage,
        "cost_usd": cost,
        # NEW: Structured input/reasoning/output
        "user_input": user_input,
        "reasoning": reasoning,
        "ai_output": ai_output,
        # Legacy field (truncated for backward compat)
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
        # Updated schema with input/reasoning/output columns
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
                user_input TEXT,
                reasoning TEXT,
                ai_output TEXT,
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
            ("user_input", "TEXT"),
            ("reasoning", "TEXT"),
            ("ai_output", "TEXT"),
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
                working_dir, model, input_tokens, output_tokens, cache_read_tokens, cost_usd,
                user_input, reasoning, ai_output, ai_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            trace.get("user_input"),
            trace.get("reasoning"),
            trace.get("ai_output"),
            trace.get("ai_response"),
        ))
        conn.commit()
        conn.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()

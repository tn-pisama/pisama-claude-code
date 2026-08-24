"""Registered-source transport and isolated config tests."""

import json
import os
import stat
from pathlib import Path

import pytest
from click.testing import CliRunner

import pisama_claude_code.cli as cli
from pisama_claude_code.cli import (
    main,
    normalize_trace,
    prepare_sync_payload,
    registered_source_identity,
    save_config,
)
from pisama_claude_code.paths import get_config_dir

REGISTERED_IDENTITY = {
    "source_instance_id": "claude-registration",
    "environment": "development",
    "subject_type": "claude_code_project",
    "subject_id": "pisama",
}


def test_config_dir_environment_override_and_default(monkeypatch, tmp_path):
    monkeypatch.setenv("PISAMA_CONFIG_DIR", str(tmp_path / "isolated"))
    assert get_config_dir() == tmp_path / "isolated"

    monkeypatch.delenv("PISAMA_CONFIG_DIR")
    assert get_config_dir() == Path.home() / ".claude" / "pisama"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission check")
def test_save_config_makes_directory_and_file_private(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    config_file = config_dir / "config.json"
    config_dir.mkdir(mode=0o755)
    config_file.write_text("{}")
    config_file.chmod(0o644)
    monkeypatch.setattr(cli, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cli, "CONFIG_FILE", config_file)

    save_config({"api_key": "local-key"})

    assert stat.S_IMODE(config_dir.stat().st_mode) == 0o700
    assert stat.S_IMODE(config_file.stat().st_mode) == 0o600
    assert json.loads(config_file.read_text()) == {"api_key": "local-key"}


def test_registered_source_identity_accepts_legacy_and_complete_identity():
    assert registered_source_identity({}) == {}
    assert registered_source_identity(REGISTERED_IDENTITY) == REGISTERED_IDENTITY


@pytest.mark.parametrize(
    "identity",
    [
        {"source_instance_id": "only-one-field"},
        {**REGISTERED_IDENTITY, "environment": "qa"},
        {**REGISTERED_IDENTITY, "subject_type": "Claude-Code"},
        {**REGISTERED_IDENTITY, "subject_type": 7},
        {**REGISTERED_IDENTITY, "source_instance_id": "legacy"},
        {**REGISTERED_IDENTITY, "subject_id": "  "},
    ],
)
def test_registered_source_identity_rejects_partial_or_invalid_values(identity):
    with pytest.raises(ValueError):
        registered_source_identity(identity)


def test_connect_persists_complete_registered_identity(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(cli, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cli, "CONFIG_FILE", config_dir / "config.json")

    result = CliRunner().invoke(
        main,
        [
            "connect",
            "--api-key",
            "local-key",
            "--api-url",
            "http://127.0.0.1:1",
            "--source-instance-id",
            REGISTERED_IDENTITY["source_instance_id"],
            "--environment",
            REGISTERED_IDENTITY["environment"],
            "--subject-type",
            REGISTERED_IDENTITY["subject_type"],
            "--subject-id",
            REGISTERED_IDENTITY["subject_id"],
        ],
    )

    assert result.exit_code == 0, result.output
    saved = json.loads((config_dir / "config.json").read_text())
    assert {field: saved[field] for field in REGISTERED_IDENTITY} == REGISTERED_IDENTITY


def test_connect_rejects_partial_identity_before_writing_config(monkeypatch, tmp_path):
    config_dir = tmp_path / "config"
    monkeypatch.setattr(cli, "CONFIG_DIR", config_dir)
    monkeypatch.setattr(cli, "CONFIG_FILE", config_dir / "config.json")

    result = CliRunner().invoke(
        main,
        [
            "connect",
            "--api-key",
            "local-key",
            "--source-instance-id",
            "only-one-field",
        ],
    )

    assert result.exit_code == 2
    assert "must be supplied together" in result.output
    assert not (config_dir / "config.json").exists()


def test_normalize_trace_promotes_nested_agent_identity_without_overwriting_top_level():
    nested = normalize_trace(
        {
            "session_id": "nested-session",
            "raw": {
                "agent_id": "agent-from-hook",
                "agent_type": "Explore",
                "is_sidechain": True,
            },
        }
    )
    top_level = normalize_trace(
        {
            "session_id": "top-level-session",
            "agent_id": "agent-from-row",
            "agent_type": "Plan",
            "is_sidechain": False,
            "raw": {
                "agent_id": "ignored-agent",
                "agent_type": "ignored-type",
                "is_sidechain": True,
            },
        }
    )

    assert nested["agent_id"] == "agent-from-hook"
    assert nested["agent_type"] == "Explore"
    assert nested["is_sidechain"] is True
    assert top_level["agent_id"] == "agent-from-row"
    assert top_level["agent_type"] == "Plan"
    assert top_level["is_sidechain"] is False


def test_sync_payload_carries_agent_and_registered_source_identity():
    trace = normalize_trace(
        {
            "session_id": "session-1",
            "timestamp": "2026-08-24T00:00:00Z",
            "raw": {
                "agent_id": "agent-1",
                "agent_type": "Explore",
                "is_sidechain": True,
            },
        }
    )

    payload = prepare_sync_payload([trace], False, REGISTERED_IDENTITY)

    assert {field: payload[field] for field in REGISTERED_IDENTITY} == REGISTERED_IDENTITY
    assert payload["traces"][0]["agent_id"] == "agent-1"
    assert payload["traces"][0]["agent_type"] == "Explore"
    assert payload["traces"][0]["is_sidechain"] is True


def test_legacy_sync_payload_omits_registered_source_identity():
    payload = prepare_sync_payload([], False)

    assert all(field not in payload for field in REGISTERED_IDENTITY)

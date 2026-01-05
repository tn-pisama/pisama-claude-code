# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.2] - 2025-01-04

### Added
- Token usage tracking with input, output, and cache read tokens
- Cost calculation per trace and session totals
- Model-aware pricing (Opus 4.5, Sonnet 4, Haiku 3.5)
- `pisama-cc usage` command with `--by-model` and `--by-tool` grouping
- Export to gzip format with `--compress` flag

### Changed
- Improved status output with token and cost summaries
- Better formatting for large numbers in CLI output

### Fixed
- Cache token counting for long sessions

## [0.3.1] - 2025-01-03

### Added
- Verbose trace output with `-v` flag
- Filter traces by tool type

### Fixed
- SQLite connection handling in async contexts

## [0.3.0] - 2025-01-02

### Added
- SQLite storage backend for local traces
- JSONL export format
- `pisama-cc export` command
- Automatic secret redaction (API keys, passwords, tokens)
- File path anonymization (home directory replacement)

### Changed
- Migrated from file-based to SQLite storage
- Improved hook installation reliability

## [0.2.0] - 2024-12-30

### Added
- Platform sync functionality (`pisama-cc sync`)
- `pisama-cc connect` for platform authentication
- `pisama-cc analyze` for remote failure detection

### Changed
- Restructured CLI with subcommands

## [0.1.0] - 2024-12-28

### Added
- Initial release
- Hook-based trace capture for Claude Code
- `pisama-cc install` and `pisama-cc uninstall` commands
- `pisama-cc status` command
- `pisama-cc traces` command for viewing recent traces
- Support for Bash, Read, Write, Edit, Grep, Glob tools
- Local storage in `~/.claude/pisama/traces/`

[Unreleased]: https://github.com/tn-pisama/pisama-claude-code/compare/v0.3.2...HEAD
[0.3.2]: https://github.com/tn-pisama/pisama-claude-code/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/tn-pisama/pisama-claude-code/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/tn-pisama/pisama-claude-code/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/tn-pisama/pisama-claude-code/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/tn-pisama/pisama-claude-code/releases/tag/v0.1.0

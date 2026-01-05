# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@pisama.dev**

Include the following information:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Affected versions**
4. **Potential impact** (what could an attacker do?)
5. **Any suggested fixes** (optional)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Assessment**: We will assess the vulnerability and determine severity within 7 days
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to release a fix within 30 days for critical issues

### Severity Levels

| Level | Description | Target Resolution |
|-------|-------------|-------------------|
| Critical | Remote code execution, credential exposure | 7 days |
| High | Privilege escalation, data exposure | 14 days |
| Medium | Limited data exposure, DoS | 30 days |
| Low | Minor issues | Next release |

## Security Considerations

### Data Handling

pisama-claude-code captures traces from Claude Code sessions. By default:

- **Traces are stored locally** in `~/.claude/pisama/traces/`
- **Secrets are automatically redacted** (API keys, passwords, tokens)
- **File paths are anonymized** (home directory replaced with `~`)
- **Platform sync is opt-in** - traces are never uploaded without explicit action

### Sensitive Data

The following patterns are automatically redacted:
- API keys (various formats)
- Passwords and tokens
- AWS credentials
- Private keys
- Database connection strings

If you find that sensitive data is not being properly redacted, please report it as a security issue.

### Hook Security

The capture hooks run with your user permissions. They:
- Only read data that Claude Code provides
- Do not execute arbitrary commands
- Do not modify your files or system

### Platform Communication

When syncing to the PISAMA platform:
- All communication uses HTTPS
- Authentication uses secure tokens
- Data is encrypted in transit

## Best Practices

1. **Keep updated**: Always use the latest version
2. **Review traces**: Periodically check what's being captured
3. **Limit sync**: Only sync to the platform when needed
4. **Secure storage**: Protect `~/.claude/pisama/` directory permissions

## Acknowledgments

We appreciate responsible disclosure and will acknowledge security researchers who report valid vulnerabilities (with their permission).

## Contact

- Security issues: security@pisama.dev
- General questions: team@pisama.dev

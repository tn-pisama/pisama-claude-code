#!/bin/bash
# Simulated demo for GIF recording
# Shows realistic output without needing real traces
#
# Record with: asciinema rec demo.cast
# Convert with: agg demo.cast demo.gif --theme monokai --cols 80 --rows 24

set -e

# Typing effect
type_cmd() {
    local cmd="$1"
    printf '\033[0;32m$\033[0m '
    for ((i=0; i<${#cmd}; i++)); do
        printf '%s' "${cmd:$i:1}"
        sleep 0.04
    done
    printf '\n'
    sleep 0.2
}

pause() { sleep "${1:-1}"; }

clear
printf '\033[1;36m'
cat << 'EOF'
╔═══════════════════════════════════════════════════╗
║   pisama-claude-code                              ║
║   Track token costs for Claude Code sessions      ║
╚═══════════════════════════════════════════════════╝
EOF
printf '\033[0m\n'
pause 2

# Install
printf '\033[1;33m# Install\033[0m\n'
type_cmd "pip install pisama-claude-code"
cat << 'EOF'
Successfully installed pisama-claude-code-0.3.2
EOF
pause 1.5

printf '\n\033[1;33m# Set up hooks\033[0m\n'
type_cmd "pisama-cc install"
cat << 'EOF'
✅ Installed pisama-capture.py
✅ Installed pisama-pre.sh
✅ Installed pisama-post.sh
✅ Updated ~/.claude/settings.local.json

Hooks installed! Traces will be captured automatically.
EOF
pause 2

printf '\n\033[1;33m# After a coding session, check status\033[0m\n'
type_cmd "pisama-cc status"
cat << 'EOF'
📊 PISAMA Status
========================================

🔧 Hook Installation:
   ✅ pisama-capture.py
   ✅ pisama-pre.sh
   ✅ pisama-post.sh
   All hooks installed

🔗 Platform Connection:
   ❌ Not connected (local-only mode)

📁 Local Traces: 1,847
   Input tokens:  142,580
   Output tokens: 891,234
   Total cost:    $52.34
   Models: claude-opus-4-5-20251101

📝 Claude Code Settings:
   ✅ PISAMA hooks configured in settings
EOF
pause 2.5

printf '\n\033[1;33m# View recent tool calls\033[0m\n'
type_cmd "pisama-cc traces -v --last 5"
cat << 'EOF'
📋 Recent Traces (5 shown)
======================================================================
2025-01-04T14:23:45 | Bash         | a3f8c2d1 | post |   2341i  8923o | $0.7012
2025-01-04T14:23:38 | Read         | a3f8c2d1 | post |   1823i  2341o | $0.1892
2025-01-04T14:23:31 | Edit         | a3f8c2d1 | post |   3421i 12893o | $1.0234
2025-01-04T14:23:22 | Grep         | a3f8c2d1 | post |    892i  1234o | $0.1023
2025-01-04T14:23:15 | Glob         | a3f8c2d1 | post |    423i   891o | $0.0712
──────────────────────────────────────────────────────────────────────
Totals: 8,900 input + 26,282 output tokens = $2.0873
EOF
pause 2.5

printf '\n\033[1;33m# Detailed breakdown\033[0m\n'
type_cmd "pisama-cc usage --by-model --by-tool"
cat << 'EOF'
📊 Token Usage Summary (last 100 traces)
==================================================
Input tokens:           142,580
Output tokens:          891,234
Cache read tokens:    1,234,567
Total tokens:         1,033,814
Total cost:        $       52.34

📈 By Model:
--------------------------------------------------
  claude-opus-4-5-20251101              $52.34

🔧 By Tool:
--------------------------------------------------
  Bash                   145 calls  $23.45
  Read                    89 calls  $12.34
  Edit                    67 calls   $8.92
  Write                   34 calls   $4.21
  Grep                    23 calls   $2.12
  Glob                    12 calls   $1.30
EOF
pause 2

printf '\n\033[1;36m'
cat << 'EOF'
════════════════════════════════════════════════════
  ✓ Track every token. Know your costs.

  pip install pisama-claude-code
════════════════════════════════════════════════════
EOF
printf '\033[0m'
pause 3

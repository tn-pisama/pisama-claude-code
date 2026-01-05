#!/bin/bash
# Demo recording script for pisama-claude-code
#
# Recording options:
#   1. asciinema (recommended): asciinema rec demo.cast
#   2. terminalizer: terminalizer record demo
#   3. ttygif: script + ttyrec + ttygif
#
# Then convert to GIF:
#   asciinema: agg demo.cast demo.gif --theme monokai
#   terminalizer: terminalizer render demo -o demo.gif

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Typing effect - simulates human typing
type_cmd() {
    local cmd="$1"
    echo -ne "${GREEN}\$${NC} "
    for ((i=0; i<${#cmd}; i++)); do
        echo -n "${cmd:$i:1}"
        sleep 0.05
    done
    echo ""
    sleep 0.3
}

# Run command with typing effect
run_cmd() {
    type_cmd "$1"
    eval "$1"
    sleep 1.5
}

# Clear and set title
clear
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  pisama-claude-code - Track Claude Code costs${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
sleep 2

# Step 1: Install
echo -e "${YELLOW}# Install the package${NC}"
sleep 1
run_cmd "pip install pisama-claude-code"
echo ""

# Step 2: Install hooks
echo -e "${YELLOW}# Set up capture hooks${NC}"
sleep 1
run_cmd "pisama-cc install"
echo ""

# Step 3: Show status (after some usage)
echo -e "${YELLOW}# Check status and costs${NC}"
sleep 1
run_cmd "pisama-cc status"
echo ""

# Step 4: View traces
echo -e "${YELLOW}# View recent tool calls${NC}"
sleep 1
run_cmd "pisama-cc traces -v --last 10"
echo ""

# Step 5: Usage breakdown
echo -e "${YELLOW}# Detailed cost breakdown${NC}"
sleep 1
run_cmd "pisama-cc usage --by-model --by-tool"
echo ""

# End
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓${NC} Track every token. Know your costs."
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
sleep 3

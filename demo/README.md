# Demo Recording

Scripts to create a GIF demo for the README.

## Quick Start (Recommended)

```bash
# Install asciinema and agg (ASCII to GIF)
brew install asciinema
cargo install --git https://github.com/asciinema/agg

# Record the simulated demo
cd demo
chmod +x demo-simulated.sh
asciinema rec demo.cast -c ./demo-simulated.sh

# Convert to GIF
agg demo.cast ../assets/demo.gif \
    --theme monokai \
    --cols 70 \
    --rows 28 \
    --speed 1.2

# Or use gif-for-cli for smaller file size
# pip install gif-for-cli
```

## Files

| File | Purpose |
|------|---------|
| `demo-simulated.sh` | Pre-scripted demo with realistic output (use this) |
| `record-demo.sh` | Live demo using actual `pisama-cc` commands |

## Recording Tips

1. **Use simulated demo** - Consistent, reproducible output
2. **Terminal size** - Set to 70x28 before recording
3. **Clean terminal** - No distracting prompts or colors
4. **Speed** - 1.2x makes it watchable without being too fast

## Alternative: Terminalizer

```bash
npm install -g terminalizer

# Record
terminalizer record demo --config terminalizer.yml

# Render
terminalizer render demo -o demo.gif
```

## Alternative: VHS (by Charm)

```bash
brew install vhs

# Create a .tape file and run
vhs demo.tape
```

## Adding to README

Once you have `demo.gif`, add to README.md:

```markdown
## Demo

![pisama-claude-code demo](assets/demo.gif)
```

## Optimal GIF Settings

- **Width**: 600-800px (readable on GitHub)
- **FPS**: 10-15 (smaller file size)
- **Duration**: 15-25 seconds (attention span)
- **File size**: Under 5MB (GitHub displays inline)

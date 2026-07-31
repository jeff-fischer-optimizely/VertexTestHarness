#!/bin/bash
# Quick Start: Run diagnostics for both backends

set -e

echo "========================================================================"
echo "  Session Persistence Diagnostics - Quick Start"
echo "========================================================================"
echo ""

# Check for Python
if ! command -v python &> /dev/null; then
    echo "Error: Python not found"
    exit 1
fi

# Check for claude-agent-sdk
if ! python -c "import claude_agent_sdk" 2>/dev/null; then
    echo "⚠️  Claude Agent SDK not installed"
    echo "Installing..."
    pip install claude-agent-sdk
fi

# Create output directory
mkdir -p diagnostic_output

echo ""
echo "Running diagnostics..."
echo ""

# Option 1: Automated (placeholder results)
echo "--- Option 1: Automated Runner ---"
echo "This generates a framework with placeholder results."
echo "Press Enter to run, or Ctrl+C to skip..."
read

python run_diagnostics.py --backend both

echo ""
echo "--- Option 2: Interactive Test ---"
echo "For real testing, run the interactive suite:"
echo ""
echo "  python interactive_test.py"
echo ""
echo "This will guide you through each test with your actual"
echo "Claude Agent SDK session."
echo ""

echo "✓ Quick start complete"
echo ""
echo "Next steps:"
echo "  1. Review: diagnostic_output/diagnostic_results_*.json"
echo "  2. Read: README.md for detailed usage"
echo "  3. Run: python interactive_test.py for real testing"
echo ""

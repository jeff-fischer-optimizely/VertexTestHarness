# Session Persistence Diagnostics - START HERE

## Quick Start (3 Steps)

### 1. See What Will Be Tested (30 seconds, FREE)
```bash
python run_real_tests.py --dry-run
```

### 2. Set Your API Key
```bash
export ANTHROPIC_API_KEY=your-key-here
```
Get a key at: https://console.anthropic.com/

### 3. Run Real Tests (2 minutes, ~$0.10)
```bash
python run_real_tests.py
```

That's it! Results saved to `diagnostic_output/diagnostic_results_*.json`

---

## What This Does

Tests **5 diagnostic scenarios** to identify where session persistence breaks between Anthropic and Vertex backends:

1. ✓ Session Persistence - Does response reach history?
2. ✓ Stream vs History - Do they match?
3. ✓ JSONL Transcript - Is structure valid?
4. ✓ Session Continuity - Does session stay consistent?
5. ✓ **Backend Matrix** - Where does Vertex differ from Anthropic?

**Test 5 is the critical one** - it identifies the EXACT failure point.

---

## Example Output

```
--- Test 5: Backend Matrix Comparison ---
Anthropic remembers: True
Vertex remembers:    False

WARNING: DIFFERENCE DETECTED:
  Anthropic first failure: None
  Vertex first failure:    in_history  ← THE SMOKING GUN
```

This tells you: **Vertex responses aren't being persisted to history.**

---

## Read More

- **[FINAL_SUMMARY.md](FINAL_SUMMARY.md)** - Complete overview of what was built
- **[HOWTO_RUN_TESTS.md](HOWTO_RUN_TESTS.md)** - Detailed instructions
- **[README.md](README.md)** - Full documentation (492 lines)
- **[DIAGNOSTICS_SUMMARY.md](DIAGNOSTICS_SUMMARY.md)** - Executive summary

---

## Three Ways to Run

| Method | API Key? | Cost | Time | Use Case |
|--------|----------|------|------|----------|
| `--dry-run` | No | $0 | 10s | See what will be tested |
| Real tests | Yes | ~$0.10 | 2min | Get actual diagnostic data |
| Interactive | Yes | ~$0.10 | 5min | Manual step-by-step |

---

## Files Created

```
Core Scripts (3):
  session_diagnostics.py   - Diagnostic framework
  sdk_integration.py       - Real API integration
  run_real_tests.py        - Safe runner

Documentation (6):
  START_HERE.md            - This file
  FINAL_SUMMARY.md         - Complete overview
  HOWTO_RUN_TESTS.md       - Instructions
  README.md                - Full docs
  DIAGNOSTICS_SUMMARY.md   - Executive summary
  USAGE_EXAMPLES.md        - Code examples

Setup:
  requirements.txt         - Dependencies
  quick_start.sh           - One-command setup
```

---

## Current Status

✅ Framework installed
✅ anthropic package installed (v0.120.2)
✅ Example test completed
❌ ANTHROPIC_API_KEY not set (needed for real tests)

---

## Cost Breakdown

- Dry run: **$0** (no API calls)
- Test Anthropic: **~$0.05**
- Test Vertex: **~$0.05**
- **Total: ~$0.10** for complete diagnostic suite

This is **extremely cheap** for identifying a production bug.

---

## What You'll Learn

After running tests, you'll know **exactly** where the pipeline breaks:

```
Pipeline Stages:
  1. Claude generates      ← Check: streamed = true
  2. SDK receives          ← Check: streamed = true
  3. Stream emits          ← Check: streamed = true
  4. History persists      ← Check: in_history = true/false
  5. Active branch         ← Check: correct_parent_chain = true/false
  6. Session continues     ← Check: same_session = true/false
  7. Remembers value       ← Check: remembers = true/false
```

The JSON output shows which check fails first.

---

## Ready to Run?

```bash
# See what will happen (free)
python run_real_tests.py --dry-run

# Run real tests (requires API key)
export ANTHROPIC_API_KEY=your-key
python run_real_tests.py
```

**Everything is ready. Just add your API key.**

# Session Persistence Diagnostics

Comprehensive test suite for diagnosing Claude Agent SDK session persistence issues between Anthropic and Vertex AI backends.

Based on the diagnostic framework from this [ChatGPT conversation](https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2).

## Overview

This test harness identifies **where** in the message pipeline session persistence breaks:

```
Claude generates response
        ↓
SDK receives response
        ↓
receive_response() emits response
        ↓
Transcript persists response
        ↓
Response belongs to active branch
        ↓
Next turn resumes same branch
        ↓
Response included in effective context
        ↓
Claude reasons using previous response
```

## The Five Core Tests

### Test 1: Persisted Session History
**What it tests:** Whether Claude's assistant response actually made it into the session history.

**How to verify:**
```python
from claude_agent_sdk import get_session_messages

messages = get_session_messages(session_id="your-session-id")
# Check if expected assistant message is present
```

**Requires:** Claude Agent SDK 0.1.46+ (session history APIs)

---

### Test 2: Stream vs History Comparison
**What it tests:** Whether messages emitted by `receive_response()` match what gets persisted to session history.

**How to verify:**
```python
# Capture streamed messages
received = []
async for message in client.receive_response():
    received.append(message)

# Capture history
history = get_session_messages(session_id)

# Compare counts and content
```

**Known issue:** [SDK Issue #294](https://github.com/anthropics/claude-agent-sdk-python/issues/294) - messages present in JSONL but not emitted by `receive_response()`

---

### Test 3: JSONL Transcript Inspection
**What it tests:** Raw transcript structure, parent relationships, and conversation branching.

**How to verify:**
- Parse JSONL transcript file
- Check `uuid` and `parentUuid` relationships
- Verify expected content is on the **active conversation branch**, not orphaned

**Why it matters:** A response can exist in the transcript but not belong to the lineage being resumed.

---

### Test 4: Session ID Continuity
**What it tests:** Whether the session ID remains constant across turns.

**How to verify:**
- Log session ID on every turn
- Log CWD and configuration
- Verify no unexpected session switches

**Known issue:** Session continuation can fail when resumed from a different root directory.

---

### Test 5: Backend Matrix (Comprehensive)
**What it tests:** Full pipeline comparison between Anthropic and Vertex.

**Verification checklist:**

| Stage                       | Anthropic | Vertex |
| --------------------------- | :-------: | :----: |
| Response streamed           |     ✓     |   ?    |
| Response in session history |     ✓     |   ?    |
| Correct parent relationship |     ✓     |   ?    |
| Same session continues      |     ✓     |   ?    |
| Next turn remembers value   |     ✓     |   ?    |

**Test prompts:**
1. `Say exactly: "PINEAPPLE-7821 is the magic value."`
2. `What magic value did you just tell me?`

The matrix identifies the **first arrow that breaks** in the pipeline.

---

## Installation

### Prerequisites
```bash
pip install claude-agent-sdk
```

For session history APIs (Tests 1-2), requires SDK version `0.1.46+`.

### Setup
```bash
cd c:\src\EpiServer\VertextTestHarness

# Anthropic backend (default)
unset CLAUDE_CODE_USE_VERTEX
unset ANTHROPIC_VERTEX_PROJECT_ID
unset CLOUD_ML_REGION

# Vertex AI backend
export CLAUDE_CODE_USE_VERTEX=true
export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
export CLOUD_ML_REGION=your-region
```

---

## Usage

### Option 1: Automated Runner (Placeholder)
```bash
python run_diagnostics.py --backend anthropic
python run_diagnostics.py --backend vertex
python run_diagnostics.py --backend both
```

**Note:** This provides a framework and generates placeholder results. You'll need to integrate with your actual Claude Agent SDK client.

### Option 2: Interactive Test
```bash
python interactive_test.py
```

Prompts you through each test step and captures manual verification results.

### Option 3: Programmatic Integration
```python
from session_diagnostics import SessionDiagnostics
from pathlib import Path

diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))

# Test 1: Session persistence
result = await diagnostics.test_session_persistence(
    backend="anthropic",
    session_id="your-session-id",
    expected_assistant_content="PINEAPPLE-7821"
)
diagnostics.record_result(result)

# ... run other tests

diagnostics.print_summary()
diagnostics.save_results()
```

---

## File Structure

```
.
├── session_diagnostics.py   # Core diagnostic framework
├── run_diagnostics.py        # Automated test runner
├── interactive_test.py       # Interactive guided tests
├── README.md                 # This file
└── diagnostic_output/        # Test results (created on first run)
    └── diagnostic_results_YYYYMMDD_HHMMSS.json
```

---

## Output

### Console Summary
```
================================================================================
SESSION PERSISTENCE DIAGNOSTIC SUMMARY
================================================================================

Total Tests: 10

--- Anthropic Backend ---
  Passed: 5/5
  Failed: 0/5

--- Vertex Backend ---
  Passed: 2/5
  Failed: 3/5

--- Test Breakdown ---

1_session_persistence:
  Anthropic: 1 pass, 0 fail
  Vertex:    0 pass, 1 fail

2_stream_vs_history:
  Anthropic: 1 pass, 0 fail
  Vertex:    0 pass, 1 fail
...
```

### JSON Output
```json
{
  "summary": {
    "total_tests": 10,
    "anthropic": {"total": 5, "passed": 5, "failed": 0},
    "vertex": {"total": 5, "passed": 2, "failed": 3}
  },
  "results": [
    {
      "test_name": "1_session_persistence",
      "backend": "vertex",
      "passed": false,
      "details": {
        "found_in_history": false,
        "expected_content": "PINEAPPLE-7821"
      },
      "timestamp": "2026-07-31T10:30:45.123456",
      "session_id": "abc123"
    }
  ]
}
```

---

## Interpreting Results

### If Test 1 fails (Session Persistence)
**Diagnosis:** Response never made it to session history.
**Action:** Check SDK message persistence logic before turn N+1.

### If Test 2 fails (Stream vs History)
**Diagnosis:** Streaming and persistence pipelines diverged.
**Action:** Check for SDK bugs similar to [Issue #294](https://github.com/anthropics/claude-agent-sdk-python/issues/294).

### If Test 3 fails (JSONL Transcript)
**Diagnosis:** Response exists but is on wrong conversation branch.
**Action:** Inspect `parentUuid` relationships in transcript JSONL.

### If Test 4 fails (Session Continuity)
**Diagnosis:** Session ID changed unexpectedly between turns.
**Action:** Check if CWD changed, or if resume/continue logic failed.

### If Test 5 fails for Vertex but passes for Anthropic
**Diagnosis:** Vertex-specific configuration alters one of the above stages.
**Action:** Use the matrix to identify **first failure point**, then instrument that stage.

---

## Key Insights from the Framework

1. **These aren't just theoretical possibilities** — Anthropic's SDK issue history shows real cases where streamed vs persisted messages diverged.

2. **The JSONL transcript is diagnostic gold** — even before official history APIs existed, Anthropic collaborators suggested parsing those files.

3. **Don't start from "Vertex drops assistant messages"** — start from:
   > Does the Vertex configuration alter which of these observable stages fails?

4. **Instrument the pipeline before running benchmark suites** — this can turn a fuzzy model-quality issue into a precise SDK regression with a reproducible test case.

---

## Known SDK Issues

- **Multi-line buffering fixes** ([CHANGELOG](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md))
- **Sidechain messages not yielded** ([Issue #294](https://github.com/anthropics/claude-agent-sdk-python/issues/294))
- **Session history API support** ([Issue #109](https://github.com/anthropics/claude-agent-sdk-python/issues/109))
- **Session continuation from different directories** ([Issue #109](https://github.com/anthropics/claude-agent-sdk-python/issues/109))

---

## Next Steps

1. **Run the interactive test** for both backends
2. **Integrate with your Claude Agent SDK client** to populate real data
3. **Instrument the pipeline stages** that fail
4. **Capture JSONL transcripts** for manual inspection
5. **File SDK issues** with reproducible test cases

---

## Contributing

This is a diagnostic framework. To add new tests:

1. Add a test method to `SessionDiagnostics` class
2. Add corresponding runner in `DiagnosticRunner`
3. Add interactive prompt in `InteractiveDiagnostic`
4. Update this README

---

## References

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Session History APIs (Issue #109)](https://github.com/anthropics/claude-agent-sdk-python/issues/109)
- [Stream/History Divergence (Issue #294)](https://github.com/anthropics/claude-agent-sdk-python/issues/294)
- [SDK Changelog](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)
- [Original ChatGPT Diagnostic Framework](https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2)

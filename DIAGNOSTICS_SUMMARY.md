# Session Persistence Diagnostics - Executive Summary

## Problem Statement

Claude Agent SDK sessions may fail to persist assistant responses between turns, causing the model to "forget" what it just said. This manifests as retained reasoning failure where:

- **Turn N:** Claude says "The magic value is PINEAPPLE-7821"
- **Turn N+1:** Claude doesn't remember saying that value

The question: **Where in the message pipeline does persistence break?**

---

## The Diagnostic Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Claude generates response                                 │
│         ↓                                                    │
│ 2. SDK receives response                                    │
│         ↓                                                    │
│ 3. receive_response() emits response                        │
│         ↓                                                    │
│ 4. Transcript persists response                             │
│         ↓                                                    │
│ 5. Response belongs to active branch                        │
│         ↓                                                    │
│ 6. Next turn resumes same branch                            │
│         ↓                                                    │
│ 7. Response included in effective context                   │
│         ↓                                                    │
│ 8. Claude reasons using previous response                   │
└─────────────────────────────────────────────────────────────┘
```

**Goal:** Find the first arrow that breaks.

---

## The Five Tests

### 1️⃣ Session Persistence
**Question:** Did the assistant response make it into session history?

**Method:**
```python
messages = get_session_messages(session_id)
# Verify expected assistant message is present
```

**Failure mode:** Response never persisted → breaks at stage 4

---

### 2️⃣ Stream vs History
**Question:** Do streamed messages match persisted messages?

**Method:**
```python
# Capture both pipelines
streamed = [msg async for msg in client.receive_response()]
history = get_session_messages(session_id)
# Compare counts and content
```

**Failure mode:** Stream/persist pipelines diverged → breaks at stage 3-4

**Known SDK bug:** [Issue #294](https://github.com/anthropics/claude-agent-sdk-python/issues/294)

---

### 3️⃣ JSONL Transcript
**Question:** Is the response on the active conversation branch?

**Method:**
- Parse JSONL transcript
- Check `uuid` and `parentUuid` relationships
- Verify content is on main lineage, not orphaned

**Failure mode:** Response exists but on wrong branch → breaks at stage 5

---

### 4️⃣ Session Continuity
**Question:** Does the session ID remain constant?

**Method:**
```python
# Track across turns
turn_1_session = "abc123"
turn_2_session = "abc123"  # ✓ same
turn_3_session = "xyz789"  # ✗ different - why?
```

**Failure mode:** Session switched unexpectedly → breaks at stage 6

**Known issue:** Continuation fails from different CWD

---

### 5️⃣ Backend Matrix
**Question:** Where does Vertex differ from Anthropic?

**Method:** Test full pipeline for both backends

| Stage                       | Anthropic | Vertex | First Failure |
| --------------------------- | :-------: | :----: | :-----------: |
| Response streamed           |     ✓     |   ?    |               |
| Response in session history |     ✓     |   ?    |      ←        |
| Correct parent relationship |     ✓     |   ?    |               |
| Same session continues      |     ✓     |   ?    |               |
| Next turn remembers value   |     ✓     |   ✗    |               |

**Example failure signature:**
```
stream          ✓
history         ✗  ← First failure
parent chain    N/A
remember        ✗
```

**Diagnosis:** Response never made it to session history (stage 4)

---

## Test Prompts

### Establish Test Value
```
USER: Say exactly: "PINEAPPLE-7821 is the magic value."
```

Expected response:
```
ASSISTANT: PINEAPPLE-7821 is the magic value.
```

### Recall Test Value
```
USER: What magic value did you just tell me?
```

Expected response:
```
ASSISTANT: PINEAPPLE-7821
```

**If Claude doesn't remember:** Session persistence broke somewhere.

---

## How to Run

### Quick Start
```bash
chmod +x quick_start.sh
./quick_start.sh
```

### Interactive (Recommended)
```bash
python interactive_test.py
```

Guides you through manual testing with your actual SDK session.

### Programmatic
```bash
python run_diagnostics.py --backend anthropic
python run_diagnostics.py --backend vertex
python run_diagnostics.py --backend both
```

Generates framework (integrate with your SDK client for real data).

---

## Expected Output

### Console
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
  Vertex:    0 pass, 1 fail  ← FIRST FAILURE

5_backend_matrix:
  Anthropic: 1 pass, 0 fail
  Vertex:    0 pass, 1 fail
```

### JSON
```json
{
  "results": [
    {
      "test_name": "1_session_persistence",
      "backend": "vertex",
      "passed": false,
      "details": {
        "found_in_history": false,
        "expected_content": "PINEAPPLE-7821",
        "total_messages": 12,
        "assistant_messages": 5
      }
    }
  ]
}
```

---

## Interpreting Results

### ✓ All tests pass
**Diagnosis:** Pipeline is healthy.
**Action:** Look elsewhere for retained reasoning issues.

### ✗ Test 1 fails
**Diagnosis:** Response never made it to session history.
**Action:** Instrument SDK persistence logic around `session.add_message()`.

### ✗ Test 2 fails
**Diagnosis:** Stream/persist divergence.
**Action:** Check for SDK bugs similar to Issue #294.

### ✗ Test 3 fails
**Diagnosis:** Response on wrong conversation branch.
**Action:** Inspect JSONL `parentUuid` chain.

### ✗ Test 4 fails
**Diagnosis:** Session ID switched.
**Action:** Check CWD changes, session resume logic.

### ✗ Test 5 fails for Vertex only
**Diagnosis:** Vertex-specific configuration alters pipeline.
**Action:** Use matrix to identify **first failure stage**, then instrument that stage.

---

## Why This Matters

From the [original ChatGPT conversation](https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2):

> "The important thing is that these aren't just theoretical possibilities. Anthropic's own SDK issue history shows real cases where **what gets streamed and what gets persisted diverged**."

This diagnostic suite:

1. **Identifies the exact failure stage** (not just "it doesn't work")
2. **Compares backends** (Anthropic vs Vertex)
3. **Produces reproducible test cases** for SDK bug reports
4. **Turns fuzzy model-quality issues into precise SDK regressions**

---

## Key Files

| File                      | Purpose                                   |
| ------------------------- | ----------------------------------------- |
| `session_diagnostics.py`  | Core diagnostic framework (5 test types)  |
| `run_diagnostics.py`      | Automated runner (generates placeholders) |
| `interactive_test.py`     | Interactive guided testing                |
| `README.md`               | Detailed usage documentation              |
| `DIAGNOSTICS_SUMMARY.md`  | This file (executive overview)            |
| `quick_start.sh`          | One-command setup and run                 |
| `requirements.txt`        | Python dependencies                       |

---

## Next Steps

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run interactive test:**
   ```bash
   python interactive_test.py
   ```

3. **Capture JSONL transcripts** for inspection

4. **Compare Anthropic vs Vertex** using Test 5 matrix

5. **File SDK issues** with reproducible data

---

## Success Criteria

You've successfully diagnosed the issue when you can answer:

> **"At which stage does the Vertex pipeline first differ from Anthropic?"**

Not:
- ❌ "Vertex doesn't remember things"
- ❌ "The model forgets previous responses"

But:
- ✅ "Vertex fails at stage 4: response not persisted to session history"
- ✅ "Vertex succeeds through stage 5 but fails at stage 6: session ID switches"

**Precision matters** for effective debugging and SDK bug reports.

---

## References

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Session History APIs (SDK 0.1.46+)](https://github.com/anthropics/claude-agent-sdk-python/issues/109)
- [Stream/History Divergence Bug](https://github.com/anthropics/claude-agent-sdk-python/issues/294)
- [SDK Changelog](https://github.com/anthropics/claude-agent-sdk-python/blob/main/CHANGELOG.md)
- [Original Diagnostic Framework](https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2)

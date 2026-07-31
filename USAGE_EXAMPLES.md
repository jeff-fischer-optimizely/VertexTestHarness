# Usage Examples

## Quick Validation (No SDK Required)

### 1. Run Framework Test
```bash
python session_diagnostics.py
```

**Output:**
```
WARNING: Session history APIs not available (requires SDK 0.1.46+)
[10:32:06] INFO  | Detected backend: ANTHROPIC
[10:32:06] INFO  | Diagnostic framework initialized

================================================================================
SESSION PERSISTENCE DIAGNOSTIC SUMMARY
================================================================================

Total Tests: 1

--- Anthropic Backend ---
  Passed: 1/1
  Failed: 0/1
```

**Result:** Creates `diagnostic_output/diagnostic_results_*.json`

---

## Manual Testing Workflow

### Step 1: Set Up Backend

**For Anthropic:**
```bash
unset CLAUDE_CODE_USE_VERTEX
unset ANTHROPIC_VERTEX_PROJECT_ID
unset CLOUD_ML_REGION
```

**For Vertex:**
```bash
export CLAUDE_CODE_USE_VERTEX=true
export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
export CLOUD_ML_REGION=us-central1
```

### Step 2: Run Interactive Test
```bash
python interactive_test.py
```

**Follow the prompts:**
```
================================================================================
  INTERACTIVE SESSION DIAGNOSTICS
================================================================================

Which backend? (anthropic/vertex): anthropic

================================================================================
  Interactive Diagnostics: ANTHROPIC
================================================================================

This interactive suite will guide you through 5 diagnostic tests.
You'll need to manually interact with Claude Agent SDK and provide data.

Press Enter to continue...
```

### Step 3: Manual SDK Testing

**Test 1: Session Persistence**

1. Open your Claude Agent SDK client
2. Send prompt: `Say exactly: "The magic value is PINEAPPLE-7821."`
3. Note the session ID
4. Check session history:

```python
from claude_agent_sdk import get_session_messages

messages = get_session_messages(session_id="your-session-id")
for msg in messages:
    if msg.get("role") == "assistant":
        print(msg.get("content"))
```

5. Verify you see: `"The magic value is PINEAPPLE-7821."`

**Test 2: Recall Value**

6. Send prompt: `What magic value did you just tell me?`
7. Verify Claude responds: `PINEAPPLE-7821`

If Claude doesn't remember → session persistence broken.

---

## Programmatic Integration

### Example: Integrate with Your SDK Client

```python
import asyncio
from pathlib import Path
from session_diagnostics import SessionDiagnostics
from your_sdk_wrapper import YourClaudeClient  # Your SDK wrapper

async def run_diagnostics():
    diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))
    client = YourClaudeClient()
    
    # Test 1: Send prompt and capture session
    session_id = await client.send_message('Say exactly: "PINEAPPLE-7821"')
    
    # Test persistence
    result_1 = await diagnostics.test_session_persistence(
        backend="anthropic",
        session_id=session_id,
        expected_assistant_content="PINEAPPLE-7821"
    )
    diagnostics.record_result(result_1)
    
    # Test 2: Capture streamed messages
    streamed = []
    async for msg in client.receive_response():
        streamed.append(msg)
    
    result_2 = await diagnostics.test_stream_vs_history(
        backend="anthropic",
        session_id=session_id,
        streamed_messages=streamed
    )
    diagnostics.record_result(result_2)
    
    # Generate summary
    diagnostics.print_summary()
    diagnostics.save_results()

asyncio.run(run_diagnostics())
```

---

## Comparing Backends

### Run for Both Backends

```bash
# Test Anthropic
unset CLAUDE_CODE_USE_VERTEX
python interactive_test.py  # Answer prompts for "anthropic"

# Test Vertex
export CLAUDE_CODE_USE_VERTEX=true
python interactive_test.py  # Answer prompts for "vertex"
```

### Compare Results

```bash
ls diagnostic_output/
# diagnostic_results_20260731_103000.json  (anthropic)
# diagnostic_results_20260731_104500.json  (vertex)
```

**Review JSON:**
```python
import json

# Load both results
with open("diagnostic_output/diagnostic_results_20260731_103000.json") as f:
    anthropic_results = json.load(f)

with open("diagnostic_output/diagnostic_results_20260731_104500.json") as f:
    vertex_results = json.load(f)

# Compare summaries
print("Anthropic:", anthropic_results["summary"])
print("Vertex:", vertex_results["summary"])

# Find first failure
for result in vertex_results["results"]:
    if not result["passed"]:
        print(f"First failure: {result['test_name']}")
        print(f"Details: {result['details']}")
        break
```

---

## JSONL Transcript Analysis

### Locate Your Session Transcript

Session transcripts are typically stored in:
```
~/.claude/sessions/<session-id>.jsonl
```

Or within your project directory depending on SDK configuration.

### Manual Inspection

```python
import json
from pathlib import Path

transcript_path = Path("~/.claude/sessions/abc123.jsonl").expanduser()

with open(transcript_path) as f:
    entries = [json.loads(line) for line in f if line.strip()]

# Find test value
for entry in entries:
    message = entry.get("message", {})
    content = message.get("content", [])
    
    for c in content:
        if c.get("type") == "text" and "PINEAPPLE-7821" in c.get("text", ""):
            print(f"Found in entry: {entry.get('uuid')}")
            print(f"Parent: {entry.get('parentUuid')}")
            print(f"Role: {message.get('role')}")
```

### Programmatic Test

```python
from session_diagnostics import SessionDiagnostics

diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))

result = await diagnostics.test_jsonl_transcript(
    backend="anthropic",
    session_id="abc123",
    transcript_path=Path("~/.claude/sessions/abc123.jsonl"),
    expected_content="PINEAPPLE-7821"
)

print(f"Found: {result.details['found_content']}")
print(f"Parent chain length: {result.details['parent_chain_length']}")
```

---

## Interpreting Results

### Example 1: Everything Passes (Anthropic)

```json
{
  "test_name": "5_backend_matrix",
  "backend": "anthropic",
  "passed": true,
  "details": {
    "streamed": true,
    "in_history": true,
    "correct_parent_chain": true,
    "same_session": true,
    "remembers": true,
    "first_failure": null
  }
}
```

**Diagnosis:** Pipeline is healthy. Look elsewhere for issues.

---

### Example 2: Session Persistence Fails (Vertex)

```json
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
```

**Diagnosis:** Response never made it to session history.

**Action:**
1. Check SDK logs around message persistence
2. Verify Vertex-specific configuration
3. Compare with Anthropic behavior
4. File SDK issue with reproducible case

---

### Example 3: Parent Chain Broken

```json
{
  "test_name": "3_jsonl_transcript",
  "backend": "vertex",
  "passed": false,
  "details": {
    "found_content": true,
    "found_uuid": "xyz789",
    "parent_chain_length": 0,
    "total_entries": 15
  }
}
```

**Diagnosis:** Response exists but has no parent chain (orphaned).

**Action:**
1. Inspect JSONL manually
2. Check for conversation branching
3. Verify session continuation logic

---

### Example 4: Matrix Shows First Failure

```json
{
  "test_name": "5_backend_matrix",
  "backend": "vertex",
  "passed": false,
  "details": {
    "streamed": true,
    "in_history": false,  ← First failure
    "correct_parent_chain": null,
    "same_session": null,
    "remembers": false,
    "first_failure": "in_history"
  }
}
```

**Diagnosis:** Response streamed correctly but never persisted.

**Pipeline breakdown:**
```
✓ Claude generates
✓ SDK receives
✓ receive_response() emits
✗ Transcript persists  ← BREAKS HERE
? Active branch
? Session continues
✗ Remembers
```

**Action:** Instrument stage 4 (transcript persistence).

---

## Advanced: Custom Test

### Create Your Own Diagnostic

```python
from session_diagnostics import DiagnosticResult
import asyncio

async def custom_test(diagnostics, backend, session_id):
    """Test for specific edge case"""
    
    # Your custom logic here
    custom_check_passed = True  # Replace with actual test
    
    result = DiagnosticResult(
        test_name="custom_edge_case",
        backend=backend,
        passed=custom_check_passed,
        details={
            "custom_metric": 42,
            "note": "Testing specific scenario"
        },
        timestamp=datetime.now().isoformat(),
        session_id=session_id
    )
    
    diagnostics.record_result(result)
    return result
```

---

## Troubleshooting

### "SDK not available"
```bash
pip install claude-agent-sdk
```

### "Session history APIs not available"
```bash
pip install --upgrade claude-agent-sdk  # Requires 0.1.46+
```

### "Transcript not found"
Check SDK configuration for session storage location:
```python
from claude_agent_sdk import list_sessions

sessions = list_sessions(directory="/path/to/project")
print(sessions)
```

### "UnicodeEncodeError"
Already fixed in current version. If you see this, ensure you have the latest files.

---

## Next Steps

1. **Run the framework test** to verify installation
   ```bash
   python session_diagnostics.py
   ```

2. **Run interactive test** with your SDK client
   ```bash
   python interactive_test.py
   ```

3. **Compare backends** (Anthropic vs Vertex)

4. **Analyze JSONL transcripts** for detailed inspection

5. **File SDK issues** with reproducible test cases

---

## Getting Help

- **SDK Issues:** https://github.com/anthropics/claude-agent-sdk-python/issues
- **This Framework:** See README.md and DIAGNOSTICS_SUMMARY.md
- **Original Diagnostic Framework:** https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2

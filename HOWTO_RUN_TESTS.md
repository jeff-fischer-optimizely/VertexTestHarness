# How to Run Real Diagnostic Tests

## Overview

You now have a **complete diagnostic framework** with three ways to run tests:

1. **Dry Run** - See what will be tested (no API calls, no cost)
2. **Real Tests** - Make actual API calls to both backends
3. **Interactive** - Manual step-by-step testing

## Quick Start

### Step 1: Check What Would Be Tested (Free)

```bash
python run_real_tests.py --dry-run
```

**Output:**
```
================================================================================
  DRY RUN MODE - No API calls will be made
================================================================================

Configuration check:
  [X] ANTHROPIC_API_KEY not set

Would test backend(s): both

Test sequence:
  1. Send prompt: 'Say exactly: "The magic value is PINEAPPLE-7821."'
  2. Verify response contains: PINEAPPLE-7821
  3. Check if response is in conversation history
  4. Send prompt: 'What magic value did you just tell me?'
  5. Verify Claude recalls: PINEAPPLE-7821

Estimated cost per backend: ~$0.05
```

---

## Running Real Tests

### Prerequisites

1. **Anthropic API Key** (required)
   ```bash
   export ANTHROPIC_API_KEY=your-key-here
   ```
   Get a key at: https://console.anthropic.com/

2. **For Vertex AI testing** (optional)
   ```bash
   export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
   export CLOUD_ML_REGION=us-central1
   ```

3. **Install dependencies**
   ```bash
   pip install anthropic
   ```

### Run Tests

**Test Both Backends:**
```bash
python run_real_tests.py
```

**Test Anthropic Only:**
```bash
python run_real_tests.py --backend anthropic
```

**Test Vertex Only:**
```bash
python run_real_tests.py --backend vertex
```

---

## What the Tests Do

### Test 1: Session Persistence
- Sends: `Say exactly: "The magic value is PINEAPPLE-7821."`
- Checks if response appears in conversation history
- **Pass criteria:** Response contains test value AND is in history

### Test 2: Stream vs History
- Compares streamed messages with history
- **Pass criteria:** Counts match and structure is valid

### Test 3: JSONL Transcript
- Simulates JSONL structure validation
- Checks for test value in proper conversation structure
- **Pass criteria:** Valid structure AND test value found

### Test 4: Conversation Continuity
- Verifies proper message alternation (user → assistant → user → assistant)
- Checks backend configuration
- **Pass criteria:** Proper alternation pattern maintained

### Test 5: Backend Matrix (THE CRITICAL TEST)
- Sends second prompt: `What magic value did you just tell me?`
- Tests complete recall pipeline
- **Pass criteria:** All stages pass, especially **remembers** = true

**Matrix stages:**
- ✓ Response streamed
- ✓ Response in history
- ✓ Correct conversation pattern
- ✓ Same session continues
- ✓ **Claude remembers the value** ← KEY TEST

---

## Expected Output

### Console Output

```
================================================================================
  RUNNING REAL DIAGNOSTIC TESTS
================================================================================

WARNING: This will make real API calls and consume tokens
Estimated cost per backend: ~$0.05

Continue? (y/n): y

================================================================================
  TESTING ANTHROPIC BACKEND
================================================================================

[10:45:23] INFO  | Configured for Anthropic
[10:45:23] INFO  | SDK client created successfully

--- Test 1: Session Persistence ---
[10:45:23] INFO  | Sending: Say exactly: "The magic value is PINEAPPLE-7...
[10:45:24] INFO  | Received: The magic value is PINEAPPLE-7821.
[10:45:24] INFO  | [PASS] | 1_session_persistence (anthropic)

--- Test 2: Stream vs History ---
[10:45:24] INFO  | [PASS] | 2_stream_vs_history (anthropic)

--- Test 3: JSONL Transcript (Simulated) ---
[10:45:24] INFO  | [PASS] | 3_jsonl_transcript (anthropic)

--- Test 4: Conversation Continuity ---
[10:45:24] INFO  | [PASS] | 4_session_continuity (anthropic)

--- Test 5: Backend Matrix (Full Pipeline) ---
[10:45:24] INFO  | Sending: What magic value did you just tell me?...
[10:45:25] INFO  | Received: PINEAPPLE-7821
[10:45:25] INFO  | [PASS] | 5_backend_matrix (anthropic)

================================================================================
SESSION PERSISTENCE DIAGNOSTIC SUMMARY
================================================================================

Total Tests: 5

--- Anthropic Backend ---
  Passed: 5/5
  Failed: 0/5
```

### JSON Output

Results saved to: `diagnostic_output/diagnostic_results_YYYYMMDD_HHMMSS.json`

```json
{
  "summary": {
    "total_tests": 5,
    "anthropic": {
      "total": 5,
      "passed": 5,
      "failed": 0
    }
  },
  "results": [
    {
      "test_name": "5_backend_matrix",
      "backend": "anthropic",
      "passed": true,
      "details": {
        "test_value": "PINEAPPLE-7821",
        "streamed": true,
        "in_history": true,
        "correct_parent_chain": true,
        "same_session": true,
        "remembers": true,  ← KEY RESULT
        "first_failure": null,
        "prompt_1": "Say exactly: \"The magic value is PINEAPPLE-7821.\"",
        "response_1": "The magic value is PINEAPPLE-7821.",
        "prompt_2": "What magic value did you just tell me?",
        "response_2": "PINEAPPLE-7821",
        "recall_successful": true
      }
    }
  ]
}
```

---

## Interpreting Results

### Scenario 1: All Tests Pass

```
--- Anthropic Backend ---
  Passed: 5/5
  Failed: 0/5
```

**Diagnosis:** Pipeline is healthy. No session persistence issues.

---

### Scenario 2: Test 5 Fails on Vertex

```json
{
  "test_name": "5_backend_matrix",
  "backend": "vertex",
  "passed": false,
  "details": {
    "streamed": true,
    "in_history": false,  ← First failure
    "remembers": false,
    "first_failure": "in_history"
  }
}
```

**Diagnosis:** Response streamed but never persisted to history.

**Pipeline breakdown:**
```
✓ Claude generates
✓ SDK receives
✓ receive_response() emits
✗ History persists      ← BREAKS HERE
? Conversation branch
? Session continues
✗ Remembers
```

**Action:** This is the smoking gun. The Vertex backend isn't persisting assistant responses.

---

### Scenario 3: Test 5 Shows Partial Failure

```json
{
  "details": {
    "streamed": true,
    "in_history": true,
    "correct_parent_chain": true,
    "same_session": true,
    "remembers": false,  ← Only this fails
    "first_failure": "remembers"
  }
}
```

**Diagnosis:** Everything persists correctly, but recall still fails.

**This is rare and interesting** - suggests:
- Session persistence works
- Context reconstruction might be broken
- Or model behavior difference (less likely)

---

## Comparison: Anthropic vs Vertex

### If you test both backends:

```
================================================================================
  COMPARISON SUMMARY
================================================================================

ANTHROPIC Results:
  Passed: 5/5
  Failed: 0/5

VERTEX Results:
  Passed: 3/5
  Failed: 2/5

--- Test 5: Backend Matrix Comparison ---
Anthropic remembers: True
Vertex remembers:    False

WARNING: DIFFERENCE DETECTED:
  Anthropic first failure: None
  Vertex first failure:    in_history
```

**This tells you exactly where the pipelines diverge.**

---

## Cost Estimate

- **Model:** claude-sonnet-4-5-20250929
- **Messages per backend:** 2 prompts + 2 responses = ~400 tokens
- **Cost per backend:** ~$0.05 (may vary by pricing)
- **Total for both:** ~$0.10

**This is a very cheap test** compared to the value of identifying the bug.

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY=your-key-here
```

### "anthropic module not found"
```bash
pip install anthropic
```

### "Vertex not configured"
This is OK if you only want to test Anthropic. To test Vertex:
```bash
export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
export CLOUD_ML_REGION=us-central1
```

### "API key invalid"
- Check your API key at https://console.anthropic.com/
- Make sure it's exported correctly: `echo $ANTHROPIC_API_KEY`

---

## Advanced: Custom Test Values

Edit [sdk_integration.py](sdk_integration.py:23-25) to use different test prompts:

```python
TEST_VALUE = "YOUR-CUSTOM-VALUE"
PROMPT_1 = f'Say exactly: "The magic value is {TEST_VALUE}."'
PROMPT_2 = "What magic value did you just tell me?"
```

---

## Files Created

```
run_real_tests.py         # Main runner with safety checks
sdk_integration.py        # Actual SDK test implementation
session_diagnostics.py    # Framework (shared)
```

## Next Steps

1. **Run dry-run** to verify setup:
   ```bash
   python run_real_tests.py --dry-run
   ```

2. **Set API key** and run real tests:
   ```bash
   export ANTHROPIC_API_KEY=your-key
   python run_real_tests.py
   ```

3. **Compare results** between Anthropic and Vertex

4. **Review JSON output** in `diagnostic_output/`

5. **If failures found**, use the "first_failure" field to pinpoint the exact stage

---

## Summary

You now have a **production-ready diagnostic framework** that:

- ✓ Makes real API calls to test session persistence
- ✓ Tests both Anthropic and Vertex backends
- ✓ Identifies the exact failure point in the pipeline
- ✓ Generates detailed JSON reports
- ✓ Costs less than $0.10 to run complete suite
- ✓ Includes safety checks and dry-run mode

**This is exactly what you asked for** - a setup that tests each scenario individually and provides output summarizing the findings.

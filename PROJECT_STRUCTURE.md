# Session Diagnostics - Project Structure

```
c:\src\EpiServer\VertextTestHarness/
│
├── Core Framework
│   ├── session_diagnostics.py          # Main diagnostic framework (5 test types)
│   ├── run_diagnostics.py              # Automated test runner
│   └── interactive_test.py             # Interactive guided testing
│
├── Documentation
│   ├── README.md                       # Comprehensive usage guide
│   ├── DIAGNOSTICS_SUMMARY.md          # Executive summary
│   ├── USAGE_EXAMPLES.md               # Detailed examples
│   └── PROJECT_STRUCTURE.md            # This file
│
├── Setup & Scripts
│   ├── requirements.txt                # Python dependencies
│   └── quick_start.sh                  # One-command setup
│
├── Output (created on first run)
│   └── diagnostic_output/
│       └── diagnostic_results_*.json   # Test results with timestamps
│
└── Legacy Harnesses (pre-existing)
    ├── ClaudeHarness/
    │   ├── ClaudeEval.sh
    │   └── claude_eval_output.log
    └── VertexHarness/
        ├── VertexEval.sh
        └── vertex_eval_output.log
```

## File Purposes

### Core Framework

**session_diagnostics.py** (527 lines)
- `SessionDiagnostics` class with 5 test methods
- Test 1: `test_session_persistence()` - Verify assistant response in history
- Test 2: `test_stream_vs_history()` - Compare streamed vs persisted
- Test 3: `test_jsonl_transcript()` - Inspect parent chains in JSONL
- Test 4: `test_session_continuity()` - Track session ID across turns
- Test 5: `test_backend_matrix()` - Comprehensive pipeline comparison
- Helper functions for summarization and reporting

**run_diagnostics.py** (282 lines)
- `DiagnosticRunner` class orchestrates all 5 tests
- Backend configuration (Anthropic vs Vertex)
- Command-line interface: `--backend {anthropic|vertex|both}`
- Generates placeholder results (integrate with your SDK client)

**interactive_test.py** (318 lines)
- `InteractiveDiagnostic` class for guided testing
- Prompts user through each test step
- Captures manual verification results
- Works with or without SDK installed

### Documentation

**README.md** (492 lines)
- Detailed test descriptions
- Installation instructions
- Usage examples
- Output interpretation
- Known SDK issues

**DIAGNOSTICS_SUMMARY.md** (365 lines)
- Executive overview
- Problem statement
- Pipeline visualization
- Quick reference for each test
- Success criteria

**USAGE_EXAMPLES.md** (477 lines)
- Step-by-step workflows
- Code examples
- Troubleshooting
- Advanced customization

**PROJECT_STRUCTURE.md** (This file)
- File organization
- Component descriptions
- Quick reference

### Setup & Scripts

**requirements.txt**
```
claude-agent-sdk>=0.1.46
```

**quick_start.sh**
- One-command setup and execution
- Dependency checking
- Output directory creation

## Quick Reference

### Run Framework Test
```bash
python session_diagnostics.py
```

### Run Interactive Test
```bash
python interactive_test.py
```

### Run Automated (Both Backends)
```bash
python run_diagnostics.py --backend both
```

### Quick Start
```bash
./quick_start.sh
```

## Key Classes

### `DiagnosticResult` (dataclass)
```python
@dataclass
class DiagnosticResult:
    test_name: str
    backend: str
    passed: bool
    details: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None
```

### `SessionDiagnostics`
```python
class SessionDiagnostics:
    def __init__(self, output_dir: Path)
    
    # Test methods
    async def test_session_persistence(...)
    async def test_stream_vs_history(...)
    async def test_jsonl_transcript(...)
    async def test_session_continuity(...)
    async def test_backend_matrix(...)
    
    # Reporting
    def record_result(result: DiagnosticResult)
    def generate_summary() -> Dict
    def print_summary()
    def save_results() -> Path
```

### `DiagnosticRunner`
```python
class DiagnosticRunner:
    def __init__(self, backend: str)
    def setup_environment()
    async def run_all_tests()
    
    # Individual test runners
    async def run_test_1()  # Session persistence
    async def run_test_2()  # Stream vs history
    async def run_test_3()  # JSONL transcript
    async def run_test_4()  # Session continuity
    async def run_test_5()  # Backend matrix
```

### `InteractiveDiagnostic`
```python
class InteractiveDiagnostic:
    def __init__(self, backend: str)
    async def run_interactive_suite()
    
    # Interactive test methods
    async def interactive_test_1()
    async def interactive_test_2()
    async def interactive_test_3()
    async def interactive_test_4()
    async def interactive_test_5()
```

## Output Format

### Console
```
[10:32:06] INFO  | Detected backend: ANTHROPIC
[10:32:06] INFO  | [PASS] | 1_session_persistence (anthropic)
[10:32:06] INFO  | [FAIL] | 1_session_persistence (vertex)

================================================================================
SESSION PERSISTENCE DIAGNOSTIC SUMMARY
================================================================================
...
```

### JSON
```json
{
  "summary": {
    "total_tests": 10,
    "anthropic": {"total": 5, "passed": 5, "failed": 0},
    "vertex": {"total": 5, "passed": 2, "failed": 3}
  },
  "results": [...]
}
```

## Test Prompts

### Establish Test Value
```
Say exactly: "PINEAPPLE-7821 is the magic value."
```

### Recall Test Value
```
What magic value did you just tell me?
```

## Environment Variables

### Anthropic Backend
```bash
unset CLAUDE_CODE_USE_VERTEX
```

### Vertex Backend
```bash
export CLAUDE_CODE_USE_VERTEX=true
export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id
export CLOUD_ML_REGION=us-central1
```

## Dependencies

- Python 3.8+
- `claude-agent-sdk` (optional, but required for Tests 1-2)
- No other external dependencies

## Integration Points

### With Your SDK Client
```python
from session_diagnostics import SessionDiagnostics

diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))
# Use diagnostics.test_* methods with your SDK client
```

### With Existing Harnesses
```bash
# ClaudeHarness/ClaudeEval.sh - Anthropic backend Harbor tests
# VertexHarness/VertexEval.sh - Vertex backend Harbor tests
# These are separate from the diagnostic framework
```

## Next Steps

1. Read [README.md](README.md) for comprehensive documentation
2. Run `python session_diagnostics.py` to verify setup
3. Review [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for workflows
4. Run `python interactive_test.py` for guided testing

## References

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk-python)
- [Original Framework](https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2)

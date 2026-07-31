"""
Session Persistence Diagnostics for Claude Agent SDK

Based on the diagnostic framework from:
https://chatgpt.com/share/6a6cb07a-5b1c-83ea-8193-45ceae8f92f2

Tests the complete message pipeline to identify where persistence breaks:
  Claude generates → SDK receives → stream emits → transcript persists
  → branch linkage → resume/continue → context reconstruction
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    from claude_agent_sdk import (
        list_sessions,
        get_session_info,
        get_session_messages,
    )
    SDK_HAS_HISTORY_API = True
except ImportError:
    SDK_HAS_HISTORY_API = False
    print("WARNING: Session history APIs not available (requires SDK 0.1.46+)")


@dataclass
class DiagnosticResult:
    """Result from a single diagnostic test"""
    test_name: str
    backend: str  # "anthropic" or "vertex"
    passed: bool
    details: Dict[str, Any]
    timestamp: str
    session_id: Optional[str] = None


class SessionDiagnostics:
    """Comprehensive session persistence diagnostic suite"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[DiagnosticResult] = []

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] {level:5s} | {message}")

    def record_result(self, result: DiagnosticResult):
        """Record a test result"""
        self.results.append(result)
        status = "[PASS]" if result.passed else "[FAIL]"
        self.log(f"{status} | {result.test_name} ({result.backend})")

    # =========================================================================
    # Test 1: Persisted Session History
    # =========================================================================

    async def test_session_persistence(
        self,
        backend: str,
        session_id: str,
        expected_assistant_content: str
    ) -> DiagnosticResult:
        """
        Test 1: Check the persisted session history

        Verifies that Claude's assistant response actually made it into
        the session history using the official SDK APIs.
        """
        test_name = "1_session_persistence"

        if not SDK_HAS_HISTORY_API:
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": "SDK history APIs not available"},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        try:
            messages = get_session_messages(session_id=session_id)

            # Find the expected assistant message
            found = False
            assistant_messages = [m for m in messages if m.get("role") == "assistant"]

            for msg in assistant_messages:
                content = msg.get("content", [])
                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    if any(expected_assistant_content in text for text in text_parts):
                        found = True
                        break

            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=found,
                details={
                    "expected_content": expected_assistant_content,
                    "found_in_history": found,
                    "total_messages": len(messages),
                    "assistant_messages": len(assistant_messages)
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        except Exception as e:
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

    # =========================================================================
    # Test 2: Stream vs History Comparison
    # =========================================================================

    async def test_stream_vs_history(
        self,
        backend: str,
        session_id: str,
        streamed_messages: List[Dict],
    ) -> DiagnosticResult:
        """
        Test 2: Compare receive_response() against session history

        Verifies that messages emitted by receive_response() match
        what gets persisted to session history.
        """
        test_name = "2_stream_vs_history"

        if not SDK_HAS_HISTORY_API:
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": "SDK history APIs not available"},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        try:
            history = get_session_messages(session_id=session_id)

            # Compare counts
            stream_count = len(streamed_messages)
            history_count = len(history)

            # Extract assistant messages for comparison
            stream_assistant = [m for m in streamed_messages if m.get("role") == "assistant"]
            history_assistant = [m for m in history if m.get("role") == "assistant"]

            match = stream_count == history_count

            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=match,
                details={
                    "stream_total": stream_count,
                    "history_total": history_count,
                    "stream_assistant": len(stream_assistant),
                    "history_assistant": len(history_assistant),
                    "counts_match": match
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        except Exception as e:
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

    # =========================================================================
    # Test 3: JSONL Transcript Inspection
    # =========================================================================

    async def test_jsonl_transcript(
        self,
        backend: str,
        session_id: str,
        transcript_path: Path,
        expected_content: str
    ) -> DiagnosticResult:
        """
        Test 3: Inspect the underlying JSONL transcript

        Verifies the raw transcript structure, parent relationships,
        and conversation branching.
        """
        test_name = "3_jsonl_transcript"

        if not transcript_path.exists():
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": f"Transcript not found: {transcript_path}"},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            entries = [json.loads(line) for line in lines if line.strip()]

            # Find entries with expected content
            found_content = False
            found_uuid = None
            parent_chain = []

            for entry in entries:
                message = entry.get("message", {})
                content = message.get("content", [])

                if isinstance(content, list):
                    text_parts = [c.get("text", "") for c in content if c.get("type") == "text"]
                    if any(expected_content in text for text in text_parts):
                        found_content = True
                        found_uuid = entry.get("uuid")

                        # Build parent chain
                        current = entry
                        while current.get("parentUuid"):
                            parent_chain.append(current.get("parentUuid"))
                            # Find parent
                            current = next((e for e in entries if e.get("uuid") == current.get("parentUuid")), None)
                            if not current:
                                break

            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=found_content,
                details={
                    "found_content": found_content,
                    "found_uuid": found_uuid,
                    "parent_chain_length": len(parent_chain),
                    "total_entries": len(entries),
                    "transcript_path": str(transcript_path)
                },
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

        except Exception as e:
            return DiagnosticResult(
                test_name=test_name,
                backend=backend,
                passed=False,
                details={"error": str(e), "error_type": type(e).__name__},
                timestamp=datetime.now().isoformat(),
                session_id=session_id
            )

    # =========================================================================
    # Test 4: Session ID Continuity
    # =========================================================================

    async def test_session_continuity(
        self,
        backend: str,
        session_ids: List[str],
        cwd_list: List[str],
        config_info: Dict[str, Any]
    ) -> DiagnosticResult:
        """
        Test 4: Verify the session ID doesn't change unexpectedly

        Tracks session ID across turns to detect accidental session switches.
        """
        test_name = "4_session_continuity"

        unique_sessions = set(session_ids)
        expected_single_session = len(unique_sessions) == 1
        unique_cwds = set(cwd_list)

        return DiagnosticResult(
            test_name=test_name,
            backend=backend,
            passed=expected_single_session,
            details={
                "session_ids": list(unique_sessions),
                "session_count": len(unique_sessions),
                "expected_single_session": expected_single_session,
                "cwds": list(unique_cwds),
                "config": config_info
            },
            timestamp=datetime.now().isoformat(),
            session_id=session_ids[0] if session_ids else None
        )

    # =========================================================================
    # Test 5: Anthropic vs Vertex Matrix
    # =========================================================================

    async def test_backend_matrix(
        self,
        backend: str,
        streamed: bool,
        in_history: bool,
        correct_parent_chain: bool,
        same_session: bool,
        remembers: bool,
        test_value: str
    ) -> DiagnosticResult:
        """
        Test 5: Backend comparison matrix

        Compares Anthropic vs Vertex across all diagnostic dimensions:
        - Response streamed
        - Response in session history
        - Correct parent relationship
        - Same session continues
        - Next turn remembers value
        """
        test_name = "5_backend_matrix"

        # All stages should pass
        all_passed = all([
            streamed,
            in_history,
            correct_parent_chain,
            same_session,
            remembers
        ])

        return DiagnosticResult(
            test_name=test_name,
            backend=backend,
            passed=all_passed,
            details={
                "test_value": test_value,
                "streamed": streamed,
                "in_history": in_history,
                "correct_parent_chain": correct_parent_chain,
                "same_session": same_session,
                "remembers": remembers,
                "first_failure": self._find_first_failure([
                    ("streamed", streamed),
                    ("in_history", in_history),
                    ("correct_parent_chain", correct_parent_chain),
                    ("same_session", same_session),
                    ("remembers", remembers)
                ])
            },
            timestamp=datetime.now().isoformat()
        )

    def _find_first_failure(self, checks: List[tuple]) -> Optional[str]:
        """Helper to identify first failure point in pipeline"""
        for name, passed in checks:
            if not passed:
                return name
        return None

    # =========================================================================
    # Summary & Reporting
    # =========================================================================

    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary of all test results"""
        anthropic_results = [r for r in self.results if r.backend == "anthropic"]
        vertex_results = [r for r in self.results if r.backend == "vertex"]

        return {
            "total_tests": len(self.results),
            "anthropic": {
                "total": len(anthropic_results),
                "passed": sum(1 for r in anthropic_results if r.passed),
                "failed": sum(1 for r in anthropic_results if not r.passed)
            },
            "vertex": {
                "total": len(vertex_results),
                "passed": sum(1 for r in vertex_results if r.passed),
                "failed": sum(1 for r in vertex_results if not r.passed)
            },
            "test_breakdown": self._test_breakdown()
        }

    def _test_breakdown(self) -> Dict[str, Dict[str, int]]:
        """Break down results by test type"""
        breakdown = {}
        for result in self.results:
            if result.test_name not in breakdown:
                breakdown[result.test_name] = {"anthropic_pass": 0, "anthropic_fail": 0, "vertex_pass": 0, "vertex_fail": 0}

            key = f"{result.backend}_{'pass' if result.passed else 'fail'}"
            breakdown[result.test_name][key] += 1

        return breakdown

    def save_results(self, suffix: str = ""):
        """Save all results to JSON file"""
        if suffix:
            filename = f"diagnostic_results_{suffix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            filename = f"diagnostic_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_file = self.output_dir / filename

        output = {
            "summary": self.generate_summary(),
            "results": [asdict(r) for r in self.results],
            "timestamp": datetime.now().isoformat()
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)

        self.log(f"Results saved to: {output_file}", "INFO")
        return output_file

    def print_summary(self):
        """Print formatted summary to console"""
        summary = self.generate_summary()

        print("\n" + "="*80)
        print("SESSION PERSISTENCE DIAGNOSTIC SUMMARY")
        print("="*80)

        print(f"\nTotal Tests: {summary['total_tests']}")

        print("\n--- Anthropic Backend ---")
        print(f"  Passed: {summary['anthropic']['passed']}/{summary['anthropic']['total']}")
        print(f"  Failed: {summary['anthropic']['failed']}/{summary['anthropic']['total']}")

        print("\n--- Vertex Backend ---")
        print(f"  Passed: {summary['vertex']['passed']}/{summary['vertex']['total']}")
        print(f"  Failed: {summary['vertex']['failed']}/{summary['vertex']['total']}")

        print("\n--- Test Breakdown ---")
        for test_name, counts in summary['test_breakdown'].items():
            print(f"\n{test_name}:")
            print(f"  Anthropic: {counts['anthropic_pass']} pass, {counts['anthropic_fail']} fail")
            print(f"  Vertex:    {counts['vertex_pass']} pass, {counts['vertex_fail']} fail")

        print("\n" + "="*80 + "\n")


# =============================================================================
# Helper Functions
# =============================================================================

def detect_backend() -> str:
    """Detect which backend is currently configured"""
    if os.getenv("CLAUDE_CODE_USE_VERTEX") == "true":
        return "vertex"
    return "anthropic"


def get_session_info_safe(session_id: str) -> Optional[Dict]:
    """Safely get session info if API is available"""
    if not SDK_HAS_HISTORY_API:
        return None
    try:
        return get_session_info(session_id=session_id)
    except Exception as e:
        print(f"Error getting session info: {e}")
        return None


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """Main diagnostic runner"""
    diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))

    backend = detect_backend()
    diagnostics.log(f"Detected backend: {backend.upper()}", "INFO")

    # This is a framework - actual test execution would be driven by
    # external test runners that interact with Claude Agent SDK
    diagnostics.log("Diagnostic framework initialized", "INFO")
    diagnostics.log("Use this class in your test harness to run diagnostics", "INFO")

    # Example placeholder result
    example_result = DiagnosticResult(
        test_name="example",
        backend=backend,
        passed=True,
        details={"note": "This is an example result"},
        timestamp=datetime.now().isoformat()
    )
    diagnostics.record_result(example_result)

    diagnostics.print_summary()
    diagnostics.save_results()


if __name__ == "__main__":
    asyncio.run(main())

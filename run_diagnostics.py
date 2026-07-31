"""
Diagnostic Test Runner

Executes the 5 core diagnostic tests against both Anthropic and Vertex backends
to identify where session persistence breaks.

Usage:
    python run_diagnostics.py --backend anthropic
    python run_diagnostics.py --backend vertex
    python run_diagnostics.py --backend both
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

from session_diagnostics import SessionDiagnostics, DiagnosticResult


# Test configuration
TEST_VALUE = "FACT-9147"
TEST_PROMPT_1 = f'Say exactly: "{TEST_VALUE} is the authentication bug."'
TEST_PROMPT_2 = "What did you just say the authentication bug was?"


class DiagnosticRunner:
    """Orchestrates diagnostic test execution"""

    def __init__(self, backend: str):
        self.backend = backend
        self.diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))
        self.session_ids = []
        self.cwds = []

    def setup_environment(self):
        """Configure environment for the target backend"""
        if self.backend == "vertex":
            os.environ["CLAUDE_CODE_USE_VERTEX"] = "true"
            # Assumes project ID and region are already set
            self.diagnostics.log("Configured for Vertex AI", "INFO")
        else:
            os.environ.pop("CLAUDE_CODE_USE_VERTEX", None)
            os.environ.pop("ANTHROPIC_VERTEX_PROJECT_ID", None)
            os.environ.pop("CLOUD_ML_REGION", None)
            self.diagnostics.log("Configured for Anthropic", "INFO")

    async def run_all_tests(self):
        """Execute all 5 diagnostic tests"""
        self.setup_environment()

        self.diagnostics.log(f"Starting diagnostic suite for {self.backend.upper()}", "INFO")

        # Test 1: Session Persistence
        await self.run_test_1()

        # Test 2: Stream vs History
        await self.run_test_2()

        # Test 3: JSONL Transcript
        await self.run_test_3()

        # Test 4: Session Continuity
        await self.run_test_4()

        # Test 5: Backend Matrix (comprehensive)
        await self.run_test_5()

        self.diagnostics.print_summary()
        output_file = self.diagnostics.save_results()

        return output_file

    async def run_test_1(self):
        """
        Test 1: Check the persisted session history

        Workflow:
        1. Send prompt with test value
        2. Immediately inspect session history
        3. Verify assistant response is present
        """
        self.diagnostics.log("Running Test 1: Session Persistence", "INFO")

        # NOTE: This is a placeholder implementation
        # In actual use, this would:
        # 1. Use Claude Agent SDK to send TEST_PROMPT_1
        # 2. Capture the session ID
        # 3. Use get_session_messages() to verify persistence

        # Placeholder result
        result = DiagnosticResult(
            test_name="1_session_persistence",
            backend=self.backend,
            passed=False,
            details={
                "note": "Manual test required",
                "instructions": [
                    f"1. Send prompt: {TEST_PROMPT_1}",
                    "2. Capture session ID",
                    "3. Run: get_session_messages(session_id)",
                    f"4. Verify assistant response contains: {TEST_VALUE}"
                ]
            },
            timestamp="",
            session_id="manual_test_required"
        )

        self.diagnostics.record_result(result)

    async def run_test_2(self):
        """
        Test 2: Compare receive_response() against session history

        Workflow:
        1. Capture all messages from receive_response()
        2. Capture session history from get_session_messages()
        3. Compare counts and content
        """
        self.diagnostics.log("Running Test 2: Stream vs History", "INFO")

        result = DiagnosticResult(
            test_name="2_stream_vs_history",
            backend=self.backend,
            passed=False,
            details={
                "note": "Manual test required",
                "instructions": [
                    "1. Capture streamed messages with:",
                    "   received = []",
                    "   async for message in client.receive_response():",
                    "       received.append(message)",
                    "2. Capture history with:",
                    "   history = get_session_messages(session_id)",
                    "3. Compare message counts and content"
                ]
            },
            timestamp="",
            session_id="manual_test_required"
        )

        self.diagnostics.record_result(result)

    async def run_test_3(self):
        """
        Test 3: Inspect the underlying JSONL transcript

        Workflow:
        1. Locate session JSONL file
        2. Parse entries and build parent chain
        3. Verify expected content is on active branch
        """
        self.diagnostics.log("Running Test 3: JSONL Transcript", "INFO")

        result = DiagnosticResult(
            test_name="3_jsonl_transcript",
            backend=self.backend,
            passed=False,
            details={
                "note": "Manual test required",
                "instructions": [
                    "1. Locate JSONL transcript file",
                    "2. Parse entries and check for:",
                    "   - uuid/parentUuid relationships",
                    f"   - Expected content: {TEST_VALUE}",
                    "   - Verify entry is on active conversation branch",
                    "3. Use session_diagnostics.test_jsonl_transcript() helper"
                ]
            },
            timestamp="",
            session_id="manual_test_required"
        )

        self.diagnostics.record_result(result)

    async def run_test_4(self):
        """
        Test 4: Verify the session ID doesn't change

        Workflow:
        1. Track session ID across multiple turns
        2. Track CWD and configuration
        3. Verify continuity
        """
        self.diagnostics.log("Running Test 4: Session Continuity", "INFO")

        config_info = {
            "backend": self.backend,
            "vertex_enabled": os.getenv("CLAUDE_CODE_USE_VERTEX") == "true",
            "vertex_project": os.getenv("ANTHROPIC_VERTEX_PROJECT_ID", ""),
            "vertex_region": os.getenv("CLOUD_ML_REGION", ""),
            "cwd": os.getcwd()
        }

        result = DiagnosticResult(
            test_name="4_session_continuity",
            backend=self.backend,
            passed=False,
            details={
                "note": "Manual test required",
                "config": config_info,
                "instructions": [
                    "1. Track session_id on each turn",
                    "2. Track cwd on each turn",
                    "3. Verify session_id remains constant",
                    "4. Check for unexpected session switches"
                ]
            },
            timestamp="",
            session_id="manual_test_required"
        )

        self.diagnostics.record_result(result)

    async def run_test_5(self):
        """
        Test 5: Comprehensive backend matrix

        Workflow:
        1. Run full conversation cycle
        2. Test all pipeline stages
        3. Identify first failure point
        """
        self.diagnostics.log("Running Test 5: Backend Matrix", "INFO")

        result = DiagnosticResult(
            test_name="5_backend_matrix",
            backend=self.backend,
            passed=False,
            details={
                "note": "Manual test required",
                "test_value": TEST_VALUE,
                "prompts": [TEST_PROMPT_1, TEST_PROMPT_2],
                "instructions": [
                    "1. Send first prompt (establish test value)",
                    "2. Verify response was streamed",
                    "3. Verify response in session history",
                    "4. Verify correct parent chain in JSONL",
                    "5. Verify same session continues",
                    "6. Send second prompt (recall test value)",
                    "7. Verify model remembers the value",
                    "8. Compare Anthropic vs Vertex results"
                ],
                "expected_results": {
                    "streamed": True,
                    "in_history": True,
                    "correct_parent_chain": True,
                    "same_session": True,
                    "remembers": True
                }
            },
            timestamp="",
            session_id="manual_test_required"
        )

        self.diagnostics.record_result(result)


async def main():
    parser = argparse.ArgumentParser(description="Run session persistence diagnostics")
    parser.add_argument(
        "--backend",
        choices=["anthropic", "vertex", "both"],
        default="both",
        help="Which backend to test"
    )

    args = parser.parse_args()

    if args.backend == "both":
        backends = ["anthropic", "vertex"]
    else:
        backends = [args.backend]

    for backend in backends:
        print(f"\n{'='*80}")
        print(f"Running diagnostics for: {backend.upper()}")
        print(f"{'='*80}\n")

        runner = DiagnosticRunner(backend)
        output_file = await runner.run_all_tests()

        print(f"\nResults saved to: {output_file}\n")


if __name__ == "__main__":
    asyncio.run(main())

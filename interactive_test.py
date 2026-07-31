"""
Interactive Session Diagnostic Test

Provides an interactive harness to manually test the 5 diagnostic scenarios
with real Claude Agent SDK calls and capture detailed results.

This script prompts you through each test and captures the necessary data
for diagnostic analysis.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from session_diagnostics import SessionDiagnostics, DiagnosticResult

# Try to import Claude Agent SDK
try:
    from claude_agent_sdk import (
        list_sessions,
        get_session_info,
        get_session_messages,
    )
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    print("WARNING: Claude Agent SDK not available")
    print("Install with: pip install claude-agent-sdk")


TEST_VALUE = "PINEAPPLE-7821"
PROMPT_1 = f'Say exactly: "The magic value is {TEST_VALUE}."'
PROMPT_2 = f"What magic value did you just tell me?"


class InteractiveDiagnostic:
    """Interactive test runner for session diagnostics"""

    def __init__(self, backend: str):
        self.backend = backend
        self.diagnostics = SessionDiagnostics(output_dir=Path("./diagnostic_output"))
        self.session_id: Optional[str] = None
        self.streamed_messages: List[Dict] = []
        self.turn_data: List[Dict] = []

    def setup_backend(self):
        """Configure environment for backend"""
        if self.backend == "vertex":
            os.environ["CLAUDE_CODE_USE_VERTEX"] = "true"
            print(f"\n✓ Configured for Vertex AI")
            print(f"  Project: {os.getenv('ANTHROPIC_VERTEX_PROJECT_ID', 'NOT SET')}")
            print(f"  Region: {os.getenv('CLOUD_ML_REGION', 'NOT SET')}")
        else:
            os.environ.pop("CLAUDE_CODE_USE_VERTEX", None)
            print(f"\n✓ Configured for Anthropic")

    def prompt_user(self, message: str) -> str:
        """Get user input"""
        return input(f"\n{message}\n> ").strip()

    def display_banner(self, title: str):
        """Display section banner"""
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")

    async def run_interactive_suite(self):
        """Run full interactive test suite"""
        self.setup_backend()
        self.display_banner(f"Interactive Diagnostics: {self.backend.upper()}")

        print("This interactive suite will guide you through 5 diagnostic tests.")
        print("You'll need to manually interact with Claude Agent SDK and provide data.")
        print("\nPress Enter to continue...")
        input()

        # Test 1
        await self.interactive_test_1()

        # Test 2
        await self.interactive_test_2()

        # Test 3
        await self.interactive_test_3()

        # Test 4
        await self.interactive_test_4()

        # Test 5
        await self.interactive_test_5()

        # Summary
        self.diagnostics.print_summary()
        output_file = self.diagnostics.save_results()
        print(f"\n✓ Results saved to: {output_file}")

    async def interactive_test_1(self):
        """Test 1: Session Persistence"""
        self.display_banner("Test 1: Session Persistence")

        print(f"Instructions:")
        print(f"1. Open a Claude Agent SDK session")
        print(f"2. Send this prompt: {PROMPT_1}")
        print(f"3. Note the session ID")
        print(f"4. Check if the assistant response appears in session history")

        if not SDK_AVAILABLE:
            print("\nWARNING: SDK not available - manual verification required")
            found = self.prompt_user("Did you find the assistant message in session history? (y/n)").lower() == 'y'
            self.session_id = self.prompt_user("Enter the session ID")
        else:
            self.session_id = self.prompt_user("Enter the session ID")

            try:
                result = await self.diagnostics.test_session_persistence(
                    backend=self.backend,
                    session_id=self.session_id,
                    expected_assistant_content=TEST_VALUE
                )
                self.diagnostics.record_result(result)
                return
            except Exception as e:
                print(f"Error: {e}")
                found = self.prompt_user("Manual check - was it in history? (y/n)").lower() == 'y'

        # Manual result
        result = DiagnosticResult(
            test_name="1_session_persistence",
            backend=self.backend,
            passed=found,
            details={"manual_verification": found, "session_id": self.session_id},
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id
        )
        self.diagnostics.record_result(result)

    async def interactive_test_2(self):
        """Test 2: Stream vs History"""
        self.display_banner("Test 2: Stream vs History")

        print("Instructions:")
        print("1. Count messages emitted by receive_response()")
        print("2. Count messages in session history")
        print("3. Compare the counts")

        stream_count = int(self.prompt_user("How many messages were streamed?"))
        history_count = int(self.prompt_user("How many messages in history?"))

        match = stream_count == history_count

        result = DiagnosticResult(
            test_name="2_stream_vs_history",
            backend=self.backend,
            passed=match,
            details={
                "stream_count": stream_count,
                "history_count": history_count,
                "counts_match": match
            },
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id
        )
        self.diagnostics.record_result(result)

    async def interactive_test_3(self):
        """Test 3: JSONL Transcript"""
        self.display_banner("Test 3: JSONL Transcript Inspection")

        print("Instructions:")
        print("1. Locate the JSONL transcript file for your session")
        print("2. Parse the file and look for the test value")
        print("3. Verify the parent/child relationships")

        transcript_path = self.prompt_user("Enter path to JSONL transcript (or 'skip')")

        if transcript_path.lower() == 'skip':
            found = self.prompt_user(f"Did you find '{TEST_VALUE}' in transcript? (y/n)").lower() == 'y'
            correct_chain = self.prompt_user("Is it on the active conversation branch? (y/n)").lower() == 'y'

            result = DiagnosticResult(
                test_name="3_jsonl_transcript",
                backend=self.backend,
                passed=found and correct_chain,
                details={
                    "found_content": found,
                    "correct_parent_chain": correct_chain,
                    "manual_verification": True
                },
                timestamp=datetime.now().isoformat(),
                session_id=self.session_id
            )
        else:
            result = await self.diagnostics.test_jsonl_transcript(
                backend=self.backend,
                session_id=self.session_id,
                transcript_path=Path(transcript_path),
                expected_content=TEST_VALUE
            )

        self.diagnostics.record_result(result)

    async def interactive_test_4(self):
        """Test 4: Session Continuity"""
        self.display_banner("Test 4: Session ID Continuity")

        print("Instructions:")
        print("1. Track session ID across multiple conversation turns")
        print("2. Verify it remains constant")

        num_turns = int(self.prompt_user("How many turns have you tested?"))

        session_ids = []
        for i in range(num_turns):
            sid = self.prompt_user(f"Session ID for turn {i+1}")
            session_ids.append(sid)

        unique_sessions = set(session_ids)
        same_session = len(unique_sessions) == 1

        config_info = {
            "backend": self.backend,
            "cwd": os.getcwd(),
            "vertex_enabled": os.getenv("CLAUDE_CODE_USE_VERTEX") == "true"
        }

        result = await self.diagnostics.test_session_continuity(
            backend=self.backend,
            session_ids=session_ids,
            cwd_list=[os.getcwd()] * num_turns,
            config_info=config_info
        )

        self.diagnostics.record_result(result)

    async def interactive_test_5(self):
        """Test 5: Backend Matrix"""
        self.display_banner("Test 5: Comprehensive Backend Matrix")

        print("Full pipeline test:")
        print(f"1. Send: {PROMPT_1}")
        print(f"2. Send: {PROMPT_2}")
        print("3. Verify all stages work correctly")

        print("\nFor each question, answer y/n:")

        streamed = self.prompt_user("Was the response streamed correctly?").lower() == 'y'
        in_history = self.prompt_user("Is the response in session history?").lower() == 'y'
        correct_chain = self.prompt_user("Is the parent chain correct in JSONL?").lower() == 'y'
        same_session = self.prompt_user("Did the session ID stay the same?").lower() == 'y'
        remembers = self.prompt_user(f"Did Claude remember '{TEST_VALUE}' on the next turn?").lower() == 'y'

        result = await self.diagnostics.test_backend_matrix(
            backend=self.backend,
            streamed=streamed,
            in_history=in_history,
            correct_parent_chain=correct_chain,
            same_session=same_session,
            remembers=remembers,
            test_value=TEST_VALUE
        )

        self.diagnostics.record_result(result)


async def main():
    print("="*80)
    print("  INTERACTIVE SESSION DIAGNOSTICS")
    print("="*80)

    backend = input("\nWhich backend? (anthropic/vertex): ").strip().lower()

    if backend not in ["anthropic", "vertex"]:
        print("Invalid backend. Choose 'anthropic' or 'vertex'")
        sys.exit(1)

    tester = InteractiveDiagnostic(backend)
    await tester.run_interactive_suite()


if __name__ == "__main__":
    asyncio.run(main())

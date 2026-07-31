"""
Run Real Diagnostic Tests

This script runs actual API calls to test session persistence between
Anthropic and Vertex backends.

IMPORTANT: This makes real API calls and will consume tokens.
Estimated cost per backend: ~$0.05 (depends on model pricing)

Usage:
    # Test both backends
    python run_real_tests.py

    # Test specific backend
    python run_real_tests.py --backend anthropic
    python run_real_tests.py --backend vertex

    # Dry run (no API calls)
    python run_real_tests.py --dry-run
"""

import asyncio
import argparse
import os
import sys
from pathlib import Path

# Check for API key
def check_environment():
    """Check if required environment variables are set"""
    issues = []

    if not os.getenv("ANTHROPIC_API_KEY"):
        issues.append("[X] ANTHROPIC_API_KEY not set")

    return issues


def print_setup_instructions():
    """Print setup instructions"""
    print("\n" + "="*80)
    print("  SETUP REQUIRED")
    print("="*80)
    print("\nTo run real diagnostic tests, you need:")
    print("\n1. Anthropic API Key:")
    print("   export ANTHROPIC_API_KEY=your-key-here")
    print("   Get a key at: https://console.anthropic.com/")

    print("\n2. For Vertex AI testing:")
    print("   export ANTHROPIC_VERTEX_PROJECT_ID=your-project-id")
    print("   export CLOUD_ML_REGION=us-central1")

    print("\n3. Install dependencies:")
    print("   pip install anthropic")

    print("\n" + "="*80 + "\n")


async def main():
    parser = argparse.ArgumentParser(description="Run real diagnostic tests")
    parser.add_argument(
        "--backend",
        choices=["anthropic", "vertex", "both"],
        default="both",
        help="Which backend to test"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be tested without making API calls"
    )

    args = parser.parse_args()

    # Check environment
    issues = check_environment()

    if args.dry_run:
        print("\n" + "="*80)
        print("  DRY RUN MODE - No API calls will be made")
        print("="*80)

        print("\nConfiguration check:")
        if issues:
            for issue in issues:
                print(f"  {issue}")
        else:
            print("  [OK] All environment variables set")

        print(f"\nWould test backend(s): {args.backend}")

        print("\nTest sequence:")
        print("  1. Send prompt: 'Say exactly: \"The magic value is PINEAPPLE-7821.\"'")
        print("  2. Verify response contains: PINEAPPLE-7821")
        print("  3. Check if response is in conversation history")
        print("  4. Send prompt: 'What magic value did you just tell me?'")
        print("  5. Verify Claude recalls: PINEAPPLE-7821")

        print("\nEstimated cost per backend: ~$0.05")
        print("\nTo run real tests:")
        print("  1. Set ANTHROPIC_API_KEY")
        print("  2. Run: python run_real_tests.py")

        print("\n" + "="*80 + "\n")
        return

    # Real run - check for issues
    if issues:
        print_setup_instructions()
        for issue in issues:
            print(issue)
        print("\nCannot proceed without required environment variables.")
        print("Use --dry-run to see what would be tested.\n")
        sys.exit(1)

    # Import the actual runner (only after env check)
    try:
        from sdk_integration import run_for_backend
    except ImportError as e:
        print(f"ERROR: Failed to import SDK integration: {e}")
        print("\nMake sure you have installed:")
        print("  pip install anthropic")
        sys.exit(1)

    print("\n" + "="*80)
    print("  RUNNING REAL DIAGNOSTIC TESTS")
    print("="*80)
    print("\nWARNING: This will make real API calls and consume tokens")
    print("Estimated cost per backend: ~$0.05\n")

    confirm = input("Continue? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Aborted.")
        return

    # Run tests
    backends_to_test = []
    if args.backend == "both":
        backends_to_test = ["anthropic"]
        # Only test Vertex if configured
        if os.getenv("ANTHROPIC_VERTEX_PROJECT_ID") and os.getenv("CLOUD_ML_REGION"):
            backends_to_test.append("vertex")
        else:
            print("\nWARNING: Vertex not configured - will only test Anthropic")
            print("To test Vertex, set ANTHROPIC_VERTEX_PROJECT_ID and CLOUD_ML_REGION\n")
    else:
        backends_to_test = [args.backend]

    results = {}
    for backend in backends_to_test:
        print(f"\n{'='*80}")
        print(f"  Testing {backend.upper()}")
        print(f"{'='*80}\n")

        output_file = await run_for_backend(backend)
        results[backend] = output_file

    # Summary
    print("\n" + "="*80)
    print("  TEST RESULTS")
    print("="*80)

    for backend, output_file in results.items():
        print(f"\n{backend.upper()}: {output_file}")

    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

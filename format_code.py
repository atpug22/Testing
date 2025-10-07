#!/usr/bin/env python3
"""
Code formatting script for the project.
"""
import subprocess
import sys
from pathlib import Path


def run_command(command: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False


def main():
    """Format all code in the project."""
    print("🎨 Starting code formatting...")

    # Get project root
    project_root = Path(__file__).parent

    # Define Python paths to format
    python_paths = [
        "app/",
        "api/",
        "core/",
        "tests/",
        "main.py",
        "format_code.py",
        "test_enhanced_ai.py",
    ]

    success_count = 0
    total_commands = 0

    # 1. Black formatting
    black_command = ["black"] + python_paths
    total_commands += 1
    if run_command(black_command, "Black formatting"):
        success_count += 1

    # 2. isort import sorting
    isort_command = ["isort", "--profile=black",
                     "--multi-line=3"] + python_paths
    total_commands += 1
    if run_command(isort_command, "Import sorting with isort"):
        success_count += 1

    # 3. Remove unused imports (optional)
    try:
        import autoflake

        autoflake_command = [
            "autoflake",
            "--remove-all-unused-imports",
            "--remove-unused-variables",
            "--in-place",
            "--recursive",
        ] + python_paths
        total_commands += 1
        if run_command(autoflake_command, "Removing unused imports"):
            success_count += 1
    except ImportError:
        print("ℹ️  autoflake not installed, skipping unused import removal")

    # Summary
    print(f"\n📊 Formatting Summary:")
    print(f"✅ Successful: {success_count}/{total_commands}")

    if success_count == total_commands:
        print("🎉 All formatting completed successfully!")
        return True
    else:
        print("⚠️  Some formatting operations failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

#!/usr/bin/env python3
"""
Code Quality Assessment Script

Runs various quality checks and provides actionable recommendations.
"""

import subprocess  # nosec B404


def run_command(cmd: str, description: str) -> tuple[int, str]:
    """Run a command and return exit code and output."""
    print(f"\n{'=' * 60}")
    print(f"🔍 {description}")
    print(f"{'=' * 60}")

    result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)  # nosec B602

    output = result.stdout + result.stderr
    print(output if output else "✅ No issues found")

    return result.returncode, output


def main():  # noqa: PLR0915
    """Run quality assessment."""
    print("""
╔══════════════════════════════════════════════════════════╗
║          CODE QUALITY ASSESSMENT REPORT                  ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Track metrics
    results = {}

    # 1. Linting check
    code, output = run_command("ruff check app/ --statistics", "Linting Issues (Ruff)")

    if code == 0:
        results["lint"] = "✅ PASS"
    else:
        # Extract issue count
        lines = output.strip().split("\n")
        if lines:
            last_line = lines[-1]
            if "errors" in last_line:
                results["lint"] = f"⚠️  {last_line}"

    # 2. Formatting check
    code, output = run_command("ruff format --check app/", "Code Formatting (Ruff)")
    results["format"] = "✅ PASS" if code == 0 else "❌ NEEDS FORMATTING"

    # 3. Type checking
    code, output = run_command(
        "mypy app/ --no-error-summary 2>&1 | head -5", "Type Checking (Mypy) - Sample"
    )
    results["types"] = "✅ PASS" if code == 0 else "⚠️  TYPE ISSUES FOUND"

    # 4. Security scan
    code, output = run_command("bandit -c pyproject.toml -r app/ -q", "Security Scan (Bandit)")
    results["security"] = "✅ PASS" if code == 0 else "⚠️  SECURITY ISSUES"

    # 5. Test coverage (if pytest available)
    print(f"\n{'=' * 60}")
    print("🧪 Test Coverage")
    print(f"{'=' * 60}")
    try:
        result = subprocess.run(
            ["pytest", "--co", "-q"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )  # nosec B603, B607
        test_count = len([line for line in result.stdout.split("\n") if "test_" in line])
        print(f"Found {test_count} tests")
        results["tests"] = f"✅ {test_count} tests found"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        results["tests"] = "⚠️  Unable to run tests"
        print("Unable to collect tests (dependencies may be missing)")

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 SUMMARY")
    print(f"{'=' * 60}\n")

    for check, status in results.items():
        print(f"{check.upper():12} : {status}")

    # Recommendations
    print(f"\n{'=' * 60}")
    print("💡 RECOMMENDED NEXT STEPS")
    print(f"{'=' * 60}\n")

    if "❌" in results.get("format", ""):
        print("1. 🎨 Format code:")
        print("   make format\n")

    if "errors" in results.get("lint", ""):
        print("2. 🔧 Fix linting issues:")
        print("   ruff check app/ --fix --unsafe-fixes\n")

    if "TYPE ISSUES" in results.get("types", ""):
        print("3. 📝 Review type issues:")
        print("   mypy app/ --show-error-context\n")

    if "SECURITY" in results.get("security", ""):
        print("4. 🔒 Review security issues:")
        print("   bandit -r app/ -v\n")

    print("5. 📈 Measure test coverage:")
    print("   pytest --cov=app --cov-report=html")
    print("   open htmlcov/index.html\n")

    print("6. 🚀 Run full validation:")
    print("   make validate\n")

    print(f"{'=' * 60}")
    print("📚 DOCUMENTATION")
    print(f"{'=' * 60}\n")
    print("Setup Guide:       docs/CODE_QUALITY.md")
    print("Improvements:      docs/CODE_QUALITY_IMPROVEMENTS.md")
    print("Review Checklist:  docs/CODE_REVIEW_CHECKLIST.md")
    print("Initial Report:    docs/CODE_QUALITY_REPORT.md")

    print(f"\n{'=' * 60}\n")


if __name__ == "__main__":
    main()

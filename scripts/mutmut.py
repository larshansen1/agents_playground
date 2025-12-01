#!/usr/bin/env python3
"""Extract surviving mutants from mutmut for AI processing."""

import subprocess


def get_mutant_list():
    """Get all mutants by running mutmut results."""
    result = subprocess.run(
        ["mutmut", "results", "--all", "true"], check=False, capture_output=True, text=True
    )
    return result.stdout


def get_mutant_diff(mutant_name):
    """Get the diff for a specific mutant."""
    result = subprocess.run(
        ["mutmut", "show", mutant_name], check=False, capture_output=True, text=True
    )
    return result.stdout


def parse_browse_output():
    """Parse file stats from mutmut browse (run interactively first to cache)."""
    # Based on your screenshot, manually define priority files
    return [
        ("app/tools/registry.py", 326, 2),  # 326 survived, 2 killed - worst ratio!
        ("app/worker_helpers.py", 186, 407),
        ("app/tasks.py", 14, 274),
        ("app/worker.py", 30, 397),
        ("app/calculator.py", 4, 42),
        ("app/worker_lease.py", 2, 115),
    ]


def export_for_ai():
    """Export surviving mutants in AI-friendly format."""

    output = {"summary": {}, "files": []}

    priority_files = parse_browse_output()

    for filepath, survived, killed in priority_files:
        file_data = {
            "path": filepath,
            "survived": survived,
            "killed": killed,
            "mutation_score": round(killed / (killed + survived) * 100, 1)
            if (killed + survived) > 0
            else 0,
            "priority": "high" if survived > killed else "medium",
            "surviving_mutants": [],
        }

        # Get mutants for this file
        # Mutant names follow pattern: app.module.xǁClassǁmethod__mutmut_N
        module_prefix = filepath.replace("/", ".").replace(".py", "")

        # Try to get mutants (this may need adjustment based on actual naming)
        for i in range(1, survived + 1):
            mutant_name = f"{module_prefix}__mutmut_{i}"
            try:
                diff = get_mutant_diff(mutant_name)
                if (diff and "Survived" in diff) or diff:
                    file_data["surviving_mutants"].append(
                        {
                            "name": mutant_name,
                            "diff": diff[:2000],  # Truncate for readability
                        }
                    )
            except Exception:
                pass

        output["files"].append(file_data)

    output["summary"] = {
        "total_files": len(priority_files),
        "total_survived": sum(f[1] for f in priority_files),
        "total_killed": sum(f[2] for f in priority_files),
    }

    return output


if __name__ == "__main__":
    # Simpler approach: just iterate through known mutant patterns
    print("Extracting mutants...")

    # Get a sample to understand naming
    result = subprocess.run(
        ["mutmut", "show", "app.worker_helpers.x__handle_workflow_completion__mutmut_1"],
        check=False,
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    print("---")
    print(result.stderr)

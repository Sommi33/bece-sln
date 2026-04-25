"""
system_test.py
--------------
Module owner: Semilore
Automated end-to-end system test for the BECE SLN project.

This script runs every module in the correct order and logs
whether each one passed or failed. It produces a JSON test report
that serves as evidence for Chapter 4.

Run from the bece-sln folder:
    python system_test.py
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
MODULES = [
    {
        "name": "Synthetic Data Generator",
        "script": "generate_students.py",
        "expected_output": "students.json",
        "description": "Generates 50 synthetic JSS3 student profiles with scores across 80 topics"
    },
    {
        "name": "Neo4j Knowledge Graph Loader",
        "script": "load_to_neo4j.py",
        "expected_output": None,  # writes to Neo4j, not a file
        "description": "Loads 50 students, 80 topics, and 4000 SCORED relationships into Neo4j"
    },
    {
        "name": "Complementarity Analysis",
        "script": "complementarity_analysis.py",
        "expected_output": "complementary_pairs.json",
        "description": "Computes student-student complementarity scores and writes COMPLEMENTS edges to Neo4j"
    },
    {
        "name": "SIR Knowledge Diffusion Simulation",
        "script": "sir_simulation.py",
        "expected_output": "sir_simulation_report.json",
        "description": "Simulates knowledge spread using the SIR epidemiological model"
    },
    {
        "name": "Predictive Model (Topic Dependencies)",
        "script": "predictive_model.py",
        "expected_output": "predictive_model_report.json",
        "description": "Identifies topic-topic dependencies and writes DEPENDS_ON edges to Neo4j"
    },
]

# Optional modules (may not be ready yet)
OPTIONAL_MODULES = [
    {
        "name": "Topic Failure Analysis (Adebayo)",
        "script": "topic_failure_analysis.py",
        "expected_output": "topic_failure_report.json",
        "description": "Analyses which topics the class fails most frequently"
    },
    {
        "name": "AI Clustering (Samuel)",
        "script": "ai_clustering.py",
        "expected_output": "peer_groups.json",
        "description": "Forms optimised peer study groups using K-Means clustering"
    },
]

REPORT_FILE = "system_test_report.json"


# -------------------------------------------------------------------
# TEST RUNNER
# -------------------------------------------------------------------
def run_module(module_info):
    """
    Run a single module and return the test result.
    """
    script = module_info["script"]
    name = module_info["name"]
    expected = module_info.get("expected_output")

    result = {
        "module": name,
        "script": script,
        "status": "NOT RUN",
        "duration_seconds": 0,
        "output_file_exists": None,
        "error": None,
        "timestamp": datetime.now().isoformat(),
    }

    # Check if script exists
    if not Path(script).exists():
        result["status"] = "SKIPPED"
        result["error"] = f"{script} not found in current directory"
        return result

    print(f"\n{'='*60}")
    print(f"TESTING: {name}")
    print(f"Script:  {script}")
    print(f"{'='*60}")

    start_time = time.time()

    try:
        # Run the script as a subprocess
        process = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per module
        )

        duration = time.time() - start_time
        result["duration_seconds"] = round(duration, 2)

        # Print the output
        if process.stdout:
            # Only print last 30 lines to keep output manageable
            lines = process.stdout.strip().split("\n")
            if len(lines) > 30:
                print(f"  ... ({len(lines) - 30} lines hidden)")
            for line in lines[-30:]:
                print(f"  {line}")

        if process.returncode == 0:
            result["status"] = "PASSED"
            print(f"\n  ✅ PASSED ({duration:.1f}s)")
        else:
            result["status"] = "FAILED"
            result["error"] = process.stderr[-500:] if process.stderr else "Unknown error"
            print(f"\n  ❌ FAILED ({duration:.1f}s)")
            if process.stderr:
                print(f"  Error: {process.stderr[-200:]}")

    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = "Script took more than 120 seconds"
        print(f"\n  ⏰ TIMEOUT (>120s)")

    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
        print(f"\n  ❌ ERROR: {e}")

    # Check if expected output file was created
    if expected:
        exists = Path(expected).exists()
        result["output_file_exists"] = exists
        if exists:
            size = Path(expected).stat().st_size
            result["output_file_size_bytes"] = size
            print(f"  Output: {expected} ({size:,} bytes)")
        else:
            print(f"  Output: {expected} NOT FOUND")

    return result


def check_charts():
    """Check which chart PNG files exist."""
    expected_charts = [
        "chart_complementarity_heatmap.png",
        "chart_sir_hardest_topic.png",
        "chart_sir_easiest_topic.png",
        "chart_sir_hardest_comparison.png",
        "chart_sir_easiest_comparison.png",
        "chart_sir_beta_sensitivity.png",
        "chart_topic_dependencies.png",
        "chart_prediction_accuracy.png",
    ]

    results = []
    for chart in expected_charts:
        exists = Path(chart).exists()
        size = Path(chart).stat().st_size if exists else 0
        results.append({
            "file": chart,
            "exists": exists,
            "size_bytes": size
        })

    return results


def check_prerequisites():
    """Verify that required files exist before running tests."""
    print("Checking prerequisites...")
    issues = []

    if not Path("topics.json").exists():
        issues.append("topics.json not found")

    if not Path(".env").exists():
        issues.append(".env file not found — create it with Neo4j credentials")

    # Check Python packages
    required = ["neo4j", "pandas", "numpy", "matplotlib", "scipy", "sklearn", "flask"]
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            issues.append(f"Python package '{pkg}' not installed")

    if issues:
        print("\n⚠️  PREREQUISITE ISSUES:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nFix these before running the tests.")
        return False

    print("  All prerequisites met ✅\n")
    return True


# -------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------
def main():
    print("\n" + "=" * 60)
    print("BECE SLN — AUTOMATED SYSTEM TEST")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")

    if not check_prerequisites():
        return

    # Run core modules
    print("\n" + "#" * 60)
    print("CORE MODULES (must all pass)")
    print("#" * 60)

    core_results = []
    for module in MODULES:
        result = run_module(module)
        core_results.append(result)

    # Run optional modules
    print("\n" + "#" * 60)
    print("OPTIONAL MODULES (ok if they fail — teammates may not be done)")
    print("#" * 60)

    optional_results = []
    for module in OPTIONAL_MODULES:
        result = run_module(module)
        optional_results.append(result)

    # Check charts
    print("\n" + "#" * 60)
    print("CHART FILES CHECK")
    print("#" * 60)
    chart_results = check_charts()
    charts_found = sum(1 for c in chart_results if c["exists"])
    print(f"\n  Charts found: {charts_found}/{len(chart_results)}")
    for c in chart_results:
        status = "✅" if c["exists"] else "❌"
        print(f"  {status} {c['file']}")

    # Summary
    core_passed = sum(1 for r in core_results if r["status"] == "PASSED")
    core_total = len(core_results)
    optional_passed = sum(1 for r in optional_results if r["status"] == "PASSED")
    optional_total = len(optional_results)
    total_time = sum(r["duration_seconds"] for r in core_results + optional_results)

    print("\n" + "=" * 60)
    print("SYSTEM TEST SUMMARY")
    print("=" * 60)
    print(f"  Core modules:     {core_passed}/{core_total} passed")
    print(f"  Optional modules: {optional_passed}/{optional_total} passed")
    print(f"  Chart files:      {charts_found}/{len(chart_results)} found")
    print(f"  Total test time:  {total_time:.1f} seconds")

    if core_passed == core_total:
        print("\n  🎉 ALL CORE MODULES PASSED — system is working correctly!")
    else:
        failed = [r["module"] for r in core_results if r["status"] != "PASSED"]
        print(f"\n  ⚠️  FAILED MODULES: {', '.join(failed)}")
        print("  Send the error messages to Chisom for debugging.")

    # Save report
    report = {
        "test_date": datetime.now().isoformat(),
        "python_version": sys.version,
        "core_modules": core_results,
        "optional_modules": optional_results,
        "chart_files": chart_results,
        "summary": {
            "core_passed": core_passed,
            "core_total": core_total,
            "optional_passed": optional_passed,
            "optional_total": optional_total,
            "charts_found": charts_found,
            "charts_total": len(chart_results),
            "total_time_seconds": round(total_time, 2),
            "overall_status": "PASS" if core_passed == core_total else "FAIL"
        }
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Test report saved to {REPORT_FILE}")

    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("1. Take screenshots of every dashboard page (see SEMILORE_BRIEF.md)")
    print("2. Take screenshots of Neo4j queries (see SEMILORE_BRIEF.md)")
    print("3. Commit your test report:")
    print("     git pull --rebase")
    print("     git add system_test.py system_test_report.json")
    print('     git commit -m "System test complete"')
    print("     git push")
    print("4. Send all screenshots to the WhatsApp group\n")


if __name__ == "__main__":
    main()

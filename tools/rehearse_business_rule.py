"""Run a reversible red/green #210 rehearsal in an exported temporary checkout."""

import argparse
import hashlib
import io
import json
import os
import platform
import subprocess
import sys
import tarfile
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

NODE = "tests/test_student_evaluations.py::test_student_evaluations_due_soon_24_hour_boundary"
ORIGINAL = "deadline < comparison_now + timedelta(hours=24)"
MUTATION = "deadline <= comparison_now + timedelta(hours=24)"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run_stage(root, label):
    report = root / f"{label}.xml"
    command = [sys.executable, "-m", "pytest", "-q", NODE, f"--junitxml={report}"]
    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    environment["EDUSURVEY_ENV"] = "development"
    environment["EDUSURVEY_DATABASE"] = str(root / "unused.db")
    started = time.perf_counter()
    result = subprocess.run(command, check=False, cwd=root, env=environment, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=120)
    tree = ET.parse(report).getroot()
    cases = list(tree.iter("testcase"))
    failed = [case.attrib["name"] for case in cases if case.find("failure") is not None]
    errors = sum(case.find("error") is not None for case in cases)
    skips = sum(case.find("skipped") is not None for case in cases)
    output = result.stdout + result.stderr
    for private, placeholder in ((str(root), "<temporary-checkout>"), (str(Path.home()), "<home>")):
        output = output.replace(private, placeholder).replace(private.replace("\\", "/"), placeholder)
    return {"stage": label, "command": f"python -m pytest -q {NODE} --junitxml=<temporary-report>",
            "exit_code": result.returncode, "tests": len(cases), "failed_nodes": failed,
            "passed": len(cases) - len(failed) - errors - skips, "errors": errors, "skipped": skips,
            "elapsed_seconds": round(time.perf_counter() - started, 3), "output": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--output", type=Path, default=Path("docs/evidence/210/mutation.json"))
    args = parser.parse_args()
    revision = subprocess.check_output(["git", "rev-parse", "--verify", args.revision + "^{commit}"], text=True).strip()
    workspace_source = Path("src/app.py")
    workspace_hash = digest(workspace_source.read_bytes())
    with TemporaryDirectory(prefix="m4-rehearsal-210-") as directory:
        root = Path(directory)
        archive = subprocess.check_output(["git", "archive", revision, "src", "tests"])
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            tar.extractall(root, filter="data")
        source = root / "src/app.py"
        original = source.read_bytes()
        assert original.count(ORIGINAL.encode()) == 1, "Mutation location must be unique."
        baseline = run_stage(root, "baseline")
        assert baseline["exit_code"] == 0 and baseline["passed"] == 3
        try:
            mutated = original.replace(ORIGINAL.encode(), MUTATION.encode(), 1)
            source.write_bytes(mutated)
            red = run_stage(root, "mutated")
        finally:
            source.write_bytes(original)
        restored = run_stage(root, "restored")
        assert red["exit_code"] == 1 and red["passed"] == 2 and len(red["failed_nodes"]) == 1
        assert "TC-09-at" in red["failed_nodes"][0]
        assert restored["exit_code"] == 0 and restored["passed"] == 3
        assert all(stage["errors"] == stage["skipped"] == 0 for stage in (baseline, red, restored))
        assert source.read_bytes() == original
        restored_hash = digest(source.read_bytes())
    assert digest(workspace_source.read_bytes()) == workspace_hash
    evidence = {"captured_at": datetime.now(UTC).isoformat(), "revision": revision,
                "environment": {"platform": platform.system(), "python": platform.python_version()},
                "scope": "Local temporary-copy mutation, not a deployment or a production defect fix",
                "source": "src/app.py", "original_expression": ORIGINAL, "mutated_expression": MUTATION,
                "original_sha256": digest(original), "mutated_sha256": digest(mutated),
                "restored_sha256": restored_hash, "workspace_source_unchanged": True,
                "stages": [baseline, red, restored]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"revision": revision, "baseline_passed": baseline["passed"], "mutated_failed": red["failed_nodes"],
                      "restored_passed": restored["passed"], "workspace_source_unchanged": True, "output": str(args.output)}))


if __name__ == "__main__":
    main()

"""Fail closed unless every required CI job passed; no provider credentials needed."""

import os


def require_successful_checks(results):
    for name in ("DETECT_RESULT", "PYTHON_RESULT", "SECURITY_RESULT"):
        if results.get(name) != "success":
            raise RuntimeError(f"Required CI job did not succeed: {name}")
    detected = results.get("NODE_DETECTED")
    if detected not in ("true", "false"):
        raise RuntimeError("Node stack detection result is missing or invalid")
    expected = "success" if detected == "true" else "skipped"
    if results.get("NODE_RESULT") != expected:
        raise RuntimeError("Node job result does not match the detected stack")


if __name__ == "__main__":
    require_successful_checks(os.environ)
    print("Required test, lint and security jobs succeeded; CI gate is green.")

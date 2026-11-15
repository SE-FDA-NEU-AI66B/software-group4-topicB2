"""Compute sanitized rolling-window request metrics from exported app log lines.

Exit 2 means a configured investigation threshold was crossed, not an alert sent.
"""

import argparse
import json
import math
import re
import sys
from datetime import UTC, datetime, timedelta


def summarize(lines, now, window_seconds=300):
    if now.tzinfo is None or window_seconds <= 0:
        raise ValueError("An aware timestamp and positive window are required.")
    start = now - timedelta(seconds=window_seconds)
    durations, statuses, seen = [], [], set()
    health_failures = invalid = duplicates = 0
    for line in lines:
        try:
            # Flask/platform exporters may prepend a log timestamp and level.
            record = json.loads(line[line.index("{"):])
        except (ValueError, TypeError):
            continue
        if not isinstance(record, dict) or record.get("event") != "request_completed":
            continue
        try:
            timestamp = datetime.fromisoformat(record["timestamp"])
            duration, status = record["duration_ms"], record["status"]
            if (timestamp.tzinfo is None or isinstance(duration, bool)
                    or not isinstance(duration, (int, float)) or not math.isfinite(duration)
                    or duration < 0 or type(status) is not int or not 100 <= status <= 599
                    or not re.fullmatch(r"[0-9a-f]{32}", record["request_id"])):
                raise ValueError("Invalid request metric")
        except (KeyError, TypeError, ValueError):
            invalid += 1
            continue
        if not start < timestamp <= now:
            continue
        if record["request_id"] in seen:
            duplicates += 1
            continue
        seen.add(record["request_id"])
        if record.get("endpoint") == "health":
            health_failures += int(status >= 500)
            continue
        if record.get("endpoint") == "static":
            continue
        durations.append(duration)
        statuses.append(status)
    total = len(statuses)
    errors = sum(status >= 500 for status in statuses)
    rate = errors / total * 100 if total else None
    p95 = sorted(durations)[math.ceil(0.95 * total) - 1] if total else None
    return {
        "window_start_exclusive": start.isoformat(), "window_end_inclusive": now.isoformat(),
        "requests": total, "server_errors": errors, "error_rate_percent": rate,
        "p95_server_ms": p95, "health_failures": health_failures,
        "invalid_events": invalid, "duplicate_events": duplicates,
        "low_sample": total < 20,
        "error_rate_breach": total >= 20 and rate >= 5,
        "latency_breach": total >= 20 and p95 > 1000,
        "health_breach": health_failures > 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--now", help="ISO-8601 timestamp with offset; defaults to current UTC")
    parser.add_argument("--window-seconds", type=int, default=300)
    args = parser.parse_args()
    try:
        now = datetime.fromisoformat(args.now) if args.now else datetime.now(UTC)
        result = summarize(sys.stdin, now, args.window_seconds)
    except ValueError:
        parser.error("Use an offset-aware --now and a positive window.")
    print(json.dumps(result, sort_keys=True))
    return 2 if any(result[key] for key in ("error_rate_breach", "latency_breach", "health_breach")) else 0


if __name__ == "__main__":
    raise SystemExit(main())

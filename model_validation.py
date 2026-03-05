#!/usr/bin/env python3
"""Validate trained model metrics against thresholds for CI/CD quality gates."""

import argparse
import json
import sys
from pathlib import Path


def validate_metrics(metrics_file: Path, min_accuracy: float, min_f1: float, report_file: Path) -> bool:
    if not metrics_file.exists():
        print(f"ERROR: metrics file not found: {metrics_file}")
        return False

    metrics = json.loads(metrics_file.read_text())
    accuracy = float(metrics.get("accuracy", 0.0))
    f1_score = float(metrics.get("f1_score", 0.0))

    checks = [
        {
            "metric": "accuracy",
            "value": accuracy,
            "threshold": min_accuracy,
            "passed": accuracy >= min_accuracy,
        },
        {
            "metric": "f1_score",
            "value": f1_score,
            "threshold": min_f1,
            "passed": f1_score >= min_f1,
        },
    ]

    overall_passed = all(c["passed"] for c in checks)

    report = {
        "overall_passed": overall_passed,
        "metrics_file": str(metrics_file),
        "checks": checks,
    }
    report_file.parent.mkdir(parents=True, exist_ok=True)
    report_file.write_text(json.dumps(report, indent=2))

    print("=== Model Validation Report ===")
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        print(
            f"{status}: {c['metric']} = {c['value']:.4f} "
            f"(threshold: {c['threshold']:.4f})"
        )

    print(f"Overall: {'PASSED' if overall_passed else 'FAILED'}")
    print(f"Report written to {report_file}")
    return overall_passed


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate model metrics against thresholds")
    parser.add_argument("--metrics-file", default="metrics.json")
    parser.add_argument("--report-file", default="validation_report.json")
    parser.add_argument("--min-accuracy", type=float, default=0.90)
    parser.add_argument("--min-f1", type=float, default=0.85)
    args = parser.parse_args()

    passed = validate_metrics(
        metrics_file=Path(args.metrics_file),
        min_accuracy=args.min_accuracy,
        min_f1=args.min_f1,
        report_file=Path(args.report_file),
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

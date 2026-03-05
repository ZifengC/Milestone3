#!/usr/bin/env python3
"""Register a trained MLflow run artifact into the Model Registry."""

import argparse
import json
from pathlib import Path

import mlflow
from mlflow.tracking import MlflowClient


def register_from_metrics(
    metrics_file: Path, tracking_uri: str, model_name: str, artifact_path: str
) -> dict:
    if not metrics_file.exists():
        raise FileNotFoundError(f"metrics file not found: {metrics_file}")

    metrics = json.loads(metrics_file.read_text())
    run_id = metrics.get("run_id")
    if not run_id:
        raise ValueError("metrics.json does not contain run_id")

    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"runs:/{run_id}/{artifact_path}"
    result = mlflow.register_model(model_uri=model_uri, name=model_name)

    client = MlflowClient()
    version = client.get_model_version(name=model_name, version=result.version)
    payload = {
        "model_name": model_name,
        "model_version": version.version,
        "run_id": run_id,
        "status": version.status,
    }
    print(json.dumps(payload, indent=2))
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Register model from MLflow run artifacts.")
    parser.add_argument("--metrics-file", default="metrics.json")
    parser.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    parser.add_argument("--model-name", default="iris-classifier")
    parser.add_argument("--artifact-path", default="model")
    args = parser.parse_args()

    register_from_metrics(
        metrics_file=Path(args.metrics_file),
        tracking_uri=args.tracking_uri,
        model_name=args.model_name,
        artifact_path=args.artifact_path,
    )


if __name__ == "__main__":
    main()

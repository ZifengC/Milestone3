#!/usr/bin/env python3
"""Train a RandomForest model on Iris, log to MLflow, and export metrics."""

import argparse
import json
import time
from pathlib import Path

import mlflow
import mlflow.sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split


def train_model(
    metrics_file: Path,
    tracking_uri: str,
    experiment_name: str,
    n_estimators: int,
    max_depth: int,
    random_state: int,
) -> dict:
    metrics_file.parent.mkdir(parents=True, exist_ok=True)

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(experiment_name)

    iris = load_iris()
    X_train, X_test, y_train, y_test = train_test_split(
        iris.data, iris.target, test_size=0.2, random_state=random_state
    )

    params = {
        "n_estimators": n_estimators,
        "max_depth": max_depth,
        "random_state": random_state,
    }

    with mlflow.start_run() as run:
        start = time.time()
        model = RandomForestClassifier(**params)
        model.fit(X_train, y_train)
        training_time = time.time() - start

        preds = model.predict(X_test)
        accuracy = accuracy_score(y_test, preds)
        f1 = f1_score(y_test, preds, average="weighted")

        mlflow.log_params(params)
        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("f1_score", f1)
        mlflow.log_metric("training_time_seconds", training_time)
        mlflow.sklearn.log_model(model, artifact_path="model")

        result = {
            "run_id": run.info.run_id,
            "accuracy": round(accuracy, 4),
            "f1_score": round(f1, 4),
            "training_time_seconds": round(training_time, 4),
            "tracking_uri": tracking_uri,
            "experiment_name": experiment_name,
            **params,
        }

    metrics_file.write_text(json.dumps(result, indent=2))
    print(f"Metrics written to {metrics_file}")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Train model and log metrics.")
    parser.add_argument("--metrics-file", default="metrics.json")
    parser.add_argument("--tracking-uri", default="sqlite:///mlflow.db")
    parser.add_argument("--experiment-name", default="milestone3-training")
    parser.add_argument("--n-estimators", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=5)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    train_model(
        metrics_file=Path(args.metrics_file),
        tracking_uri=args.tracking_uri,
        experiment_name=args.experiment_name,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        random_state=args.random_state,
    )


if __name__ == "__main__":
    main()

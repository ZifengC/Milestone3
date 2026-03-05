#!/usr/bin/env python3
"""Airflow DAG: train, validate, then register in MLflow Model Registry."""

import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator

PROJECT_DIR = Path(os.getenv("MILESTONE3_DIR", Path(__file__).resolve().parents[1]))
METRICS_FILE = PROJECT_DIR / "metrics.json"
REPORT_FILE = PROJECT_DIR / "validation_report.json"
TRACKING_URI = f"sqlite:///{PROJECT_DIR / 'mlflow.db'}"
REGISTERED_MODEL_NAME = "iris-classifier"
FAILURE_LOG = PROJECT_DIR / "failure_events.log"


def on_task_failure(context: dict) -> None:
    """Record failure context and clean stale outputs after train failures."""
    dag = context.get("dag")
    task = context.get("task_instance")
    dag_run = context.get("dag_run")
    exception = context.get("exception")

    payload = {
        "timestamp_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "dag_id": dag.dag_id if dag else None,
        "task_id": task.task_id if task else None,
        "run_id": dag_run.run_id if dag_run else None,
        "exception": str(exception) if exception else None,
    }

    FAILURE_LOG.parent.mkdir(parents=True, exist_ok=True)
    with FAILURE_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")

    # If training fails, remove stale artifacts to avoid confusing later steps.
    if task and task.task_id == "train_model":
        for path in (METRICS_FILE, REPORT_FILE):
            if path.exists():
                path.unlink()


DEFAULT_ARGS = {
    "owner": "mlops",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "on_failure_callback": on_task_failure,
}


def _conf_value(conf: dict, key: str, default, cast):
    """Read a value from dag_run.conf with best-effort casting."""
    value = conf.get(key, default)
    try:
        return cast(value)
    except (TypeError, ValueError):
        return default


def _dag_conf(context: dict) -> dict:
    dag_run = context.get("dag_run")
    return dag_run.conf or {} if dag_run else {}


def run_train(**context) -> None:
    conf = _dag_conf(context)
    n_estimators = _conf_value(conf, "n_estimators", 100, int)
    max_depth = _conf_value(conf, "max_depth", 5, int)
    random_state = _conf_value(conf, "random_state", 42, int)
    experiment_name = _conf_value(conf, "experiment_name", "milestone3-airflow", str)

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_DIR / "train.py"),
            "--metrics-file",
            str(METRICS_FILE),
            "--tracking-uri",
            TRACKING_URI,
            "--experiment-name",
            experiment_name,
            "--n-estimators",
            str(n_estimators),
            "--max-depth",
            str(max_depth),
            "--random-state",
            str(random_state),
        ],
        check=True,
        cwd=PROJECT_DIR,
    )


def run_validation(**context) -> None:
    conf = _dag_conf(context)
    min_accuracy = _conf_value(conf, "min_accuracy", 0.90, float)
    min_f1 = _conf_value(conf, "min_f1", 0.85, float)

    subprocess.run(
        [
            sys.executable,
            str(PROJECT_DIR / "model_validation.py"),
            "--metrics-file",
            str(METRICS_FILE),
            "--report-file",
            str(REPORT_FILE),
            "--min-accuracy",
            str(min_accuracy),
            "--min-f1",
            str(min_f1),
        ],
        check=True,
        cwd=PROJECT_DIR,
    )


def run_register() -> None:
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_DIR / "register_model.py"),
            "--metrics-file",
            str(METRICS_FILE),
            "--tracking-uri",
            TRACKING_URI,
            "--model-name",
            REGISTERED_MODEL_NAME,
            "--artifact-path",
            "model",
        ],
        check=True,
        cwd=PROJECT_DIR,
    )


with DAG(
    dag_id="milestone3_train_pipeline",
    default_args=DEFAULT_ARGS,
    description="Milestone3 training + validation + registry pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["milestone3", "ml", "validation", "registry"],
) as dag:
    train_task = PythonOperator(task_id="train_model", python_callable=run_train)
    validate_task = PythonOperator(task_id="validate_model", python_callable=run_validation)
    register_task = PythonOperator(task_id="register_model", python_callable=run_register)

    train_task >> validate_task >> register_task

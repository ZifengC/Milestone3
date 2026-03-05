# Milestone 3: Unified MLOps Pipeline

This folder merges Airflow orchestration, CI/CD quality gates, and MLflow tracking using the current Iris + RandomForest model.

## Structure

```
milestone3/
├── .github/
│   └── workflows/
│       └── train_and_validate.yml
├── dags/
│   └── train_pipeline.py
├── mlruns/
├── model_validation.py
├── register_model.py
├── train.py
├── requirements.txt
└── README.md
```

## What each file does

- `train.py`: Trains the RandomForest model, logs run/model/metrics to MLflow, writes `metrics.json`.
- `model_validation.py`: Applies threshold checks (`accuracy`, `f1_score`) and exits non-zero on failure.
- `register_model.py`: Registers the trained run artifact to MLflow Model Registry.
- `dags/train_pipeline.py`: Airflow DAG that runs `train.py` -> `model_validation.py` -> `register_model.py`.
- `.github/workflows/train_and_validate.yml`: CI workflow for train + validate + register + artifact upload.

## Local quick start

```bash
cd milestone3
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

python train.py --metrics-file metrics.json --tracking-uri sqlite:///mlflow.db
python model_validation.py --metrics-file metrics.json --min-accuracy 0.90 --min-f1 0.85
python register_model.py --metrics-file metrics.json --tracking-uri sqlite:///mlflow.db --model-name iris-classifier
```

If you upgraded MLflow from an older setup and hit migration errors, recreate the tracking DB:

```bash
mv mlflow.db mlflow.db.bak
```

## Airflow usage

If you run Airflow from Docker, make sure `milestone3` is mounted and set:

```bash
export MILESTONE3_DIR=/path/to/milestone3
```

Then trigger DAG `milestone3_train_pipeline`.

To tune parameters from Airflow UI only:

1. Open Airflow UI -> `DAGs` -> `milestone3_train_pipeline` -> `Trigger DAG`.
2. Paste JSON config in `Run configuration`.
3. Trigger run.

Example config:

```json
{
  "n_estimators": 200,
  "max_depth": 8,
  "random_state": 123,
  "min_accuracy": 0.93,
  "min_f1": 0.90,
  "experiment_name": "milestone3-airflow-ui"
}
```

Supported keys in `dag_run.conf`:

- `n_estimators` (int, default `100`)
- `max_depth` (int, default `5`)
- `random_state` (int, default `42`)
- `min_accuracy` (float, default `0.90`)
- `min_f1` (float, default `0.85`)
- `experiment_name` (string, default `milestone3-airflow`)

## Notes

- This workflow uses threshold-based gating: validation failure returns exit code `1`, so registration does not run.
- MLflow artifacts and tracking files are generated under this folder (`mlflow.db`, `mlruns/`).
- GitHub only auto-detects workflow files in repository root `.github/workflows/`; this file is placed under `milestone3/.github/` to match the requested structure.


### 

In airflow-local

docker compose up airflow-init

docker compose up -d

In milestone3
git init
git branch -M main

git add .
git commit -m "Initial commit: milestone3 mlops pipeline"

git remote add origin https://github.com/ZifengC/Milestone3.git
git push -u origin main


mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5001

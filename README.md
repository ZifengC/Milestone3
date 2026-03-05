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

## Notes

- This workflow uses threshold-based gating: validation failure returns exit code `1`, so registration does not run.
- MLflow artifacts and tracking files are generated under this folder (`mlflow.db`, `mlruns/`).
- GitHub only auto-detects workflow files in repository root `.github/workflows/`; this file is placed under `milestone3/.github/` to match the requested structure.


### 
git init
git branch -M main

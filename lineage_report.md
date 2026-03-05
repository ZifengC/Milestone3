# Model Lineage Report

## Scope

This report documents model lineage for `milestone3_train_pipeline` and compares production candidates using:

- Parameters (including examples like learning rate / batch size where applicable)
- Metrics (accuracy, F1, AUC where available)
- Artifact hashes for reproducibility

Data sources used:

- Airflow train/validate logs under `airflow-local/logs/`
- MLflow model artifacts under `milestone3/mlruns/<experiment_id>/models/`

## Run Comparison Table

| Run ID | Run Time (UTC) | Model Type | Parameters (core) | Learning Rate | Batch Size | Accuracy | F1 (weighted) | AUC | Validation Gate | Model Artifact SHA256 (`model.pkl`) | Notes |
|---|---|---|---|---|---|---:|---:|---|---|---|---|
| `d0872f94b3764bfba5820b79d56b1e70` | 2026-03-05 21:15:37 | RandomForestClassifier | `n_estimators=500`, `max_depth=5`, `random_state=123` | N/A | N/A | 0.9333 | 0.9348 | N/A | N/A (no validation record found) | `d6d1ee6c59edba6cb992f97765aa02e102f0d3984f0d4331a03d627bb88a1c08` | Highest tree count; longest training time (`0.2883s`) |
| `d2300b68bc304ac0ace195dbcbf2a7f2` | 2026-03-05 21:13:08 | RandomForestClassifier | `n_estimators=100`, `max_depth=15`, `random_state=123` | N/A | N/A | 0.9333 | 0.9348 | N/A | N/A (no validation record found) | `c18f9a23a6068a263d7550ea7440f4fef7925338a3a86ace2cc082c9acb31dde` | Deeper trees with moderate training time (`0.0669s`) |
| `fec9f5abaf2844c393be8f35d19e43a5` | 2026-03-05 20:47:15 | RandomForestClassifier | `n_estimators=200`, `max_depth=8`, `random_state=123` | N/A | N/A | 0.9333 | 0.9348 | N/A | PASS (`min_accuracy=0.93`, `min_f1=0.90`) | `ce19c4c961bda6023dac881d498400ac3bb7c803df9b1a1ba58a382832cab17b` | Airflow-gated run |
| `5734bb2b91964492820458c63cad8530` | 2026-03-05 20:34:52 | RandomForestClassifier | `n_estimators=100`, `max_depth=5`, `random_state=42` | N/A | N/A | 1.0000 | 1.0000 | N/A | PASS (`min_accuracy=0.90`, `min_f1=0.85`) | `f821ae9e82058d71cb3ae7b0c3949503077f7383062ae0bd94a8bd207c249d27` | Best quality among latest 5 runs |
| `59f190f4793d4cae8e68efbe5538da98` | 2026-03-05 20:22:53 | RandomForestClassifier | `n_estimators=100`, `max_depth=5`, `random_state=42` | N/A | N/A | 1.0000 | 1.0000 | N/A | PASS (`min_accuracy=0.90`, `min_f1=0.85`) | `f821ae9e82058d71cb3ae7b0c3949503077f7383062ae0bd94a8bd207c249d27` | Same metrics/hash as run `5734...` |

## Run Comparisons and Analysis

- Across the latest 5 runs, two performance tiers appear: `{5734..., 59f...}` at `accuracy/F1 = 1.0`, and `{fec9..., d230..., d087...}` at `0.9333/0.9348`.
- Three of five runs have explicit Airflow validation PASS records; the two newest runs currently have no validation log evidence in the local Airflow logs.
- Artifact hashes differ across run configurations, and identical hashes for `5734...` and `59f...` indicate reproducible binary output under the same parameters.
- AUC is not currently logged in `train.py`; comparison is limited to accuracy/F1/training time.
- Fields such as learning rate and batch size are not applicable to RandomForest in this implementation, so they are marked as `N/A` for explicitness.

## Justification for Production Candidate Selection

Selected production candidate: **Run `5734bb2b91964492820458c63cad8530`**

Justification:

- Best observed quality in the latest 5 records: accuracy/F1 both `1.0000`.
- Same quality and artifact hash as run `59f...`, but with later execution timestamp (more recent equivalent candidate).
- Verified validation PASS in workflow logs with defined thresholds.
- Fully traceable lineage:
  - Airflow run/task logs
  - Recorded run ID
  - Deterministic artifact hash (`SHA256`)
  - Registry linkage from run artifact (`runs:/<run_id>/model`)

## Identified Risks and Monitoring Needs

Identified risks:

- Small benchmark dataset (Iris) can overstate performance and may not represent production data distribution.
- Metric set is incomplete for robust governance (no AUC, precision/recall breakdown, calibration metrics).
- RandomForest pickle artifacts have deserialization security considerations (as noted by MLflow warning).
- Dataset/input schema lineage is not explicitly versioned in this repo yet.

Monitoring needs:

1. Add online/offline drift monitoring:
   - Feature distribution drift (e.g., PSI/KL or KS tests)
   - Target drift where labels are available
2. Expand model quality monitoring:
   - Track precision/recall (per class), AUC, and calibration over time
3. Strengthen reproducibility controls:
   - Persist dataset snapshot/version ID per run
   - Store training code commit SHA in run tags
4. Add operational monitors:
   - Inference latency and failure rate SLAs
   - Alert on threshold breaches and automated rollback policy

## Reproducibility Notes

- To verify artifact immutability, recompute hash:

```bash
shasum -a 256 milestone3/mlruns/<experiment_id>/models/<model_id>/artifacts/model.pkl
```

- A run should be promoted only when:
  - Validation report is PASS
  - Run ID and artifact hash are recorded in release documentation
  - Monitoring plan for that run is configured

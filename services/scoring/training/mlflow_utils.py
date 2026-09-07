"""
Tiny MLflow helper shared by every training / evaluation script.

All runs go to a local SQLite store at <project>/mlflow.db (artifacts in <project>/mlruns).
Open the UI with:   mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
"""
import contextlib
import numbers
import os
import pathlib

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
TRACKING_URI = f"sqlite:///{ROOT / 'mlflow.db'}"
ARTIFACT_ROOT = (ROOT / "mlruns").as_uri()


def setup(experiment: str):
    mlflow.set_tracking_uri(TRACKING_URI)
    if mlflow.get_experiment_by_name(experiment) is None:
        mlflow.create_experiment(experiment, artifact_location=ARTIFACT_ROOT)
    mlflow.set_experiment(experiment)


@contextlib.contextmanager
def mlflow_run(experiment, run_name, params=None, tags=None, enabled=True):
    """Context manager: yields the active run (or None when disabled)."""
    if not enabled:
        yield None
        return
    setup(experiment)
    with mlflow.start_run(run_name=run_name) as run:
        if tags:
            mlflow.set_tags(tags)
        if params:
            mlflow.log_params({k: str(v)[:500] for k, v in params.items()})
        yield run


def log_metrics(metrics, step=None, prefix="", enabled=True):
    if not enabled or not mlflow.active_run():
        return
    clean = {}
    for k, v in metrics.items():
        if isinstance(v, bool) or not isinstance(v, numbers.Number):
            continue
        clean[f"{prefix}{k}"] = float(v)
    if clean:
        mlflow.log_metrics(clean, step=step)


def log_dict(obj, filename, enabled=True):
    if enabled and mlflow.active_run():
        mlflow.log_dict(obj, filename)


def log_artifact(path, enabled=True):
    if enabled and mlflow.active_run() and os.path.exists(path):
        mlflow.log_artifact(path)

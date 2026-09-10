"""
MLflow helper shared by every training / evaluation script (ONE tracking system for the service).

Store   : SQLite at services/scoring/mlflow.db  (git-ignored) ; artifacts under services/scoring/mlruns/
UI      : cd services/scoring && mlflow ui --backend-store-uri sqlite:///mlflow.db --port 5000
Override: MLFLOW_TRACKING_URI=<uri> (e.g. a shared server) takes precedence over the local SQLite file.

Every run started through mlflow_run() automatically carries:
  tags   git_commit, git_branch, git_dirty, service=scoring, host, python
  params artifact_path (where the trained weights were written), plus whatever the caller passes
Callers log dataset/version, seed, lr, batch, epochs, max_length in `params`, training time and
val/test metrics through log_metrics(), and the full metrics.json through log_dict().
"""
import contextlib
import numbers
import os
import pathlib
import platform
import subprocess
import time

os.environ.setdefault("MLFLOW_DISABLE_AGENT_HINT", "1")

import mlflow  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]                     # services/scoring
TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI") or f"sqlite:///{ROOT / 'mlflow.db'}"
ARTIFACT_ROOT = (ROOT / "mlruns").as_uri()


def _git(*args):
    try:
        return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=5,
                              check=True).stdout.strip()
    except Exception:
        return None


def git_info():
    sha = _git("rev-parse", "HEAD")
    return {"git_commit": sha or "unknown", "git_commit_short": (sha or "unknown")[:12],
            "git_branch": _git("rev-parse", "--abbrev-ref", "HEAD") or "unknown",
            "git_dirty": str(bool(_git("status", "--porcelain")))}


def standard_tags():
    return {**git_info(), "service": "scoring", "host": platform.node(), "python": platform.python_version()}


def setup(experiment: str):
    mlflow.set_tracking_uri(TRACKING_URI)
    if mlflow.get_experiment_by_name(experiment) is None:
        kwargs = {"artifact_location": ARTIFACT_ROOT} if TRACKING_URI.startswith("sqlite") else {}
        mlflow.create_experiment(experiment, **kwargs)
    mlflow.set_experiment(experiment)


@contextlib.contextmanager
def mlflow_run(experiment, run_name, params=None, tags=None, enabled=True, artifact_path=None):
    """Context manager: yields the active run (or None when disabled). Records wall time as run_seconds."""
    if not enabled:
        yield None
        return
    setup(experiment)
    t0 = time.time()
    with mlflow.start_run(run_name=run_name) as run:
        mlflow.set_tags({**standard_tags(), **(tags or {})})
        merged = dict(params or {})
        if artifact_path is not None:
            merged["artifact_path"] = str(artifact_path)
        if merged:
            mlflow.log_params({k: str(v)[:500] for k, v in merged.items()})
        try:
            yield run
        finally:
            mlflow.log_metric("run_seconds", time.time() - t0)


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

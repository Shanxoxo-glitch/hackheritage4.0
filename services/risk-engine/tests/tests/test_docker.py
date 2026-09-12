"""tests/test_docker.py -- end-to-end verification of the Dockerfile +
requirements changes. Builds the image once, runs it, and proves:

  image-level : non-root user, fixed UID, nologin, EXPOSE 8200, healthcheck
                config (127.0.0.1, start-period, cadence), env flags, CMD
                (one worker, --no-access-log), labels
  runtime     : becomes HEALTHY, /healthz contract, model version matches
                the startup log, X-Request-ID header, fusion conflict /
                threat-force / stale behavior, forecast contract + interval
                ordering + 422 validation, explain LOO structure, /metrics
                contract, precompiled bytecode, exactly one worker,
                graceful shutdown, read-only rootfs compatibility
  gate (opt-in): corrupt artifact -> BUILD FAILS (RUN_NEGATIVE=1)

Run:      pytest tests/test_docker.py -v
Slow opt: RUN_NEGATIVE=1 pytest tests/test_docker.py -v   (adds the
          negative gate test; does a second build)
Debug:    KEEP_IMAGE=1 pytest tests/test_docker.py -v     (don't rmi after)

Requires: docker daemon running, repo root one level up, artifacts/ present
in the build context (a .gitkeep is enough -- heuristic fallback is tested
as a valid mode), and .dockerignore must NOT exclude `artifacts` (that line
belongs to the multi-stage variant only).
"""
import json
import os
import re
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
IMAGE = os.getenv("RISK_TEST_IMAGE", "risk-engine-citest")
NAME = f"risk-citest-{os.getpid()}"


# ----------------------------------------------------------------- helpers --
def _sh(*args, timeout=900):
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _get(url, path, timeout=10):
    with urllib.request.urlopen(url + path, timeout=timeout) as r:
        return r.status, dict(r.headers), r.read()


def _post_json(url, path, payload, timeout=10):
    req = urllib.request.Request(
        url + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), json.loads(r.read())
    except urllib.error.HTTPError as e:            # 4xx/5xx are test data
        raw = e.read()
        try:
            raw = json.loads(raw)
        except Exception:
            raw = raw.decode(errors="replace")
        return e.code, dict(e.headers), raw


def _wait_http(url, path="/healthz", timeout_s=60):
    deadline, last = time.time() + timeout_s, None
    while time.time() < deadline:
        try:
            status, _, body = _get(url, path, timeout=3)
            if status == 200:
                return json.loads(body)
        except Exception as e:
            last = e
        time.sleep(1)
    pytest.fail(f"{path} never returned 200 within {timeout_s}s (last: {last})")


def _logs(name=NAME) -> str:
    return _sh("docker", "logs", name, timeout=60).stdout


def _exec(name, *cmd, timeout=30):
    return _sh("docker", "exec", name, *cmd, timeout=timeout)


# ---------------------------------------------------------------- fixtures --
@pytest.fixture(scope="session")
def image():
    if _sh("docker", "version", "--format", "{{.Server.Version}}", timeout=30).returncode != 0:
        pytest.skip("docker daemon not available")
    build = _sh("docker", "build", "-t", IMAGE, str(ROOT))
    assert build.returncode == 0, (build.stdout + build.stderr)[-4000:]
    yield IMAGE
    if os.getenv("KEEP_IMAGE") != "1":
        _sh("docker", "rmi", "-f", IMAGE, timeout=120)


@pytest.fixture(scope="session")
def img_cfg(image):
    r = _sh("docker", "image", "inspect", IMAGE)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)[0]


@pytest.fixture(scope="session")
def base_url(image):
    _sh("docker", "rm", "-f", NAME, timeout=60)            # stale leftovers
    port = _free_port()
    run = _sh("docker", "run", "-d", "--name", NAME,
              "-p", f"127.0.0.1:{port}:8200", IMAGE)
    assert run.returncode == 0, run.stderr
    url = f"http://127.0.0.1:{port}"
    deadline, status = time.time() + 120, "starting"
    while time.time() < deadline:
        status = _sh("docker", "inspect", "--format",
                     "{{.State.Health.Status}}", NAME, timeout=30).stdout.strip()
        if status == "healthy":
            break
        time.sleep(2)
    assert status == "healthy", f"never healthy (last={status}); logs:\n{_logs()}"
    yield url
    _sh("docker", "rm", "-f", NAME, timeout=60)


# ------------------------------------------------------------ image config --
def test_image_runs_as_non_root(img_cfg):
    assert img_cfg["Config"]["User"] == "appuser"


def test_image_exposes_8200(img_cfg):
    assert "8200/tcp" in img_cfg["Config"]["ExposedPorts"]


def test_image_env_flags(img_cfg):
    env = set(img_cfg["Config"]["Env"])
    assert {"PYTHONDONTWRITEBYTECODE=1", "PYTHONUNBUFFERED=1",
            "PIP_NO_CACHE_DIR=1", "PIP_DISABLE_PIP_VERSION_CHECK=1"} <= env


def test_image_healthcheck_config(img_cfg):
    hc = img_cfg["Config"]["Healthcheck"]
    assert hc["Interval"] == 15_000_000_000          # 15s (was 30s)
    assert hc["Timeout"] == 3_000_000_000            # 3s   (was 5s)
    assert hc["Retries"] == 3
    assert hc["StartPeriod"] == 20_000_000_000       # NEW: covers model load
    test_cmd = " ".join(hc["Test"])
    assert "127.0.0.1:8200/healthz" in test_cmd      # not 'localhost' (::1 flap)
    assert "localhost" not in test_cmd
    assert "timeout=2" in test_cmd and "status == 200" in test_cmd


def test_image_cmd_one_worker_no_access_log(img_cfg):
    assert img_cfg["Config"]["Cmd"] == [
        "uvicorn", "app.main:app", "--host", "0.0.0.0",
        "--port", "8200", "--no-access-log"]          # no --workers anywhere


def test_image_labels(img_cfg):
    labels = img_cfg["Config"]["Labels"] or {}
    assert labels.get("org.opencontainers.image.version") == "0.3.0"


# ----------------------------------------------------------- runtime user ---
def test_runtime_user_is_uid_10001(base_url):
    r = _exec(NAME, "id", "-u")
    assert r.returncode == 0 and r.stdout.strip() == "10001"


def test_runtime_user_shell_is_nologin(base_url):
    r = _exec(NAME, "getent", "passwd", "appuser")
    assert r.returncode == 0
    fields = r.stdout.strip().split(":")
    assert fields[2] == "10001" and fields[6] == "/usr/sbin/nologin"


# ------------------------------------------------------------ runtime HTTP --
def test_healthz_contract(base_url):
    status, _, body = _get(base_url, "/healthz")
    assert status == 200
    data = json.loads(body)
    assert data["ok"] is True
    assert data["model"] in ("heuristic-v0",) or data["model"].startswith("ens")
    assert int(data["horizon_days"]) >= 1


def test_model_version_matches_startup_log(base_url):
    """healthz must agree with what actually loaded (no silent drift)."""
    data = _wait_http(base_url)
    logs = _logs()
    m = re.search(r"forecaster_loaded version=(\S+)", logs)
    if m:
        assert data["model"] == m.group(1)
        assert "heuristic" not in logs.lower().split("forecaster_loaded")[0][-2000:]
    else:
        assert "heuristic-fallback" in logs
        assert data["model"] == "heuristic-v0"


def test_request_id_header(base_url):
    status, headers, _ = _post_json(base_url, "/v1/fusion",
                                    {"sentiment": {"score": 0.5}})
    assert status == 200
    assert any(k.lower() == "x-request-id" and len(v) == 12
               for k, v in headers.items())


def test_fusion_conflict_flagged(base_url):
    status, _, out = _post_json(base_url, "/v1/fusion", {
        "sentiment": {"score": 0.9},
        "voice_stress": {"score": 0.2}})
    assert status == 200
    assert out["conflict"] is True
    assert out["conflict_chi2"] > 3.84                       # chi2 crit, df=1
    assert "signal_conflict" in out["triggers"]
    assert 0.0 <= out["composite_score"] <= 1.0


def test_fusion_threat_force(base_url):
    status, _, out = _post_json(base_url, "/v1/fusion", {
        "threat": {"prob": 0.95}})
    assert status == 200
    assert "threat_force" in out["triggers"]
    assert out["label"] == "CRITICAL"
    assert out["composite_score"] >= 0.80
    assert out["confidence"] >= 0.60


def test_fusion_stale_reported(base_url):
    status, _, out = _post_json(base_url, "/v1/fusion", {
        "sentiment": {"score": 0.8,
                      "observed_at": "2020-01-01T00:00:00Z"}})
    assert status == 200
    assert "sentiment" in out["stale"]


def test_forecast_contract(base_url):
    status, _, out = _post_json(base_url, "/v1/forecast", {
        "case_id": "c-docker",
        "score_history": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85]})
    assert status == 200
    assert 0.0 <= out["p_escalation"] <= 0.97
    assert out["horizon_days"] == 7
    assert isinstance(out["drivers"], list) and out["drivers"]


def test_forecast_interval_ordered(base_url):
    _, _, out = _post_json(base_url, "/v1/forecast", {
        "case_id": "c-docker",
        "score_history": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85]})
    if out.get("p10") is not None:                           # model present
        assert out["p10"] <= out["p_escalation"] <= out["p90"]


def test_forecast_validation_422(base_url):
    status, _, body = _post_json(base_url, "/v1/forecast", {})
    assert status == 422                                     # case_id required
    assert "detail" in body


def test_explain_loo_structure(base_url):
    status, _, out = _post_json(base_url, "/v1/explain", {
        "sentiment": {"score": 0.8}, "threat": {"prob": 0.3},
        "voice_stress": {"score": 0.82}})
    assert status == 200
    assert set(out["sensors"]) == {"sentiment", "threat", "voice_stress"}
    for v in out["sensors"].values():
        assert "score_without_this" in v and "sigma" in v


def test_metrics_contract(base_url):
    _post_json(base_url, "/v1/fusion", {"sentiment": {"score": 0.5}})
    status, headers, body = _get(base_url, "/metrics")
    assert status == 200
    assert headers.get("Content-Type", "").startswith("text/plain")
    text = body.decode()
    assert "risk_fusion_requests_total" in text
    assert "risk_signal_mean" in text


# --------------------------------------------------------- runtime details --
def test_precompiled_bytecode_present(base_url):
    r = _exec(NAME, "sh", "-c", "find app -name '*.pyc' | grep -q .")
    assert r.returncode == 0                                 # compileall ran


def test_exactly_one_worker(base_url):
    assert _logs().count("Started server process") == 1


def test_graceful_shutdown(image):
    name, port = NAME + "-stop", _free_port()
    _sh("docker", "rm", "-f", name, timeout=60)
    try:
        r = _sh("docker", "run", "-d", "--name", name,
                "-p", f"127.0.0.1:{port}:8200", image)
        assert r.returncode == 0, r.stderr
        _wait_http(f"http://127.0.0.1:{port}", timeout_s=60)
        t0 = time.time()
        stop = _sh("docker", "stop", name, timeout=40)
        dt = time.time() - t0
        assert stop.returncode == 0
        assert dt < 25, f"shutdown took {dt:.1f}s -- not graceful"
        assert "shutdown" in _logs(name)                     # lifespan logged it
    finally:
        _sh("docker", "rm", "-f", name, timeout=60)


def test_read_only_rootfs_works(image):
    """The app must write nothing at runtime (noise cache/metrics in RAM)."""
    name, port = NAME + "-ro", _free_port()
    _sh("docker", "rm", "-f", name, timeout=60)
    try:
        r = _sh("docker", "run", "-d", "--name", name, "--read-only",
                "--tmpfs", "/tmp", "-p", f"127.0.0.1:{port}:8200", image)
        assert r.returncode == 0, r.stderr
        url = f"http://127.0.0.1:{port}"
        _wait_http(url, timeout_s=60)
        status, _, out = _post_json(url, "/v1/fusion",
                                    {"threat": {"prob": 0.95}})
        assert status == 200 and out["label"] == "CRITICAL"
    finally:
        _sh("docker", "rm", "-f", name, timeout=60)


# ------------------------------------------------------- negative gate test --
@pytest.mark.skipif(os.getenv("RUN_NEGATIVE") != "1",
                    reason="opt-in: set RUN_NEGATIVE=1 (extra docker build)")
def test_build_fails_on_corrupt_artifact(tmp_path):
    """A corrupt forecaster.pkl in the context MUST fail the build -- the
    smoke-test layer is the gate that stops bad artifacts reaching prod."""
    ctx = tmp_path / "ctx"
    ctx.mkdir()
    for item in ("Dockerfile", "requirements.txt", "app", "training"):
        src = ROOT / item
        if src.exists():
            (shutil.copytree if src.is_dir() else shutil.copy2)(src, ctx / item)
    (ctx / "artifacts").mkdir(exist_ok=True)
    (ctx / "artifacts" / "forecaster.pkl").write_bytes(b"garbage-not-a-pickle")
    (ctx / ".dockerignore").write_text("**/__pycache__\n.git\n")  # keep artifacts
    r = _sh("docker", "build", "-t", IMAGE + "-neg", str(ctx))
    _sh("docker", "rmi", "-f", IMAGE + "-neg", timeout=60)
    assert r.returncode != 0, "build must FAIL when the artifact is corrupt"
    assert "artifact present but rejected" in (r.stdout + r.stderr)

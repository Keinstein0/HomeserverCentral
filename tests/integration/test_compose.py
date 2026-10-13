"""INT-CMP-01, INT-CMP-02: Docker Compose config validation and healthcheck cascading."""

import subprocess

import pytest

from conftest import PROJECT_ROOT, COMPOSE_FILE, ENV_FILE


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


# INT-CMP-01: Compose Config Validation
def test_int_cmp_01_compose_config(stack):
    import os
    os.chdir(PROJECT_ROOT)

    # Prod config (no profile).
    result = _run(["docker", "compose", "-f", COMPOSE_FILE, "config"])
    assert result.returncode == 0, f"prod config failed: {result.stderr}"

    # Test profile config.
    result = _run([
        "docker", "compose", "--profile", "test",
        "--env-file", ENV_FILE, "-f", COMPOSE_FILE, "config",
    ])
    assert result.returncode == 0, f"test config failed: {result.stderr}"


# INT-CMP-02: Healthcheck Cascading
def test_int_cmp_02_healthcheck_cascading(stack):
    import json
    import time

    cmd = [
        "docker", "compose", "--profile", "test",
        "--env-file", ENV_FILE, "-f", COMPOSE_FILE,
        "ps", "--format", "json",
    ]

    # Poll until all healthchecked services report "healthy" (or timeout).
    # Docker healthchecks have intervals (10-30s) and start periods, so the
    # status may briefly be "starting" even after the HTTP endpoint is up.
    deadline = time.time() + 120
    containers = {}
    while time.time() < deadline:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"docker compose ps failed: {result.stderr}"
        containers.clear()
        for line in result.stdout.strip().split("\n"):
            if line:
                entry = json.loads(line)
                containers[entry["Service"]] = entry

        # Check all healthchecked services are healthy.
        all_healthy = True
        for service in ["matrix-auth-gateway", "status-api", "caddy"]:
            info = containers.get(service, {})
            health = info.get("Health", info.get("Status", ""))
            if "healthy" not in str(health).lower():
                all_healthy = False
                break
        if all_healthy:
            break
        time.sleep(5)
    else:
        # Timed out — show the last-known state for debugging.
        for name, info in containers.items():
            print(f"  {name}: {info.get('Health', info.get('Status', '?'))}")
        pytest.fail("Timed out waiting for all services to become healthy")

    # All healthchecked services must be healthy.
    for service in ["matrix-auth-gateway", "status-api", "caddy"]:
        assert service in containers, f"Missing container: {service}"
        health = containers[service].get("Health", containers[service].get("Status", ""))
        assert "healthy" in str(health).lower(), f"{service} not healthy: {health}"

    # The mock should be running (no healthcheck, just "Up").
    assert "tuwunel-mock" in containers, "Missing tuwunel-mock container"
    mock_status = str(containers["tuwunel-mock"].get("Status", ""))
    assert "Up" in mock_status or "running" in mock_status.lower(), \
        f"tuwunel-mock not running: {mock_status}"

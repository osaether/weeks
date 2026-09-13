"""Build the real C executable in isolation for regression tests."""

from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.fixture(scope="session")
def built_project(tmp_path_factory):
    root = Path(__file__).resolve().parents[1]
    project = tmp_path_factory.mktemp("weeks-build")
    for directory in ("src", "include"):
        shutil.copytree(root / directory, project / directory)
    shutil.copy2(root / "Makefile", project / "Makefile")
    result = subprocess.run(
        ["make"], cwd=project, capture_output=True, text=True, timeout=60
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return project


@pytest.fixture
def run_weeks(built_project, tmp_path):
    def run(yaml_text):
        (tmp_path / "test.yaml").write_text(yaml_text)
        return subprocess.run(
            [str(built_project / "weeks")],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=10,
        )

    return run

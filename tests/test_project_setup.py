"""Tests for the project-level tooling setup."""

from pathlib import Path


REQUIRED_MAKE_TARGETS = {
    "install",
    "run",
    "debug",
    "clean",
    "lint",
    "lint-strict",
}


def test_makefile_declares_required_targets() -> None:
    """Verify that the Makefile exposes every required project command."""
    project_root = Path(__file__).resolve().parents[1]
    makefile_content = (project_root / "Makefile").read_text(encoding="utf-8")

    for target in REQUIRED_MAKE_TARGETS:
        assert f"\n{target}:" in f"\n{makefile_content}"

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


def test_packaging_artifacts_present() -> None:
    """Verify that root packaging script, spec, and instructions exist."""
    project_root = Path(__file__).resolve().parents[1]
    package_sh = project_root / "package.sh"
    pacman_spec = project_root / "pacman.spec"
    instructions = project_root / "INSTRUCTIONS.txt"
    makefile = project_root / "Makefile"

    assert package_sh.is_file(), "package.sh must exist at repository root"
    assert pacman_spec.is_file(), "pacman.spec must exist at repository root"
    assert instructions.is_file(), "INSTRUCTIONS.txt must exist at root"
    assert "\npackage:" in f"\n{makefile.read_text(encoding='utf-8')}"

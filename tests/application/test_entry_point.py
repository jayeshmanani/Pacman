"""Application tests for the command-line entry point pac-man.py."""

import importlib
from pathlib import Path
from unittest.mock import patch
import pytest

_pacman_module = importlib.import_module("pac-man")
main = _pacman_module.main


def test_main_exits_when_no_args_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 when no config arg is passed."""
    with patch("sys.argv", ["pac-man.py"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Usage: python3 pac-man.py <config.json>" in captured.err


def test_main_exits_when_non_json_file_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 without .json extension."""
    with patch("sys.argv", ["pac-man.py", "config.txt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "must be a .json file" in captured.err


def test_main_exits_when_file_does_not_exist(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 when config file is missing."""
    with patch("sys.argv", ["pac-man.py", "non_existent.json"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_runs_app_with_valid_config(tmp_path: Path) -> None:
    """Verify main parses valid JSON and launches run_app."""
    config_file = tmp_path / "valid.json"
    config_file.write_text('{"lives": 5, "pacgum": 10}', encoding="utf-8")

    with patch("sys.argv", ["pac-man.py", str(config_file)]):
        with patch.object(_pacman_module, "run_app") as mock_run_app:
            main()

    mock_run_app.assert_called_once()
    passed_config = mock_run_app.call_args.kwargs.get("config")
    assert passed_config is not None
    assert passed_config.lives == 5
    assert passed_config.pacgum == 10


def test_main_falls_back_on_malformed_json(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main issues warning and uses defaults when JSON is malformed."""
    config_file = tmp_path / "malformed.json"
    config_file.write_text("invalid json content {{{", encoding="utf-8")

    with patch("sys.argv", ["pac-man.py", str(config_file)]):
        with patch.object(_pacman_module, "run_app") as mock_run_app:
            main()

    captured = capsys.readouterr()
    assert "Warning: Failed to parse" in captured.err
    mock_run_app.assert_called_once()
    passed_config = mock_run_app.call_args.kwargs.get("config")
    assert passed_config is not None
    assert passed_config.lives == 3


def test_main_handles_run_app_exception_gracefully(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main prints clean error without traceback when run_app fails."""
    config_file = tmp_path / "valid.json"
    config_file.write_text("{}", encoding="utf-8")

    with patch("sys.argv", ["pac-man.py", str(config_file)]):
        with patch.object(
            _pacman_module,
            "run_app",
            side_effect=RuntimeError("Video device failure"),
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Error: Video device failure" in captured.err


def test_main_handles_keyboard_interrupt_cleanly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify main exits code 0 on KeyboardInterrupt without error output."""
    config_file = tmp_path / "valid.json"
    config_file.write_text("{}", encoding="utf-8")

    with patch("sys.argv", ["pac-man.py", str(config_file)]):
        with patch.object(
            _pacman_module, "run_app", side_effect=KeyboardInterrupt
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert captured.err == ""

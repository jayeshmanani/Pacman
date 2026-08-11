"""Tests for the command-line entry point pac_man.py."""

from pathlib import Path
from unittest.mock import patch
import pytest
from pac_man import main


def test_main_exits_when_no_args_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 when no config arg is passed."""
    with patch("sys.argv", ["pac_man.py"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "Usage: python3 pac-man.py <config.json>" in captured.err


def test_main_exits_when_non_json_file_provided(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 without .json extension."""
    with patch("sys.argv", ["pac_man.py", "config.txt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "must be a .json file" in captured.err


def test_main_exits_when_file_does_not_exist(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main exits with error code 1 when config file is missing."""
    with patch("sys.argv", ["pac_man.py", "non_existent.json"]):
        with pytest.raises(SystemExit) as exc_info:
            main()

    assert exc_info.value.code == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_main_runs_app_with_valid_config(tmp_path: Path) -> None:
    """Verify main parses valid JSON and launches run_app."""
    config_file = tmp_path / "valid.json"
    config_file.write_text('{"lives": 5, "pacgum": 10}', encoding="utf-8")

    with patch("sys.argv", ["pac_man.py", str(config_file)]):
        with patch("pac_man.run_app") as mock_run_app:
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

    with patch("sys.argv", ["pac_man.py", str(config_file)]):
        with patch("pac_man.run_app") as mock_run_app:
            main()

    captured = capsys.readouterr()
    assert "Warning: Failed to parse" in captured.err
    mock_run_app.assert_called_once()
    passed_config = mock_run_app.call_args.kwargs.get("config")
    assert passed_config is not None
    assert passed_config.lives == 3

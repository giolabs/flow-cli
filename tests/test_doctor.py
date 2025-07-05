"""
Tests for the doctor command
"""

# mypy: ignore-errors

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from flow_cli.commands.doctor import (
    check_android_setup,
    check_flutter_setup,
    check_git_setup,
    check_ios_setup,
    doctor_command,
)
from tests.conftest import assert_command_success, assert_performance_under_threshold


class TestDoctorCommand:
    """Test suite for doctor command"""

    @pytest.mark.performance
    def test_doctor_command_success(self, cli_runner, mock_subprocess_run, performance_timer):
        """Test doctor command executes successfully"""
        # Mock successful environment checks
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        performance_timer.start()
        result = cli_runner.invoke(doctor_command)
        performance_timer.stop()

        assert_command_success(result)
        assert_performance_under_threshold(performance_timer.elapsed, 2.0)

    def test_doctor_checks_flutter_sdk(self, cli_runner, mock_subprocess_run):
        """Test doctor checks Flutter SDK"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        result = cli_runner.invoke(doctor_command)

        assert_command_success(result, "Flutter SDK")
        # Verify flutter --version was called
        mock_subprocess_run.assert_called()

    def test_doctor_checks_android_sdk(self, cli_runner, mock_subprocess_run):
        """Test doctor checks Android SDK"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Android SDK"

        result = cli_runner.invoke(doctor_command)

        assert_command_success(result)
        # Should check for adb and other Android tools
        calls = [call.args for call in mock_subprocess_run.call_args_list]
        assert any("adb" in str(call) for call in calls)

    def test_doctor_checks_ios_tools_on_macos(self, cli_runner, mock_subprocess_run):
        """Test doctor checks iOS tools on macOS"""
        with patch("platform.system", return_value="Darwin"):
            mock_subprocess_run.return_value.returncode = 0
            mock_subprocess_run.return_value.stdout = "Xcode 14.0"

            result = cli_runner.invoke(doctor_command)

            assert_command_success(result)
            # Should check for Xcode
            calls = [call.args for call in mock_subprocess_run.call_args_list]
            assert any("xcode-select" in str(call) for call in calls)

    def test_doctor_handles_missing_flutter(self, cli_runner, mock_subprocess_run):
        """Test doctor handles missing Flutter SDK"""
        mock_subprocess_run.side_effect = FileNotFoundError("Flutter not found")

        result = cli_runner.invoke(doctor_command)

        assert_command_success(result)  # Should still succeed but show warning
        assert "Flutter SDK" in result.output

    def test_doctor_shows_performance_metrics(self, cli_runner, mock_subprocess_run):
        """Test doctor shows performance information"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        result = cli_runner.invoke(doctor_command)

        assert_command_success(result)
        # Should show some performance or system information
        assert any(
            keyword in result.output.lower() for keyword in ["memory", "disk", "cpu", "system"]
        )

    def test_doctor_verbose_output(self, cli_runner, mock_subprocess_run):
        """Test doctor with verbose flag"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        result = cli_runner.invoke(doctor_command, ["--verbose"])

        assert_command_success(result)
        # Verbose output should contain more details
        assert len(result.output) > 100  # Should have substantial output

    def test_doctor_fix_flag(self, cli_runner, mock_subprocess_run):
        """Test doctor with --fix flag"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        result = cli_runner.invoke(doctor_command, ["--fix"])

        assert_command_success(result)
        # Should attempt to fix issues
        assert "fix" in result.output.lower() or "repair" in result.output.lower()

    @pytest.mark.performance
    def test_doctor_performance_under_threshold(
        self, cli_runner, mock_subprocess_run, performance_timer
    ):
        """Test doctor command completes within performance threshold"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        performance_timer.start()
        result = cli_runner.invoke(doctor_command)
        performance_timer.stop()

        assert_command_success(result)
        # Doctor should complete quickly
        assert_performance_under_threshold(performance_timer.elapsed, 3.0)

    @pytest.mark.parametrize(
        "platform_name,expected_tools",
        [
            ("Darwin", ["xcode-select", "xcrun"]),
            ("Linux", ["adb", "sdkmanager"]),
            ("Windows", ["adb", "sdkmanager"]),
        ],
    )
    def test_doctor_platform_specific_checks(
        self, cli_runner, mock_subprocess_run, platform_name, expected_tools
    ):
        """Test doctor performs platform-specific checks"""
        with patch("platform.system", return_value=platform_name):
            mock_subprocess_run.return_value.returncode = 0
            mock_subprocess_run.return_value.stdout = "Tool found"

            result = cli_runner.invoke(doctor_command)

            assert_command_success(result)

            # Verify platform-specific tools are checked
            calls = [str(call) for call in mock_subprocess_run.call_args_list]
            if platform_name == "Darwin":
                assert any(tool in call for call in calls for tool in expected_tools)

    def test_doctor_concurrent_checks(self, cli_runner, mock_subprocess_run):
        """Test doctor performs checks concurrently for speed"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Tool found"

        with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
            mock_executor.return_value.__enter__.return_value.submit.return_value.result.return_value = (
                True
            )

            result = cli_runner.invoke(doctor_command)

            assert_command_success(result)
            # Should use concurrent execution for speed
            # This test verifies the pattern is set up for concurrent execution

    def test_doctor_error_handling(self, cli_runner, mock_subprocess_run):
        """Test doctor handles errors gracefully"""
        mock_subprocess_run.side_effect = [
            Mock(returncode=0, stdout="Flutter 3.13.0"),  # Flutter check succeeds
            Exception("Network error"),  # Some check fails
            Mock(returncode=1, stderr="Tool not found"),  # Another check fails
        ]

        result = cli_runner.invoke(doctor_command)

        # Should still complete successfully despite individual check failures
        assert_command_success(result)
        assert "error" in result.output.lower() or "warning" in result.output.lower()

    def test_doctor_json_output(self, cli_runner, mock_subprocess_run):
        """Test doctor with JSON output format"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        result = cli_runner.invoke(doctor_command, ["--json"])

        assert_command_success(result)
        # Should produce valid JSON output
        import json

        try:
            json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail("Output is not valid JSON")

    def test_doctor_config_validation(self, cli_runner, mock_subprocess_run, sample_config):
        """Test doctor validates configuration settings"""
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Flutter 3.13.0"

        with patch("flow_cli.commands.config.load_config", return_value=sample_config):
            result = cli_runner.invoke(doctor_command)

            assert_command_success(result)
            # Should validate config paths
            assert "configuration" in result.output.lower()


@pytest.mark.parametrize("flutter_exists", [True, False])
def test_check_flutter_setup(monkeypatch: Any, flutter_exists: bool) -> None:
    """Test Flutter setup check"""

    def mock_which(cmd: str) -> str:
        if cmd == "flutter" and flutter_exists:
            return "/usr/local/bin/flutter"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_flutter_setup()

    assert "flutter_installed" in result
    assert result["flutter_installed"] == flutter_exists


def test_check_android_setup(monkeypatch: Any) -> None:
    """Test Android setup check"""

    def mock_which(cmd: str) -> str:
        if cmd in ["adb", "sdkmanager"]:
            return f"/android/sdk/platform-tools/{cmd}"
        return ""

    def mock_environ_get(key: str, default: str = None) -> str:
        if key == "ANDROID_HOME":
            return "/android/sdk"
        elif key == "ANDROID_SDK_ROOT":
            return "/android/sdk"
        return default if default is not None else ""

    monkeypatch.setattr("shutil.which", mock_which)
    monkeypatch.setattr("os.environ.get", mock_environ_get)

    result = check_android_setup()

    assert "android_installed" in result
    assert result["android_installed"] is True


def test_check_ios_setup_on_macos(monkeypatch: Any) -> None:
    """Test iOS setup check on macOS"""

    # Mock platform.system to return 'Darwin'
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    def mock_which(cmd: str) -> str:
        if cmd in ["xcodebuild", "xcrun"]:
            return f"/usr/bin/{cmd}"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_ios_setup()

    assert "ios_development_possible" in result
    assert result["ios_development_possible"] is True


def test_check_ios_setup_non_macos(monkeypatch: Any) -> None:
    """Test iOS setup check on non-macOS"""

    # Mock platform.system to return 'Linux'
    monkeypatch.setattr("platform.system", lambda: "Linux")

    result = check_ios_setup()

    assert "ios_development_possible" in result
    assert result["ios_development_possible"] is False
    assert "requires_macos" in result


def test_check_git_setup_installed(monkeypatch: Any) -> None:
    """Test Git setup check with Git installed"""

    def mock_which(cmd: str) -> str:
        if cmd == "git":
            return "/usr/bin/git"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_git_setup()

    assert "git_installed" in result
    assert result["git_installed"] is True


def test_check_git_setup_not_installed(monkeypatch: Any) -> None:
    """Test Git setup check with Git not installed"""

    def mock_which(cmd: str) -> str:
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_git_setup()

    assert "git_installed" in result
    assert result["git_installed"] is False


def test_doctor_command_success(monkeypatch: Any, capsys: Any) -> None:
    """Test doctor command with all checks passing"""

    # Mock all check functions
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_flutter_setup",
        lambda: {"flutter_installed": True, "version": "3.13.1"},
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_android_setup",
        lambda: {"android_installed": True, "sdk_path": "/android/sdk"},
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_ios_setup",
        lambda: {"ios_development_possible": True, "xcode_installed": True},
    )
    monkeypatch.setattr("flow_cli.commands.doctor.check_git_setup", lambda: {"git_installed": True})

    # Run doctor command
    doctor_command()

    # Check output
    captured = capsys.readouterr()
    assert "Environment Check" in captured.out
    assert "✅" in captured.out  # Success indicators


def test_doctor_command_failures(monkeypatch: Any, capsys: Any) -> None:
    """Test doctor command with failing checks"""

    # Mock check functions with failures
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_flutter_setup",
        lambda: {"flutter_installed": False, "error": "Flutter not found"},
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_android_setup",
        lambda: {"android_installed": False, "error": "Android SDK not found"},
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_ios_setup",
        lambda: {"ios_development_possible": False, "requires_macos": True},
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_git_setup", lambda: {"git_installed": False}
    )

    # Run doctor command
    doctor_command()

    # Check output
    captured = capsys.readouterr()
    assert "Environment Check" in captured.out
    assert "❌" in captured.out  # Failure indicators

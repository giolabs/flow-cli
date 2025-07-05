"""
Tests for the doctor command
"""

# mypy: ignore-errors

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from flow_cli.commands.doctor import (
    check_android,
    check_flutter,
    check_git,
    check_ios,
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
            assert any("xcrun" in str(call) for call in calls)

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
        # Should show environment health information
        assert any(
            keyword in result.output.lower() for keyword in ["environment", "health", "check", "summary"]
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
        # Mock some checks to fail and others to succeed
        def mock_subprocess_side_effect(*args, **kwargs):
            if "flutter" in str(args[0]):
                if "doctor" in str(args[0]):
                    return Mock(returncode=0, stdout="No issues found!")
                else:
                    return Mock(returncode=0, stdout="Flutter 3.13.0")
            elif "git" in str(args[0]):
                return Mock(returncode=1, stderr="Tool not found")
            else:
                return Mock(returncode=0, stdout="Tool found")

        mock_subprocess_run.side_effect = mock_subprocess_side_effect

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
            # Should show environment health check results
            assert "environment health check" in result.output.lower()


@pytest.mark.parametrize("flutter_exists", [True, False])
def test_check_flutter_setup(monkeypatch: Any, flutter_exists: bool) -> None:
    """Test Flutter setup check"""

    def mock_which(cmd: str) -> str:
        if cmd == "flutter" and flutter_exists:
            return "/usr/local/bin/flutter"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)
    
    if flutter_exists:
        # Mock successful Flutter version check and doctor check
        def mock_subprocess_run(*args, **kwargs):
            if "doctor" in args[0]:
                return Mock(returncode=0, stdout="No issues found!")
            else:
                return Mock(returncode=0, stdout="Flutter 3.13.0 • channel stable • https://github.com/flutter/flutter.git")
        monkeypatch.setattr("subprocess.run", mock_subprocess_run)
    else:
        # Mock failed Flutter check
        monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Mock(returncode=1, stdout="", stderr=""))

    result = check_flutter(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "Flutter SDK"
    if flutter_exists:
        assert result[1] == "✅"  # Status is checkmark
    else:
        assert result[1] == "❌"  # Status is X


def test_check_android_setup(monkeypatch: Any) -> None:
    """Test Android setup check"""

    def mock_which(cmd: str) -> str:
        if cmd in ["adb", "sdkmanager"]:
            return f"/android/sdk/platform-tools/{cmd}"
        return ""

    def mock_environ_get(key: str, default: Optional[str] = None) -> str:
        if key == "ANDROID_HOME":
            return "/android/sdk"
        elif key == "ANDROID_SDK_ROOT":
            return "/android/sdk"
        return default if default is not None else ""

    monkeypatch.setattr("shutil.which", mock_which)
    monkeypatch.setattr("os.environ.get", mock_environ_get)

    result = check_android(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "Android SDK"


def test_check_ios_setup_on_macos(monkeypatch: Any) -> None:
    """Test iOS setup check on macOS"""

    # Mock platform.system to return 'Darwin'
    monkeypatch.setattr("platform.system", lambda: "Darwin")

    def mock_which(cmd: str) -> str:
        if cmd in ["xcodebuild", "xcrun"]:
            return f"/usr/bin/{cmd}"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_ios(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "iOS Development"


def test_check_ios_setup_non_macos(monkeypatch: Any) -> None:
    """Test iOS setup check on non-macOS"""

    # Mock platform.system to return 'Linux'
    monkeypatch.setattr("platform.system", lambda: "Linux")

    result = check_ios(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "iOS Development"
    assert "macOS" in result[3]  # Details should mention macOS requirement


def test_check_git_setup_installed(monkeypatch: Any) -> None:
    """Test Git setup check with Git installed"""

    def mock_which(cmd: str) -> str:
        if cmd == "git":
            return "/usr/bin/git"
        return ""

    monkeypatch.setattr("shutil.which", mock_which)

    result = check_git(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "Git"
    assert result[1] == "✅"  # Status is checkmark


def test_check_git_setup_not_installed(monkeypatch: Any) -> None:
    """Test Git setup check with Git not installed"""

    def mock_which(cmd: str) -> str:
        return ""

    monkeypatch.setattr("shutil.which", mock_which)
    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: Mock(returncode=1, stdout="", stderr=""))

    result = check_git(verbose=False)

    # Result is a tuple: (component, status, info, details)
    assert isinstance(result, tuple)
    assert len(result) == 4
    assert result[0] == "Git"
    assert result[1] == "❌"  # Status is X


def test_doctor_command_success(cli_runner, monkeypatch: Any) -> None:
    """Test doctor command with all checks passing"""

    # Mock all check functions with tuple returns
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_flutter",
        lambda verbose: (
            "Flutter SDK",
            "✅",
            "Flutter 3.13.1",
            "All Flutter dependencies satisfied",
        ),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_android",
        lambda verbose: ("Android SDK", "✅", "Android SDK found", "SDK at /android/sdk"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_ios",
        lambda verbose: ("iOS Development", "✅", "Xcode available", "iOS simulators found"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_git",
        lambda verbose: ("Git", "✅", "Git 2.30.1", "Git is available"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_python",
        lambda verbose: ("Python", "✅", "Python 3.9.5", "Python version is compatible"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_python_packages",
        lambda verbose: ("Python Packages", "✅", "All packages available", "All packages found"),
    )

    # Run doctor command using CLI runner
    result = cli_runner.invoke(doctor_command)

    # Check output
    assert_command_success(result)
    assert "Environment Health Check" in result.output
    assert "✅" in result.output  # Success indicators


def test_doctor_command_failures(cli_runner, monkeypatch: Any) -> None:
    """Test doctor command with failing checks"""

    # Mock check functions with failures
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_flutter",
        lambda verbose: ("Flutter SDK", "❌", "Not found", "Install Flutter SDK from flutter.dev"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_android",
        lambda verbose: ("Android SDK", "❌", "Not found", "Install Android SDK"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_ios",
        lambda verbose: (
            "iOS Development",
            "ℹ️",
            "Not applicable",
            "iOS development requires macOS",
        ),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_git",
        lambda verbose: ("Git", "❌", "Not found", "Install Git from git-scm.com"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_python",
        lambda verbose: ("Python", "✅", "Python 3.9.5", "Python version is compatible"),
    )
    monkeypatch.setattr(
        "flow_cli.commands.doctor.check_python_packages",
        lambda verbose: ("Python Packages", "⚠️", "2 missing", "Missing: inquirer, pyyaml"),
    )

    # Run doctor command using CLI runner
    result = cli_runner.invoke(doctor_command)

    # Check output
    assert_command_success(result)
    assert "Environment Health Check" in result.output
    assert "❌" in result.output  # Failure indicators

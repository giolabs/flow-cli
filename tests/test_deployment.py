"""
Tests for deployment commands
"""

import pytest
from unittest.mock import patch, Mock, mock_open
from pathlib import Path
from click.testing import CliRunner

from flow_cli.commands.deployment.main import deployment_group
from flow_cli.commands.deployment.setup import setup_fastlane_command
from flow_cli.commands.deployment.keystore import keystore_command
from flow_cli.commands.deployment.release import release_command
from tests.conftest import (
    assert_command_success,
    assert_command_failure,
    assert_file_exists,
    assert_file_contains,
    assert_performance_under_threshold,
)


class TestDeploymentSetup:
    """Test suite for deployment setup command"""

    def test_setup_fastlane_success(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test successful Fastlane setup"""
        # Mock user inputs
        mock_inquirer_prompt.side_effect = [
            True,  # Confirm proceed
            {
                "platforms": ["Android"],
                "app_identifier": "com.example.test",
                "developer_name": "Test Developer",
            },
            {"package_name": "com.example.test", "track": "internal", "upload_to_play_store": True},
        ]

        # Mock successful git and bundle operations
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = ""

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            result = cli_runner.invoke(setup_fastlane_command)

            assert_command_success(result, "Fastlane configured successfully")

    def test_setup_creates_feature_branch(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test that setup creates a feature branch"""
        mock_inquirer_prompt.side_effect = [
            True,  # Confirm proceed
            {
                "platforms": ["Android"],
                "app_identifier": "com.example.test",
                "developer_name": "Test Developer",
            },
            {"package_name": "com.example.test", "track": "internal", "upload_to_play_store": True},
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            result = cli_runner.invoke(setup_fastlane_command)

            # Verify git commands were called
            git_calls = [call for call in mock_subprocess_run.call_args_list if "git" in str(call)]

            assert any("checkout -b feature/fastlane-setup" in str(call) for call in git_calls)
            assert_command_success(result)

    def test_setup_skip_branch_flag(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test setup with --skip-branch flag"""
        mock_inquirer_prompt.return_value = {
            "platforms": ["Android"],
            "app_identifier": "com.example.test",
            "developer_name": "Test Developer",
        }

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            result = cli_runner.invoke(setup_fastlane_command, ["--skip-branch"])

            # Should not create git branch
            git_calls = [call for call in mock_subprocess_run.call_args_list if "git" in str(call)]

            assert not any("checkout -b" in str(call) for call in git_calls)
            assert_command_success(result)

    def test_setup_force_flag(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test setup with --force flag overwrites existing Fastlane"""
        # Create existing Fastfile
        fastlane_dir = mock_flutter_project_with_git / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("existing content")

        mock_inquirer_prompt.side_effect = [
            True,  # Confirm proceed
            {
                "platforms": ["Android"],
                "app_identifier": "com.example.test",
                "developer_name": "Test Developer",
            },
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            result = cli_runner.invoke(setup_fastlane_command, ["--force"])

            assert_command_success(result)

    def test_setup_prerequisites_check(
        self, cli_runner, mock_flutter_project_with_git, mock_subprocess_run
    ):
        """Test setup checks prerequisites"""
        # Mock missing prerequisites
        mock_subprocess_run.side_effect = FileNotFoundError("ruby not found")

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            result = cli_runner.invoke(setup_fastlane_command)

            assert "Prerequisites check failed" in result.output

    def test_setup_generates_gemfile(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test setup generates Gemfile"""
        mock_inquirer_prompt.side_effect = [
            True,  # Confirm proceed
            {
                "platforms": ["Android"],
                "app_identifier": "com.example.test",
                "developer_name": "Test Developer",
            },
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            with patch("builtins.open", mock_open()) as mock_file:
                result = cli_runner.invoke(setup_fastlane_command)

                # Verify Gemfile was written
                mock_file.assert_called()
                assert_command_success(result)


class TestKeystoreGeneration:
    """Test suite for keystore generation command"""

    def test_keystore_android_generation(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test Android keystore generation"""
        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(keystore_command, ["--platform", "android"])

            # Verify keytool was called
            keytool_calls = [
                call for call in mock_subprocess_run.call_args_list if "keytool" in str(call)
            ]
            assert len(keytool_calls) > 0
            assert_command_success(result)

    def test_keystore_ios_generation_macos(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt
    ):
        """Test iOS keystore generation on macOS"""
        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        with patch("platform.system", return_value="Darwin"):
            with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
                mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

                result = cli_runner.invoke(keystore_command, ["--platform", "ios"])

                assert_command_success(result)
                assert "iOS certificate setup instructions created" in result.output

    def test_keystore_ios_generation_non_macos(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt
    ):
        """Test iOS keystore generation on non-macOS"""
        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        with patch("platform.system", return_value="Linux"):
            with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
                mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

                result = cli_runner.invoke(keystore_command, ["--platform", "ios"])

                assert_command_success(result)
                assert "iOS certificate generation requires macOS" in result.output

    def test_keystore_force_regeneration(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test keystore force regeneration"""
        # Create existing keystore
        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("existing keystore")

        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(keystore_command, ["--platform", "android", "--force"])

            assert_command_success(result)
            # Should regenerate even with existing keystore

    def test_keystore_security_gitignore(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test keystore creates .gitignore for security"""
        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            with patch("builtins.open", mock_open()) as mock_file:
                result = cli_runner.invoke(keystore_command, ["--platform", "android"])

                # Verify .gitignore was created
                mock_file.assert_called()
                assert_command_success(result)

    @pytest.mark.performance
    def test_keystore_performance(
        self,
        cli_runner,
        mock_flutter_project,
        mock_inquirer_prompt,
        mock_subprocess_run,
        performance_timer,
    ):
        """Test keystore generation performance"""
        mock_inquirer_prompt.return_value = {
            "company_name": "Test Company",
            "app_name": "Test App",
            "country_code": "US",
            "city": "Test City",
            "state": "Test State",
        }

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            performance_timer.start()
            result = cli_runner.invoke(keystore_command, ["--platform", "android"])
            performance_timer.stop()

            assert_command_success(result)
            # Keystore generation should be reasonably fast
            assert_performance_under_threshold(performance_timer.elapsed, 5.0)


class TestReleaseCommand:
    """Test suite for release command"""

    def test_release_prerequisites_check(self, cli_runner, mock_flutter_project):
        """Test release checks prerequisites"""
        # Missing Fastlane
        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(release_command)

            assert "Fastlane not configured" in result.output

    def test_release_android_build_only(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test Android release build only"""
        # Create required files
        fastlane_dir = mock_flutter_project / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("# Fastfile")

        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("keystore")
        (keys_dir / "keystore.properties").write_text("properties")

        mock_inquirer_prompt.side_effect = [
            {
                "flavor": "default",
                "build_mode": "release",
                "run_tests": False,
                "increment_version": False,
            },
            True,  # Confirm release
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(release_command, ["--platform", "android", "--build-only"])

            # Verify flutter build was called
            flutter_calls = [
                call for call in mock_subprocess_run.call_args_list if "flutter" in str(call)
            ]
            assert any("build appbundle" in str(call) for call in flutter_calls)
            assert_command_success(result)

    def test_release_with_tests(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test release with tests enabled"""
        # Create required files
        fastlane_dir = mock_flutter_project / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("# Fastfile")

        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("keystore")
        (keys_dir / "keystore.properties").write_text("properties")

        mock_inquirer_prompt.side_effect = [
            {
                "flavor": "default",
                "build_mode": "release",
                "run_tests": True,
                "increment_version": False,
            },
            True,  # Confirm release
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(release_command, ["--platform", "android", "--build-only"])

            # Verify flutter test was called
            test_calls = [
                call for call in mock_subprocess_run.call_args_list if "flutter test" in str(call)
            ]
            assert len(test_calls) > 0
            assert_command_success(result)

    def test_release_version_increment(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test release with version increment"""
        # Create required files
        fastlane_dir = mock_flutter_project / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("# Fastfile")

        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("keystore")
        (keys_dir / "keystore.properties").write_text("properties")

        # Create pubspec.yaml with version
        (mock_flutter_project / "pubspec.yaml").write_text(
            """
name: test_project
version: 1.0.0+1
"""
        )

        mock_inquirer_prompt.side_effect = [
            {
                "flavor": "default",
                "build_mode": "release",
                "run_tests": False,
                "increment_version": True,
            },
            True,  # Confirm release
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            result = cli_runner.invoke(release_command, ["--platform", "android", "--build-only"])

            assert_command_success(result)
            # Should increment version in pubspec.yaml

    def test_release_flavor_support(
        self, cli_runner, mock_flutter_project, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test release with flavor support"""
        # Create required files
        fastlane_dir = mock_flutter_project / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("# Fastfile")

        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("keystore")
        (keys_dir / "keystore.properties").write_text("properties")

        mock_inquirer_prompt.side_effect = [
            {
                "flavor": "development",
                "build_mode": "release",
                "run_tests": False,
                "increment_version": False,
            },
            True,  # Confirm release
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(
                path=mock_flutter_project,
                name="test_project",
                flavors=["development", "production"],
            )

            result = cli_runner.invoke(release_command, ["--flavor", "development", "--build-only"])

            # Verify flavor was used in build command
            flutter_calls = [
                call for call in mock_subprocess_run.call_args_list if "flutter" in str(call)
            ]
            assert any("--flavor development" in str(call) for call in flutter_calls)
            assert_command_success(result)

    @pytest.mark.performance
    def test_release_performance(
        self,
        cli_runner,
        mock_flutter_project,
        mock_inquirer_prompt,
        mock_subprocess_run,
        performance_timer,
    ):
        """Test release command performance"""
        # Create required files
        fastlane_dir = mock_flutter_project / "fastlane"
        fastlane_dir.mkdir()
        (fastlane_dir / "Fastfile").write_text("# Fastfile")

        keys_dir = mock_flutter_project / "keys"
        keys_dir.mkdir()
        (keys_dir / "release-key.jks").write_text("keystore")
        (keys_dir / "keystore.properties").write_text("properties")

        mock_inquirer_prompt.side_effect = [
            {
                "flavor": "default",
                "build_mode": "release",
                "run_tests": False,
                "increment_version": False,
            },
            True,  # Confirm release
        ]

        mock_subprocess_run.return_value.returncode = 0

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project, name="test_project")

            performance_timer.start()
            result = cli_runner.invoke(release_command, ["--platform", "android", "--build-only"])
            performance_timer.stop()

            assert_command_success(result)
            # Release should complete in reasonable time for build-only
            assert_performance_under_threshold(performance_timer.elapsed, 10.0)


class TestDeploymentIntegration:
    """Integration tests for deployment workflow"""

    def test_complete_deployment_workflow(
        self, cli_runner, mock_flutter_project_with_git, mock_inquirer_prompt, mock_subprocess_run
    ):
        """Test complete deployment workflow from setup to release"""
        # Mock all subprocess calls as successful
        mock_subprocess_run.return_value.returncode = 0
        mock_subprocess_run.return_value.stdout = "Success"

        # Mock user inputs for setup
        mock_inquirer_prompt.side_effect = [
            True,  # Confirm setup
            {
                "platforms": ["Android"],
                "app_identifier": "com.example.test",
                "developer_name": "Test Developer",
            },
            {"package_name": "com.example.test", "track": "internal", "upload_to_play_store": True},
            # Keystore inputs
            {
                "company_name": "Test Company",
                "app_name": "Test App",
                "country_code": "US",
                "city": "Test City",
                "state": "Test State",
            },
            # Release inputs
            {
                "flavor": "default",
                "build_mode": "release",
                "run_tests": False,
                "increment_version": False,
            },
            True,  # Confirm release
        ]

        with patch("flow_cli.core.flutter.FlutterProject.find_project") as mock_find:
            mock_find.return_value = Mock(path=mock_flutter_project_with_git, name="test_project")

            # 1. Setup Fastlane
            result_setup = cli_runner.invoke(setup_fastlane_command)
            assert_command_success(result_setup)

            # 2. Generate Keystore
            result_keystore = cli_runner.invoke(keystore_command, ["--platform", "android"])
            assert_command_success(result_keystore)

            # 3. Create required files for release
            fastlane_dir = mock_flutter_project_with_git / "fastlane"
            fastlane_dir.mkdir(exist_ok=True)
            (fastlane_dir / "Fastfile").write_text("# Fastfile")

            keys_dir = mock_flutter_project_with_git / "keys"
            keys_dir.mkdir(exist_ok=True)
            (keys_dir / "release-key.jks").write_text("keystore")
            (keys_dir / "keystore.properties").write_text("properties")

            # 4. Release
            result_release = cli_runner.invoke(
                release_command, ["--platform", "android", "--build-only"]
            )
            assert_command_success(result_release)

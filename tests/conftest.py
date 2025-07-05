"""
Pytest configuration and fixtures for Flow CLI tests
"""

# mypy: ignore-errors

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Union

import pytest
from click.testing import CliRunner

from flow_cli.core.flutter import FlutterProject


@pytest.fixture
def cli_runner():
    """Provide a CLI runner for testing Click commands"""
    return CliRunner()


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_flutter_project(temp_dir):
    """Create a mock Flutter project structure"""
    # Create Flutter project structure
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()

    # Create pubspec.yaml
    pubspec_content = """
name: test_project
description: A test Flutter project
version: 1.0.0+1

environment:
  sdk: ">=2.17.0 <4.0.0"
  flutter: ">=3.0.0"

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""

    (project_dir / "pubspec.yaml").write_text(pubspec_content)

    # Create lib directory
    lib_dir = project_dir / "lib"
    lib_dir.mkdir()
    (lib_dir / "main.dart").write_text(
        """
import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Test App',
      home: Container(),
    );
  }
}
"""
    )

    # Create android directory
    android_dir = project_dir / "android"
    android_dir.mkdir()
    (android_dir / "build.gradle").write_text(
        """
buildscript {
    ext.kotlin_version = '1.7.10'
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:7.2.0'
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}
"""
    )

    # Create android/app directory
    android_app_dir = android_dir / "app"
    android_app_dir.mkdir()
    (android_app_dir / "build.gradle").write_text(
        """
def localProperties = new Properties()
def localPropertiesFile = rootProject.file('local.properties')
if (localPropertiesFile.exists()) {
    localPropertiesFile.withReader('UTF-8') { reader ->
        localProperties.load(reader)
    }
}

def flutterRoot = localProperties.getProperty('flutter.sdk')
if (flutterRoot == null) {
    throw new GradleException("Flutter SDK not found. Define location with flutter.sdk in the local.properties file.")
}

android {
    compileSdkVersion 33
    
    defaultConfig {
        applicationId "com.example.test_project"
        minSdkVersion 21
        targetSdkVersion 33
        versionCode 1
        versionName "1.0"
    }
    
    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
"""
    )

    # Create ios directory
    ios_dir = project_dir / "ios"
    ios_dir.mkdir()
    (ios_dir / "Podfile").write_text(
        """
platform :ios, '11.0'

target 'Runner' do
  use_frameworks!
  use_modular_headers!

  flutter_install_all_ios_pods File.dirname(File.realpath(__FILE__))
end
"""
    )

    # Create flavors directory
    flavors_dir = project_dir / "flavors"
    flavors_dir.mkdir()

    # Create development flavor
    dev_flavor_dir = flavors_dir / "development"
    dev_flavor_dir.mkdir()
    (dev_flavor_dir / "config.json").write_text(
        """
{
  "app_name": "Test App Dev",
  "package_name": "com.example.test_project.dev",
  "primary_color": "#2196F3",
  "icon_path": "assets/icons/icon_dev.png"
}
"""
    )

    # Create production flavor
    prod_flavor_dir = flavors_dir / "production"
    prod_flavor_dir.mkdir()
    (prod_flavor_dir / "config.json").write_text(
        """
{
  "app_name": "Test App",
  "package_name": "com.example.test_project",
  "primary_color": "#FF5722",
  "icon_path": "assets/icons/icon_prod.png"
}
"""
    )

    return project_dir


@pytest.fixture
def mock_flutter_project_with_git(mock_flutter_project, temp_dir):
    """Create a mock Flutter project with git repository"""
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=mock_flutter_project, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=mock_flutter_project,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"], cwd=mock_flutter_project, capture_output=True
    )
    subprocess.run(["git", "add", "."], cwd=mock_flutter_project, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"], cwd=mock_flutter_project, capture_output=True
    )

    return mock_flutter_project


@pytest.fixture
def mock_flutter_sdk():
    """Mock Flutter SDK detection"""
    with patch("flow_cli.core.flutter.FlutterProject._detect_flutter_version") as mock_version:
        mock_version.return_value = "3.13.0"
        yield mock_version


@pytest.fixture
def mock_subprocess_run():
    """Mock subprocess.run for testing command execution"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_inquirer_prompt():
    """Mock inquirer.prompt for testing interactive commands"""
    with patch("inquirer.prompt") as mock_prompt:
        yield mock_prompt


@pytest.fixture
def mock_console():
    """Mock Rich console for testing output"""
    with patch("flow_cli.core.ui.banner.console") as mock_console:
        yield mock_console


@pytest.fixture
def sample_config():
    """Provide sample configuration for tests"""
    return {
        "flutter": {"sdk_path": "/usr/local/flutter", "channel": "stable"},
        "android": {"sdk_path": "/Users/test/Library/Android/sdk", "build_tools_version": "33.0.0"},
        "ios": {"xcode_path": "/Applications/Xcode.app", "team_id": "ABCD123456"},
        "general": {
            "default_flavor": "development",
            "auto_pub_get": True,
            "verbose_output": False,
            "color_output": True,
        },
    }


class MockFlutterProject:
    """Mock Flutter project for testing"""

    def __init__(self, path, name="test_project", flavors=None):
        self.path = Path(path)
        self.name = name
        self.flavors = flavors or ["development", "production"]
        self.flutter_version = "3.13.0"

    @staticmethod
    def find_project(start_path=None):
        """Mock find_project method"""
        if start_path:
            return MockFlutterProject(start_path)
        return MockFlutterProject("/tmp/test_project")

    def has_flavor(self, flavor):
        """Check if project has specific flavor"""
        return flavor in self.flavors

    def get_flavor_config(self, flavor):
        """Get flavor configuration"""
        return {
            "app_name": f"Test App {flavor.title()}",
            "package_name": f"com.example.test_project.{flavor}",
            "primary_color": "#2196F3",
        }


@pytest.fixture
def mock_flutter_project_class():
    """Mock the FlutterProject class"""
    with patch("flow_cli.core.flutter.FlutterProject") as mock_class:
        mock_class.find_project.return_value = MockFlutterProject("/tmp/test_project")
        yield mock_class


# Test data fixtures
@pytest.fixture
def sample_fastlane_config():
    """Sample Fastlane configuration for testing"""
    return {
        "platforms": ["Android", "iOS"],
        "app_identifier": "com.example.test_project",
        "developer_name": "Test Developer",
        "android": {
            "package_name": "com.example.test_project",
            "track": "internal",
            "upload_to_play_store": True,
        },
        "ios": {"team_id": "ABCD123456", "itc_team_id": "EFGH789012", "upload_to_app_store": True},
    }


@pytest.fixture
def sample_keystore_config():
    """Sample keystore configuration for testing"""
    return {
        "company_name": "Test Company",
        "app_name": "Test App",
        "country_code": "US",
        "city": "Test City",
        "state": "Test State",
        "android_keystore_password": "test_password_123",
        "android_key_password": "test_key_password_123",
    }


@pytest.fixture
def sample_release_config():
    """Sample release configuration for testing"""
    return {
        "platform": "both",
        "flavor": "development",
        "track": "internal",
        "build_mode": "release",
        "run_tests": True,
        "increment_version": True,
        "build_only": False,
        "deploy_to_store": True,
    }


# Performance test fixtures
@pytest.fixture
def performance_timer():
    """Timer for performance testing"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

    return Timer()


# Assertion helpers
def assert_command_success(result, expected_output=None):
    """Assert that a CLI command was successful"""
    assert (
        result.exit_code == 0
    ), f"Command failed with exit code {result.exit_code}. Output: {result.output}"

    if expected_output:
        assert (
            expected_output in result.output
        ), f"Expected output '{expected_output}' not found in: {result.output}"


def assert_command_failure(result, expected_exit_code=1, expected_error=None):
    """Assert that a CLI command failed as expected"""
    assert (
        result.exit_code == expected_exit_code
    ), f"Expected exit code {expected_exit_code}, got {result.exit_code}"

    if expected_error:
        assert (
            expected_error in result.output
        ), f"Expected error '{expected_error}' not found in: {result.output}"


def assert_file_exists(file_path):
    """Assert that a file exists"""
    assert Path(file_path).exists(), f"File {file_path} does not exist"


def assert_file_contains(file_path, content):
    """Assert that a file contains specific content"""
    assert_file_exists(file_path)
    file_content = Path(file_path).read_text()
    assert content in file_content, f"Content '{content}' not found in {file_path}"


def assert_performance_under_threshold(elapsed_time, threshold_seconds):
    """Assert that a command completed within performance threshold"""
    assert (
        elapsed_time < threshold_seconds
    ), f"Command took {elapsed_time}s, expected under {threshold_seconds}s"

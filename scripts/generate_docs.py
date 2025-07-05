#!/usr/bin/env python3
"""
Script to generate comprehensive documentation for Flow CLI
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import importlib.util
import inspect
import click

# Add flow_cli to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flow_cli.main import cli
from flow_cli.commands.doctor import doctor_command
from flow_cli.commands.analyze import analyze_command
from flow_cli.commands.android.main import android_group
from flow_cli.commands.ios.main import ios_group
from flow_cli.commands.generate.main import generate_group
from flow_cli.commands.deployment.main import deployment_group
from flow_cli.commands.config import config_command


def generate_command_docs(command, level: int = 1) -> str:
    """Generate documentation for a single command"""
    
    # Get command name and help
    name = command.name or "flow"
    help_text = command.help or "No description available"
    
    # Create markdown header
    header = "#" * level
    docs = f"{header} {name}\n\n"
    docs += f"{help_text}\n\n"
    
    # Get usage
    ctx = click.Context(command)
    usage = command.get_usage(ctx)
    docs += f"**Usage:**\n```bash\n{usage}\n```\n\n"
    
    # Get options
    if command.params:
        docs += "**Options:**\n\n"
        for param in command.params:
            if isinstance(param, click.Option):
                option_names = "/".join(param.opts)
                help_text = param.help or "No description"
                docs += f"- `{option_names}`: {help_text}\n"
        docs += "\n"
    
    # Get subcommands if it's a group
    if isinstance(command, click.Group):
        subcommands = command.list_commands(ctx)
        if subcommands:
            docs += "**Subcommands:**\n\n"
            for subcmd_name in subcommands:
                subcmd = command.get_command(ctx, subcmd_name)
                if subcmd:
                    subcmd_help = subcmd.help or "No description"
                    docs += f"- `{subcmd_name}`: {subcmd_help}\n"
            docs += "\n"
            
            # Generate docs for each subcommand
            for subcmd_name in subcommands:
                subcmd = command.get_command(ctx, subcmd_name)
                if subcmd:
                    docs += generate_command_docs(subcmd, level + 1)
    
    return docs


def generate_installation_docs() -> str:
    """Generate installation documentation"""
    
    return """# Installation

Flow CLI can be installed in multiple ways:

## Via PyPI (Recommended)

```bash
pip install flow-cli
```

## Via Binary (Linux/macOS)

```bash
curl -sSL https://github.com/flowstore/flow-cli/releases/latest/download/install.sh | bash
```

## Via Binary (Windows)

```powershell
Invoke-WebRequest -Uri https://github.com/flowstore/flow-cli/releases/latest/download/flow-cli-windows.exe -OutFile flow.exe
```

## From Source

```bash
git clone https://github.com/flowstore/flow-cli.git
cd flow-cli
pip install -e .
```

## Requirements

- Python 3.8 or higher
- Flutter SDK (for Flutter-specific features)
- Git (for version control features)

### Optional Requirements

- Android SDK (for Android development)
- Xcode (for iOS development on macOS)
- Ruby & Bundler (for Fastlane integration)

"""


def generate_getting_started_docs() -> str:
    """Generate getting started documentation"""
    
    return """# Getting Started

## Quick Start

1. **Install Flow CLI:**
   ```bash
   pip install flow-cli
   ```

2. **Verify installation:**
   ```bash
   flow --version
   ```

3. **Check your development environment:**
   ```bash
   flow doctor
   ```

4. **Navigate to your Flutter project:**
   ```bash
   cd /path/to/your/flutter/project
   ```

5. **Configure Flow CLI:**
   ```bash
   flow config --init
   ```

## Basic Workflow

### 1. Environment Setup

First, ensure your development environment is properly configured:

```bash
# Check environment health
flow doctor

# Configure SDKs and tools
flow config
```

### 2. Project Analysis

Analyze your Flutter project for issues:

```bash
# Analyze project
flow analyze

# Analyze specific files
flow analyze --path lib/main.dart
```

### 3. Asset Generation

Generate app icons and splash screens:

```bash
# Generate app icons
flow generate icons

# Generate splash screens
flow generate splash

# Generate for specific flavor
flow generate icons --flavor production
```

### 4. Building and Running

Build and run your app on different platforms:

```bash
# Android
flow android build
flow android run

# iOS (macOS only)
flow ios build
flow ios run

# Multi-flavor builds
flow android build --flavor development
```

### 5. Deployment

Set up automated deployment:

```bash
# Setup Fastlane
flow deployment setup

# Generate signing certificates
flow deployment keystore

# Create release builds
flow deployment release
```

## Configuration

Flow CLI stores configuration in `~/.flow-cli/config.yaml`. You can edit this file directly or use the interactive configuration:

```bash
flow config --init
```

### Key Configuration Options

- **Flutter SDK Path**: Path to your Flutter installation
- **Android SDK Path**: Path to your Android SDK
- **Default Flavor**: Default flavor for multi-flavor projects
- **Auto Pub Get**: Automatically run `flutter pub get` when needed

## Next Steps

- [Command Reference](commands.md) - Complete command documentation
- [Examples](examples.md) - Common usage examples
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

"""


def generate_examples_docs() -> str:
    """Generate examples documentation"""
    
    return """# Examples

## Common Workflows

### Setting Up a New Flutter Project

```bash
# Create new Flutter project
flutter create my_awesome_app
cd my_awesome_app

# Initialize Flow CLI
flow config --init

# Check environment
flow doctor

# Analyze project
flow analyze
```

### Multi-Flavor Development

```bash
# Create flavor configurations
mkdir -p flavors/development flavors/production

# Configure development flavor
echo '{
  "app_name": "My App Dev",
  "package_name": "com.example.myapp.dev",
  "primary_color": "#2196F3"
}' > flavors/development/config.json

# Generate assets for specific flavor
flow generate icons --flavor development
flow generate splash --flavor development

# Build for specific flavor
flow android build --flavor development
flow ios build --flavor development
```

### Automated Deployment Setup

```bash
# Setup Fastlane for deployment
flow deployment setup

# Generate signing certificates
flow deployment keystore --platform both

# Test build process
flow deployment release --build-only

# Deploy to stores
flow deployment release --track internal
```

### CI/CD Integration

```bash
# In your CI/CD pipeline
flow doctor --json > doctor-report.json
flow analyze --json > analysis-report.json
flow android build --flavor production
flow deployment release --platform android --track production
```

## Flavor-Specific Examples

### Development Flavor

```bash
# Quick development workflow
flow android build development
flow android run development --device emulator-5554

# Generate development assets
flow generate icons --flavor development
flow generate splash --flavor development --android-12
```

### Production Flavor

```bash
# Production release workflow
flow deployment keystore --platform both
flow deployment release --flavor production --track production

# Generate production assets
flow generate icons --flavor production --platforms android,ios
flow generate splash --flavor production --dark-mode
```

## Platform-Specific Examples

### Android Development

```bash
# List available devices
flow android devices

# Build APK
flow android build --output-format apk

# Install on specific device
flow android install --device RZ8M802WG5K

# Build for specific architecture
flow android build --target-platform android-arm64
```

### iOS Development (macOS only)

```bash
# List available simulators
flow ios devices

# Run on iOS simulator
flow ios run --device "iPhone 14 Pro"

# Build for device
flow ios build --codesign
```

## Asset Generation Examples

### App Icons

```bash
# Generate for all platforms
flow generate icons --source assets/icon.png

# Generate with custom sizes
flow generate icons --sizes 192,512,1024

# Generate adaptive icons (Android)
flow generate icons --adaptive --foreground assets/icon_fg.png --background "#FFFFFF"
```

### Splash Screens

```bash
# Generate basic splash screen
flow generate splash --image assets/splash.png

# Generate with brand colors
flow generate splash --background-color "#2196F3" --image-color "#FFFFFF"

# Generate Android 12+ splash screen
flow generate splash --android-12 --brand-image assets/brand.png
```

## Configuration Examples

### Global Configuration

```bash
# Set Flutter SDK path
flow config --set flutter.sdk_path=/usr/local/flutter

# Set default flavor
flow config --set general.default_flavor=development

# Enable verbose output
flow config --set general.verbose_output=true
```

### Project-Specific Configuration

```bash
# Initialize project configuration
flow config --init

# View current configuration
flow config --list

# Edit configuration interactively
flow config
```

## Error Handling Examples

### Common Issues

```bash
# Fix missing dependencies
flow doctor --fix

# Clean and rebuild
flow android clean
flow android build

# Regenerate assets
flow generate icons --force
flow generate splash --force
```

### Debugging

```bash
# Verbose output
flow --verbose android build

# JSON output for parsing
flow doctor --json
flow analyze --json

# Performance profiling
flow --profile android build
```

## Integration Examples

### With Git Hooks

```bash
# Pre-commit hook
#!/bin/bash
flow analyze --exit-code
flow generate icons --check
```

### With GitHub Actions

```yaml
- name: Run Flow CLI checks
  run: |
    flow doctor
    flow analyze
    flow android build --flavor production
```

### With VS Code

```json
{
  "tasks": [
    {
      "label": "Flow: Build Android",
      "type": "shell",
      "command": "flow android build",
      "group": "build"
    }
  ]
}
```

"""


def generate_troubleshooting_docs() -> str:
    """Generate troubleshooting documentation"""
    
    return """# Troubleshooting

## Common Issues

### Installation Issues

#### Python Version Error
```
ERROR: flow-cli requires Python 3.8 or higher
```

**Solution:**
```bash
# Check Python version
python --version

# Install Python 3.8+ or use pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

#### Permission Denied
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied
```

**Solution:**
```bash
# Install in user directory
pip install --user flow-cli

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install flow-cli
```

### Configuration Issues

#### Flutter SDK Not Found
```
ERROR: Flutter SDK not found in PATH
```

**Solution:**
```bash
# Add Flutter to PATH
export PATH="$PATH:/path/to/flutter/bin"

# Or configure in Flow CLI
flow config --set flutter.sdk_path=/path/to/flutter
```

#### Android SDK Not Found
```
ERROR: Android SDK not detected
```

**Solution:**
```bash
# Set ANDROID_HOME environment variable
export ANDROID_HOME=/path/to/android/sdk
export PATH="$PATH:$ANDROID_HOME/tools:$ANDROID_HOME/platform-tools"

# Or configure in Flow CLI
flow config --set android.sdk_path=/path/to/android/sdk
```

### Build Issues

#### Gradle Build Failed
```
ERROR: Gradle build failed with exit code 1
```

**Solutions:**
```bash
# Clean and rebuild
flow android clean
flutter clean
flutter pub get

# Check Gradle wrapper
cd android
./gradlew clean

# Update dependencies
flutter pub upgrade
```

#### iOS Build Failed (macOS)
```
ERROR: Xcode build failed
```

**Solutions:**
```bash
# Check Xcode installation
xcode-select --print-path

# Install Xcode command line tools
xcode-select --install

# Clean iOS build
cd ios
rm -rf build/
pod install --repo-update
```

### Asset Generation Issues

#### Icon Generation Failed
```
ERROR: Failed to process icon image
```

**Solutions:**
```bash
# Check image format and size
file assets/icon.png

# Use supported formats (PNG, JPG)
# Minimum size: 512x512px

# Install required dependencies
pip install Pillow

# Force regeneration
flow generate icons --force
```

#### Splash Screen Issues
```
ERROR: Flutter native splash configuration not found
```

**Solutions:**
```bash
# Add flutter_native_splash dependency
flutter pub add flutter_native_splash

# Run pub get
flutter pub get

# Regenerate splash screen
flow generate splash --force
```

### Deployment Issues

#### Fastlane Not Found
```
ERROR: Fastlane not installed
```

**Solutions:**
```bash
# Install Ruby and Bundler
brew install ruby
gem install bundler

# Install Fastlane
gem install fastlane

# Or use Bundler (recommended)
bundle install
```

#### Keystore Generation Failed
```
ERROR: keytool command not found
```

**Solutions:**
```bash
# Ensure Java is installed
java -version

# Add Java to PATH
export PATH="$PATH:$JAVA_HOME/bin"

# Or install Java
# macOS: brew install openjdk
# Ubuntu: sudo apt install openjdk-11-jdk
# Windows: Download from Oracle or OpenJDK
```

#### Signing Configuration Error
```
ERROR: keystore.properties not found
```

**Solutions:**
```bash
# Generate keystore first
flow deployment keystore --platform android

# Verify files exist
ls keys/
cat keys/keystore.properties

# Check build.gradle configuration
grep -A 10 "signingConfigs" android/app/build.gradle
```

### Performance Issues

#### Slow Command Execution
```
Commands taking too long to execute
```

**Solutions:**
```bash
# Run with performance profiling
flow --profile doctor

# Check system resources
# Ensure sufficient disk space and memory

# Use parallel execution when available
flow test --parallel

# Clear caches
flutter clean
flow android clean
```

#### Memory Issues
```
ERROR: Out of memory
```

**Solutions:**
```bash
# Increase JVM heap size
export GRADLE_OPTS="-Xmx2048m"

# Close other applications
# Use swap file if needed

# Build with reduced parallelism
flutter build apk --split-per-abi
```

## Platform-Specific Issues

### macOS

#### Xcode Issues
```bash
# Update Xcode
# Open App Store and update Xcode

# Accept Xcode license
sudo xcodebuild -license accept

# Reset Xcode settings
rm -rf ~/Library/Developer/Xcode/DerivedData
```

#### Ruby Version Issues
```bash
# Use rbenv for Ruby management
brew install rbenv
rbenv install 3.0.0
rbenv global 3.0.0
```

### Windows

#### Path Issues
```powershell
# Add to PATH in PowerShell
$env:PATH += ";C:\\path\\to\\flutter\\bin"

# Or add permanently via System Properties
```

#### Line Ending Issues
```bash
# Configure Git for Windows
git config --global core.autocrlf true
```

### Linux

#### Missing Dependencies
```bash
# Install required packages
sudo apt update
sudo apt install curl git unzip xz-utils zip libglu1-mesa

# For Android development
sudo apt install libc6:i386 libncurses5:i386 libstdc++6:i386 lib32z1 libbz2-1.0:i386
```

## Debug Mode

### Enable Verbose Logging

```bash
# Global verbose mode
flow --verbose doctor

# Command-specific verbose
flow android build --verbose

# Debug with stack trace
flow --debug deployment setup
```

### Generate Debug Reports

```bash
# System information
flow doctor --json > debug-report.json

# Configuration dump
flow config --list --json > config-report.json

# Performance profiling
flow --profile android build > performance-report.txt
```

## Getting Help

### Built-in Help

```bash
# General help
flow --help

# Command-specific help
flow android --help
flow deployment setup --help

# List all commands
flow --help | grep -E "^  [a-z]"
```

### Log Files

Flow CLI logs are stored in:
- **macOS/Linux**: `~/.flow-cli/logs/`
- **Windows**: `%USERPROFILE%\\.flow-cli\\logs\\`

```bash
# View recent logs
tail -f ~/.flow-cli/logs/flow-cli.log

# Search for errors
grep ERROR ~/.flow-cli/logs/flow-cli.log
```

### Reporting Issues

When reporting issues, please include:

1. Flow CLI version: `flow --version`
2. Python version: `python --version`
3. Operating system and version
4. Full command that failed
5. Complete error message
6. Debug report: `flow doctor --json`

**Submit issues at**: https://github.com/flowstore/flow-cli/issues

"""


def main():
    """Main function to generate all documentation"""
    
    docs_dir = Path("docs")
    docs_dir.mkdir(exist_ok=True)
    
    # Generate main command documentation
    print("Generating command documentation...")
    with open(docs_dir / "commands.md", "w") as f:
        f.write("# Command Reference\n\n")
        f.write("Complete reference for all Flow CLI commands.\n\n")
        f.write(generate_command_docs(cli))
    
    # Generate installation docs
    print("Generating installation documentation...")
    with open(docs_dir / "installation.md", "w") as f:
        f.write(generate_installation_docs())
    
    # Generate getting started docs
    print("Generating getting started documentation...")
    with open(docs_dir / "getting-started.md", "w") as f:
        f.write(generate_getting_started_docs())
    
    # Generate examples docs
    print("Generating examples documentation...")
    with open(docs_dir / "examples.md", "w") as f:
        f.write(generate_examples_docs())
    
    # Generate troubleshooting docs
    print("Generating troubleshooting documentation...")
    with open(docs_dir / "troubleshooting.md", "w") as f:
        f.write(generate_troubleshooting_docs())
    
    # Generate index
    print("Generating documentation index...")
    with open(docs_dir / "README.md", "w") as f:
        f.write("""# Flow CLI Documentation

Welcome to the Flow CLI documentation! This comprehensive guide will help you get the most out of Flow CLI, a beautiful and interactive command-line tool for Flutter developers.

## Table of Contents

- [Installation](installation.md) - How to install Flow CLI
- [Getting Started](getting-started.md) - Quick start guide and basic workflows
- [Command Reference](commands.md) - Complete command documentation
- [Examples](examples.md) - Common usage examples and workflows
- [Troubleshooting](troubleshooting.md) - Common issues and solutions

## Quick Links

- **GitHub Repository**: https://github.com/flowstore/flow-cli
- **Issue Tracker**: https://github.com/flowstore/flow-cli/issues
- **PyPI Package**: https://pypi.org/project/flow-cli/

## Overview

Flow CLI provides a comprehensive set of tools for Flutter development including:

- **Environment Checking**: Verify your development setup
- **Project Analysis**: Analyze Flutter projects for issues
- **Asset Generation**: Generate app icons and splash screens
- **Multi-Platform Building**: Build for Android and iOS
- **Automated Deployment**: Set up Fastlane and deploy to stores
- **Configuration Management**: Manage SDK paths and preferences

## Quick Start

```bash
# Install Flow CLI
pip install flow-cli

# Check your environment
flow doctor

# Navigate to your Flutter project
cd /path/to/your/flutter/project

# Configure Flow CLI
flow config --init

# Start building amazing apps!
flow android build
```

## Features

### 🩺 Doctor Command
Comprehensive environment health checks for Flutter, Android, and iOS development.

### 📊 Analysis Tools
Static analysis and linting for Flutter projects with detailed reporting.

### 🎨 Asset Generation
Automated generation of app icons and splash screens with multi-flavor support.

### 🤖 Android Tools
Complete Android development workflow including building, running, and device management.

### 🍎 iOS Tools (macOS)
iOS development tools including simulators, building, and deployment.

### 🚀 Deployment Automation
Fastlane integration with automated store deployment and certificate management.

### ⚙️ Configuration Management
Centralized configuration for SDKs, tools, and preferences.

## Contributing

We welcome contributions! Please see our [Contributing Guide](https://github.com/flowstore/flow-cli/blob/main/CONTRIBUTING.md) for details.

## License

Flow CLI is released under the MIT License. See [LICENSE](https://github.com/flowstore/flow-cli/blob/main/LICENSE) for details.
""")
    
    print("✅ Documentation generated successfully!")
    print(f"📁 Documentation files created in: {docs_dir.absolute()}")


if __name__ == "__main__":
    main()
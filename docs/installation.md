# Installation

Flow CLI can be installed in multiple ways to suit your development environment and preferences.

## Via PyPI (Recommended)

The easiest way to install Flow CLI is via PyPI using pip:

```bash
pip install flow-cli
```

### Verify Installation

```bash
flow --version
```

## Via Binary (Cross-Platform)

Pre-built binaries are available for major platforms:

### Linux/macOS

```bash
curl -sSL https://github.com/flowstore/flow-cli/releases/latest/download/install.sh | bash
```

### Windows

```powershell
Invoke-WebRequest -Uri https://github.com/flowstore/flow-cli/releases/latest/download/flow-cli-windows.exe -OutFile flow.exe
```

### Manual Binary Download

Download the appropriate binary for your platform from the [releases page](https://github.com/flowstore/flow-cli/releases):

- **Linux**: `flow-cli-linux`
- **macOS**: `flow-cli-macos`  
- **Windows**: `flow-cli-windows.exe`

Place the binary in your PATH and make it executable (Linux/macOS):

```bash
chmod +x flow-cli-*
sudo mv flow-cli-* /usr/local/bin/flow
```

## From Source

For development or if you want the latest features:

```bash
git clone https://github.com/flowstore/flow-cli.git
cd flow-cli
pip install -e .
```

### Development Installation

If you plan to contribute or modify Flow CLI:

```bash
git clone https://github.com/flowstore/flow-cli.git
cd flow-cli
pip install -e ".[dev]"
pre-commit install
```

## Virtual Environment (Recommended)

To avoid conflicts with system packages, use a virtual environment:

```bash
python -m venv flow-cli-env
source flow-cli-env/bin/activate  # On Windows: flow-cli-env\Scripts\activate
pip install flow-cli
```

## Docker

Run Flow CLI in a Docker container:

```bash
docker run --rm -v $(pwd):/workspace flowcli/flow-cli:latest doctor
```

## Package Managers

### Homebrew (macOS)

```bash
brew tap flowstore/tap
brew install flow-cli
```

### Chocolatey (Windows)

```bash
choco install flow-cli
```

### Snap (Linux)

```bash
sudo snap install flow-cli
```

## Requirements

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: 
  - Linux (Ubuntu 18.04+, CentOS 7+, or equivalent)
  - macOS 10.15+
  - Windows 10+

### Development Dependencies

Flow CLI works best when these tools are installed:

#### Required
- **Flutter SDK**: Latest stable version
- **Git**: For version control features

#### Optional (Platform-specific)
- **Android SDK**: For Android development
- **Java JDK**: 8 or higher (for Android builds)
- **Xcode**: Latest version (macOS only, for iOS development)
- **Ruby & Bundler**: For Fastlane integration
- **Node.js**: For certain build tools

## Post-Installation Setup

### 1. Verify Installation

```bash
flow --version
flow doctor
```

### 2. Configure Environment

```bash
flow config --init
```

This interactive wizard will help you configure:
- Flutter SDK path
- Android SDK path (if available)
- iOS/Xcode path (macOS only)
- Default preferences

### 3. Check Development Environment

```bash
flow doctor
```

This will verify that all required tools are properly installed and configured.

## Troubleshooting Installation

### Permission Issues

If you encounter permission errors:

```bash
# Use --user flag
pip install --user flow-cli

# Or create virtual environment
python -m venv venv
source venv/bin/activate
pip install flow-cli
```

### Python Version Issues

Check your Python version:

```bash
python --version
# Should be 3.8 or higher
```

If you have multiple Python versions, ensure you're using the correct one:

```bash
python3 -m pip install flow-cli
```

### PATH Issues

If `flow` command is not found after installation:

```bash
# Check if it's installed
pip show flow-cli

# Add to PATH (example for bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Use virtual environment
python -m venv flow-env
source flow-env/bin/activate
pip install flow-cli

# Or update pip
pip install --upgrade pip setuptools wheel
```

## Updating Flow CLI

### Via PyPI

```bash
pip install --upgrade flow-cli
```

### Via Binary

Download the latest binary from the releases page and replace the existing installation.

### From Source

```bash
git pull origin main
pip install -e .
```

## Uninstalling

### Via PyPI

```bash
pip uninstall flow-cli
```

### Binary Installation

Simply remove the binary file from your PATH.

### Clean Removal

To completely remove Flow CLI including configuration:

```bash
pip uninstall flow-cli
rm -rf ~/.flow-cli  # Remove configuration directory
```

## IDE Integration

### VS Code

Install the Flow CLI extension from the marketplace for enhanced integration.

### IntelliJ/Android Studio

Configure Flow CLI as an external tool for easy access from the IDE.

## Next Steps

After installation:

1. [Getting Started](getting-started.md) - Learn the basics
2. [Command Reference](commands.md) - Explore all commands
3. [Examples](examples.md) - See common workflows
4. [Configuration](configuration.md) - Customize Flow CLI
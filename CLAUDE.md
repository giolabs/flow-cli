# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Flow CLI** is a Python-based, interactive command-line tool designed to provide Flutter developers with a beautiful, user-friendly interface for building amazing apps. This open-source project emphasizes developer experience with pretty formatting, interactive menus, and comprehensive help systems.

## Architecture

### Core Design Principles
- **Python-based**: Built with Python for cross-platform compatibility and rich library ecosystem
- **Interactive & Pretty**: Beautiful CLI interface with colors, progress bars, and interactive menus
- **User-friendly**: Comprehensive help system and intuitive command structure
- **Platform-specific**: Separate Android and iOS command workflows
- **Open source**: Community-driven development with clear contribution guidelines

### Command Structure
```
flow <platform> <command> [options]
flow <global-command> [options]
```

## Core Commands

### Interactive Global Commands
```bash
flow doctor                    # Interactive environment health check with fixes
flow analyze                   # Interactive project analysis with suggestions
flow init                      # Interactive project setup wizard
flow config                    # Interactive configuration management
flow help                      # Interactive help system
```

### Asset Generation Commands
```bash
flow generate icons           # Interactive icon generation (flutter_launcher_icons)
flow generate splash          # Interactive splash screen generation (flutter_splash_screen)
flow generate assets          # Interactive asset optimization and generation
```

### Android Commands (Interactive)
```bash
flow android build            # Interactive build menu with flavor selection
flow android run              # Interactive device/emulator selection and run
flow android install         # Interactive APK installation with device selection
flow android flavors          # Pretty display of available Android flavors
flow android devices          # Interactive device management
```

### iOS Commands (Interactive)
```bash
flow ios build                # Interactive build menu with flavor selection
flow ios run                  # Interactive device/simulator selection and run
flow ios install             # Interactive IPA installation with device selection
flow ios flavors              # Pretty display of available iOS flavors
flow ios devices              # Interactive device management
```

## Development Setup

### Prerequisites
- Python 3.8+
- Flutter SDK
- Android Studio (for Android development)
- Xcode (for iOS development, macOS only)

### Installation
```bash
# Install from PyPI (when published)
pip install flow-cli

# Or install from source
git clone https://github.com/giolabs/flow-cli.git
cd flow-cli
pip install -e .
```

## Project Structure

```
flow-cli/
├── flow_cli/
│   ├── __init__.py
│   ├── main.py              # Entry point with rich CLI
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── android/         # Android-specific interactive commands
│   │   ├── ios/            # iOS-specific interactive commands
│   │   ├── doctor.py       # Interactive environment check
│   │   ├── analyze.py      # Interactive project analysis
│   │   ├── generate/       # Interactive asset generation
│   │   └── config.py       # Interactive configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── ui/             # UI components and styling
│   │   ├── config.py       # Configuration management
│   │   ├── flutter.py      # Flutter SDK interactions
│   │   ├── device.py       # Device management
│   │   └── utils.py        # Shared utilities
│   ├── assets/             # Templates, icons, and resources
│   └── help/               # Help documentation and tutorials
├── tests/
├── docs/
├── setup.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Key Features

### Beautiful Interactive Interface
- **Rich formatting**: Colors, tables, progress bars, and spinners
- **Interactive menus**: Arrow key navigation and selection
- **Smart prompts**: Context-aware input with validation
- **Progress tracking**: Real-time build progress with detailed steps

### Comprehensive Help System
- **Contextual help**: `--help` flag for every command with examples
- **Interactive tutorials**: Step-by-step guides for common workflows
- **Error explanations**: Detailed error messages with suggested fixes
- **Command discovery**: Interactive command exploration

### Multi-Flavor Support
- **Visual flavor selection**: Pretty table display of available flavors
- **Batch operations**: Select multiple flavors with checkboxes
- **Flavor validation**: Automatic detection and validation from `pubspec.yaml`
- **Configuration management**: Per-flavor settings and overrides

### Smart Device Management
- **Device detection**: Automatic discovery of connected devices/emulators
- **Device selection**: Interactive device picker with device details
- **Multi-device operations**: Install on multiple devices simultaneously
- **Device health checks**: Verify device compatibility and readiness

## Development Commands

### Testing
```bash
# Run all tests with pretty output
python -m pytest --tb=short --color=yes

# Run specific test modules
python -m pytest tests/test_android.py -v
python -m pytest tests/test_ios.py -v

# Run with coverage and pretty reporting
python -m pytest --cov=flow_cli --cov-report=html
```

### Code Quality
```bash
# Format code
black flow_cli/ tests/
isort flow_cli/ tests/

# Lint code
flake8 flow_cli/ tests/
pylint flow_cli/

# Type checking
mypy flow_cli/
```

## Dependencies

### Core Dependencies
- `click` - Command-line interface framework
- `rich` - Rich text, tables, progress bars, and beautiful formatting
- `inquirer` or `questionary` - Interactive prompts and menus
- `pyyaml` - YAML configuration parsing
- `requests` - HTTP requests for updates/downloads
- `colorama` - Cross-platform colored terminal text

### Development Dependencies
- `pytest` - Testing framework with rich output
- `black` - Code formatting
- `isort` - Import sorting
- `flake8` - Linting
- `mypy` - Type checking
- `pytest-cov` - Coverage reporting

## UI/UX Guidelines

### Visual Design
- **Consistent colors**: Use semantic colors (green for success, red for errors, blue for info)
- **Progressive disclosure**: Show basic options first, advanced options on request
- **Clear hierarchy**: Use headers, subheaders, and indentation effectively
- **Responsive layout**: Adapt to different terminal sizes

### Interactive Elements
- **Confirmation prompts**: For destructive operations
- **Smart defaults**: Pre-select the most likely option
- **Input validation**: Real-time validation with helpful error messages
- **Keyboard shortcuts**: Common shortcuts for power users

### Help and Documentation
- **Examples in help**: Show real-world usage examples
- **Progressive help**: Basic help by default, detailed help on request
- **Command suggestions**: Suggest similar commands on typos
- **Learning aids**: Tips and tricks for new users

## Error Handling

### User-Friendly Error Messages
- **Clear problem description**: What went wrong in plain language
- **Specific context**: Where and when the error occurred
- **Actionable solutions**: What the user can do to fix it
- **Documentation links**: Links to relevant documentation

### Graceful Degradation
- **Fallback modes**: Continue with limited functionality when possible
- **Recovery suggestions**: How to get back to a working state
- **Partial success reporting**: What succeeded before the error

## Contributing Guidelines

### Code Style
- Follow PEP 8 standards with rich formatting considerations
- Use type hints for all functions
- Write comprehensive docstrings with examples
- Maintain test coverage above 90%
- Document UI/UX decisions and patterns

### Adding New Interactive Commands
1. Create command module with rich formatting
2. Implement interactive prompts and menus
3. Add comprehensive help text with examples
4. Include progress indicators for long operations
5. Add unit tests and integration tests
6. Update documentation and help system

### UI Component Guidelines
- Use consistent color schemes and styling
- Implement responsive design for different terminal sizes
- Include accessibility considerations
- Test on different platforms (Windows, macOS, Linux)
- Document reusable UI components
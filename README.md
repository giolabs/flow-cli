# Flow CLI 🚀

A beautiful, interactive CLI tool for Flutter developers to build amazing apps with ease.

![Flow CLI Banner](https://img.shields.io/badge/Flow_CLI-v1.0.0-blue?style=for-the-badge&logo=flutter)

## ✨ Features

- 🎨 **Interactive Interface** - Beautiful, user-friendly CLI with rich formatting
- 🤖 **Android Support** - Build, run, and manage Android apps with multi-flavor support
- 🍎 **iOS Support** - iOS development tools (macOS only)
- 🎯 **Asset Generation** - Generate app icons, splash screens, and branding assets
- 🩺 **Environment Check** - Comprehensive development environment health checks
- 📊 **Project Analysis** - Analyze your Flutter project for issues and metrics
- 🔧 **Multi-flavor Support** - Advanced flavor management and configuration

## 🚀 Quick Start

### Installation

```bash
# Install from PyPI (when published)
pip install flow-cli

# Or install from source
git clone https://github.com/giolabs/flow-cli.git
cd flow-cli
pip install -e .
```

### Basic Usage

```bash
# Interactive mode
flow

# Check environment health
flow doctor

# Analyze your Flutter project
flow analyze

# Build Android APK
flow android build

# Generate branding assets
flow generate branding
```

## 📋 Commands

### Global Commands

| Command | Description |
|---------|-------------|
| `flow doctor` | Check development environment health |
| `flow analyze` | Analyze Flutter project for issues |
| `flow generate` | Asset generation tools |

### Android Commands

| Command | Description |
|---------|-------------|
| `flow android build` | Build Android APK/AAB |
| `flow android run` | Run on Android device/emulator |
| `flow android install` | Install APK on connected devices |
| `flow android devices` | Manage Android devices |
| `flow android flavors` | View available flavors |

### iOS Commands (macOS only)

| Command | Description |
|---------|-------------|
| `flow ios build` | Build iOS app |
| `flow ios run` | Run on iOS simulator/device |
| `flow ios devices` | Manage iOS devices and simulators |

### Asset Generation

| Command | Description |
|---------|-------------|
| `flow generate icons` | Generate app icons |
| `flow generate splash` | Generate splash screens |
| `flow generate branding` | Complete branding package |

## 🎨 Multi-Flavor Support

Flow CLI provides comprehensive support for Flutter flavors:

### Flavor Structure

```
assets/
├── configs/
│   ├── production/
│   │   ├── config.json
│   │   ├── icon.png
│   │   └── splash.png
│   └── development/
│       ├── config.json
│       ├── icon.png
│       └── splash.png
```

### Configuration Format

```json
{
  "appName": "MyApp Pro",
  "packageName": "com.company.myapp.pro",
  "mainColor": "#2196F3"
}
```

### Flavor Commands

```bash
# Build specific flavor client
flow android build --flavor client

# Generate branding for all flavors client
flow generate branding --all-flavors

# View flavor configurations
flow android flavors
```

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Flutter SDK
- Android SDK (for Android development)
- Xcode (for iOS development, macOS only)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/giolabs/flow-cli.git
cd flow-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=flow_cli --cov-report=html

# Run specific test module
pytest tests/test_android.py -v
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

## 📚 Documentation

### Environment Check

The `doctor` command performs comprehensive checks:

- ✅ Flutter SDK installation and version
- ✅ Python environment compatibility
- ✅ Android SDK and ADB availability
- ✅ iOS development tools (macOS only)
- ✅ Git installation
- ✅ Required Python packages

### Project Analysis

The `analyze` command provides detailed project insights:

- 🔍 Code quality analysis with Flutter analyze
- 📦 Dependencies analysis and recommendations
- 🏗️ Build artifacts analysis
- 🎨 Flavor configuration validation
- 📁 Project structure assessment

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Ensure all tests pass
6. Format your code (`black`, `isort`)
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Style

- Follow PEP 8 standards
- Use type hints for all functions
- Write comprehensive docstrings
- Maintain test coverage above 90%
- Use rich formatting for CLI output

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Flutter team for the amazing framework
- Rich library for beautiful CLI formatting
- Click for the excellent CLI framework
- All contributors and the Flutter community

## 📞 Support

- 🐛 [Report a bug](https://github.com/giolabs/flow-cli/issues)
- 💡 [Request a feature](https://github.com/giolabs/flow-cli/issues)
- 📖 [Documentation](https://github.com/giolabs/flow-cli#readme)
- 💬 [Discussions](https://github.com/giolabs/flow-cli/discussions)

---

Made with ❤️ by [GioLabs](https://github.com/giolabs) for the Flutter community.
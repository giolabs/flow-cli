"""
Configuration command - Manage Flow CLI global configuration
"""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

import click
import inquirer
import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()

# Configuration file paths
CONFIG_DIR = Path.home() / ".flow-cli"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULT_CONFIG = {
    "flutter": {"sdk_path": "", "channel": "stable"},
    "android": {"sdk_path": "", "build_tools_version": ""},
    "ios": {"xcode_path": "", "team_id": ""},
    "general": {
        "default_flavor": "",
        "auto_pub_get": True,
        "verbose_output": False,
        "color_output": True,
    },
    "aliases": {},
    "recent_projects": [],
}


@click.command()
@click.option("--set", "set_value", help="Set configuration value (key=value)")
@click.option("--get", "get_key", help="Get configuration value")
@click.option("--list", "list_config", is_flag=True, help="List all configuration")
@click.option("--init", is_flag=True, help="Initialize configuration with setup wizard")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config_command(
    set_value: Optional[str], get_key: Optional[str], list_config: bool, init: bool, reset: bool
) -> None:
    """
    ⚙️ Manage Flow CLI global configuration

    Configure Flutter SDK paths, default settings, and preferences.
    Supports interactive setup wizard and direct value modification.
    """

    show_section_header("Flow CLI Configuration", "⚙️")

    # Ensure config directory exists
    ensure_config_dir()

    # Handle specific actions
    if init:
        run_config_wizard()
    elif reset:
        reset_configuration()
    elif set_value:
        set_config_value(set_value)
    elif get_key:
        get_config_value(get_key)
    elif list_config:
        list_configuration()
    else:
        # Interactive configuration menu
        show_config_menu()


def ensure_config_dir() -> None:
    """Ensure configuration directory exists"""
    CONFIG_DIR.mkdir(exist_ok=True)

    # Create default config if it doesn't exist
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        console.print(f"[green]Created default configuration at {CONFIG_FILE}[/green]")


def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}

        # Merge with defaults to ensure all keys exist
        merged_config = DEFAULT_CONFIG.copy()
        merged_config.update(config)
        return merged_config

    except Exception as e:
        show_error(f"Failed to load configuration: {e}")
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> None:
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
    except Exception as e:
        show_error(f"Failed to save configuration: {e}")


def run_config_wizard() -> None:
    """Run interactive configuration wizard"""

    console.print("[cyan]🧙 Configuration Setup Wizard[/cyan]\n")
    console.print("This wizard will help you configure Flow CLI for optimal Flutter development.")
    console.print()

    config = load_config()

    # Flutter SDK Configuration
    config["flutter"] = configure_flutter_sdk(config.get("flutter", {}))

    # Android SDK Configuration
    config["android"] = configure_android_sdk(config.get("android", {}))

    # iOS Configuration (macOS only)
    import platform

    if platform.system() == "Darwin":
        config["ios"] = configure_ios_settings(config.get("ios", {}))

    # General Settings
    config["general"] = configure_general_settings(config.get("general", {}))

    # Save configuration
    save_config(config)

    show_success("Configuration wizard completed!")
    console.print(f"\n[dim]Configuration saved to: {CONFIG_FILE}[/dim]")

    # Verify configuration
    verify_configuration(config)


def configure_flutter_sdk(flutter_config: Dict) -> Dict:
    """Configure Flutter SDK settings"""

    console.print("[bold cyan]📱 Flutter SDK Configuration[/bold cyan]")

    # Auto-detect Flutter SDK
    detected_flutter = detect_flutter_sdk()
    current_path = flutter_config.get("sdk_path", "")

    if detected_flutter:
        console.print(f"[green]✅ Flutter SDK detected: {detected_flutter}[/green]")
        default_path = detected_flutter
    else:
        console.print("[yellow]⚠️  Flutter SDK not found in PATH[/yellow]")
        default_path = current_path or "/usr/local/flutter"

    try:
        questions = [
            inquirer.Text("sdk_path", message="Flutter SDK path", default=default_path),
            inquirer.List(
                "channel",
                message="Preferred Flutter channel",
                choices=["stable", "beta", "dev", "master"],
                default=flutter_config.get("channel", "stable"),
            ),
        ]

        answers = inquirer.prompt(questions)
        if answers:
            flutter_config.update(answers)

            # Validate Flutter SDK
            if validate_flutter_sdk(answers["sdk_path"]):
                show_success("Flutter SDK configuration validated")
            else:
                show_warning("Flutter SDK path may be invalid")

    except KeyboardInterrupt:
        pass

    return flutter_config


def configure_android_sdk(android_config: Dict) -> Dict:
    """Configure Android SDK settings"""

    console.print("\n[bold cyan]🤖 Android SDK Configuration[/bold cyan]")

    # Auto-detect Android SDK
    detected_android = detect_android_sdk()
    current_path = android_config.get("sdk_path", "")

    if detected_android:
        console.print(f"[green]✅ Android SDK detected: {detected_android}[/green]")
        default_path = detected_android
    else:
        console.print("[yellow]⚠️  Android SDK not found[/yellow]")
        default_path = current_path or str(Path.home() / "Library/Android/sdk")

    try:
        questions = [inquirer.Text("sdk_path", message="Android SDK path", default=default_path)]

        answers = inquirer.prompt(questions)
        if answers:
            android_config.update(answers)

            # Validate Android SDK
            if validate_android_sdk(answers["sdk_path"]):
                show_success("Android SDK configuration validated")
            else:
                show_warning("Android SDK path may be invalid")

    except KeyboardInterrupt:
        pass

    return android_config


def configure_ios_settings(ios_config: Dict) -> Dict:
    """Configure iOS development settings (macOS only)"""

    console.print("\n[bold cyan]🍎 iOS Development Configuration[/bold cyan]")

    # Auto-detect Xcode
    detected_xcode = detect_xcode_path()
    current_path = ios_config.get("xcode_path", "")

    if detected_xcode:
        console.print(f"[green]✅ Xcode detected: {detected_xcode}[/green]")
        default_path = detected_xcode
    else:
        console.print("[yellow]⚠️  Xcode not found[/yellow]")
        default_path = current_path or "/Applications/Xcode.app"

    try:
        questions = [
            inquirer.Text("xcode_path", message="Xcode.app path", default=default_path),
            inquirer.Text(
                "team_id",
                message="Apple Developer Team ID (optional)",
                default=ios_config.get("team_id", ""),
            ),
        ]

        answers = inquirer.prompt(questions)
        if answers:
            ios_config.update(answers)

            # Validate Xcode
            if validate_xcode(answers["xcode_path"]):
                show_success("Xcode configuration validated")
            else:
                show_warning("Xcode path may be invalid")

    except KeyboardInterrupt:
        pass

    return ios_config


def configure_general_settings(general_config: Dict) -> Dict:
    """Configure general Flow CLI settings"""

    console.print("\n[bold cyan]⚙️ General Settings[/bold cyan]")

    try:
        questions = [
            inquirer.Text(
                "default_flavor",
                message="Default flavor (leave empty for none)",
                default=general_config.get("default_flavor", ""),
            ),
            inquirer.Confirm(
                "auto_pub_get",
                message="Automatically run 'flutter pub get' when needed?",
                default=general_config.get("auto_pub_get", True),
            ),
            inquirer.Confirm(
                "verbose_output",
                message="Enable verbose output by default?",
                default=general_config.get("verbose_output", False),
            ),
            inquirer.Confirm(
                "color_output",
                message="Enable colored output?",
                default=general_config.get("color_output", True),
            ),
        ]

        answers = inquirer.prompt(questions)
        if answers:
            general_config.update(answers)

    except KeyboardInterrupt:
        pass

    return general_config


def detect_flutter_sdk() -> Optional[str]:
    """Auto-detect Flutter SDK path"""
    try:
        result = subprocess.run(["which", "flutter"], capture_output=True, text=True)
        if result.returncode == 0:
            flutter_bin = Path(result.stdout.strip())
            flutter_sdk = flutter_bin.parent.parent
            return str(flutter_sdk)
    except Exception:
        pass

    # Check common locations
    common_paths = [
        Path.home() / "flutter",
        Path.home() / "development/flutter",
        Path("/usr/local/flutter"),
        Path("/opt/flutter"),
    ]

    for path in common_paths:
        if path.exists() and (path / "bin/flutter").exists():
            return str(path)

    return None


def detect_android_sdk() -> Optional[str]:
    """Auto-detect Android SDK path"""
    import os

    # Check environment variable
    android_home = os.environ.get("ANDROID_HOME")
    if android_home and Path(android_home).exists():
        return android_home

    # Check common locations
    common_paths = [
        Path.home() / "Library/Android/sdk",  # macOS
        Path.home() / "Android/Sdk",  # Linux
        Path.home() / "AppData/Local/Android/Sdk",  # Windows
    ]

    for path in common_paths:
        if path.exists() and (path / "platform-tools/adb").exists():
            return str(path)

    return None


def detect_xcode_path() -> Optional[str]:
    """Auto-detect Xcode path (macOS only)"""
    try:
        result = subprocess.run(["xcode-select", "-p"], capture_output=True, text=True)
        if result.returncode == 0:
            developer_dir = Path(result.stdout.strip())
            xcode_app = developer_dir.parent
            if xcode_app.name.endswith(".app"):
                return str(xcode_app)
    except Exception:
        pass

    # Check default location
    default_xcode = Path("/Applications/Xcode.app")
    if default_xcode.exists():
        return str(default_xcode)

    return None


def validate_flutter_sdk(path: str) -> bool:
    """Validate Flutter SDK path"""
    flutter_path = Path(path)
    return flutter_path.exists() and (flutter_path / "bin/flutter").exists()


def validate_android_sdk(path: str) -> bool:
    """Validate Android SDK path"""
    android_path = Path(path)
    return android_path.exists() and (android_path / "platform-tools").exists()


def validate_xcode(path: str) -> bool:
    """Validate Xcode path"""
    xcode_path = Path(path)
    return (
        xcode_path.exists()
        and xcode_path.name.endswith(".app")
        and (xcode_path / "Contents/Developer").exists()
    )


def verify_configuration(config: Dict) -> None:
    """Verify configuration settings"""

    console.print("\n[cyan]🔍 Verifying Configuration...[/cyan]")

    issues = []

    # Check Flutter SDK
    flutter_path = config.get("flutter", {}).get("sdk_path", "")
    if flutter_path and not validate_flutter_sdk(flutter_path):
        issues.append("Flutter SDK path is invalid")

    # Check Android SDK
    android_path = config.get("android", {}).get("sdk_path", "")
    if android_path and not validate_android_sdk(android_path):
        issues.append("Android SDK path is invalid")

    # Check Xcode (macOS only)
    import platform

    if platform.system() == "Darwin":
        xcode_path = config.get("ios", {}).get("xcode_path", "")
        if xcode_path and not validate_xcode(xcode_path):
            issues.append("Xcode path is invalid")

    if issues:
        console.print("[yellow]⚠️  Configuration issues found:[/yellow]")
        for issue in issues:
            console.print(f"  • {issue}")
    else:
        console.print("[green]✅ Configuration looks good![/green]")


def set_config_value(key_value: str) -> None:
    """Set a configuration value"""

    if "=" not in key_value:
        show_error("Invalid format. Use: key=value")
        return

    key, value = key_value.split("=", 1)

    config = load_config()

    # Parse nested keys (e.g., flutter.sdk_path)
    keys = key.split(".")
    current = config

    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # Convert value type
    converted_value: Any = value
    if value.lower() in ["true", "false"]:
        converted_value = value.lower() == "true"
    elif value.isdigit():
        converted_value = int(value)
    else:
        converted_value = value

    current[keys[-1]] = converted_value
    save_config(config)

    show_success(f"Set {key} = {value}")


def get_config_value(key: str) -> None:
    """Get a configuration value"""

    config = load_config()

    # Parse nested keys
    keys = key.split(".")
    current = config

    try:
        for k in keys:
            current = current[k]

        console.print(f"[cyan]{key}[/cyan] = [bright_white]{current}[/bright_white]")

    except KeyError:
        show_error(f"Configuration key '{key}' not found")


def list_configuration() -> None:
    """List all configuration values"""

    config = load_config()

    table = Table(title="⚙️ Flow CLI Configuration", box=box.ROUNDED)
    table.add_column("Setting", style="cyan", no_wrap=True)
    table.add_column("Value", style="bright_white")
    table.add_column("Status", style="bold")

    def add_config_section(section_name: str, section_data: Dict, prefix: str = "") -> None:
        for key, value in section_data.items():
            if isinstance(value, dict):
                add_config_section(f"{section_name}.{key}", value, prefix)
            else:
                full_key = f"{prefix}{section_name}.{key}" if prefix else f"{section_name}.{key}"

                # Determine status
                if key.endswith("_path") and value:
                    path = Path(value)
                    status = "[green]✅ Valid[/green]" if path.exists() else "[red]❌ Invalid[/red]"
                elif value:
                    status = "[green]✅ Set[/green]"
                else:
                    status = "[dim]➖ Empty[/dim]"

                # Format value
                display_value = str(value) if value else "[dim]<empty>[/dim]"
                if len(display_value) > 50:
                    display_value = display_value[:47] + "..."

                table.add_row(full_key, display_value, status)

    for section, data in config.items():
        if isinstance(data, dict):
            add_config_section(section, data)
        else:
            status = "[green]✅ Set[/green]" if data else "[dim]➖ Empty[/dim]"
            table.add_row(section, str(data), status)

    console.print(table)

    console.print(f"\n[dim]Configuration file: {CONFIG_FILE}[/dim]")


def reset_configuration() -> None:
    """Reset configuration to defaults"""

    try:
        confirm = inquirer.confirm(
            "Are you sure you want to reset all configuration to defaults?", default=False
        )

        if confirm:
            save_config(DEFAULT_CONFIG)
            show_success("Configuration reset to defaults")
        else:
            console.print("[dim]Reset cancelled[/dim]")

    except KeyboardInterrupt:
        console.print("\n[dim]Reset cancelled[/dim]")


def show_config_menu() -> None:
    """Show interactive configuration menu"""

    choices = [
        "🧙 Setup Wizard - Complete configuration setup",
        "📋 List Settings - View all configuration values",
        "✏️  Edit Setting - Modify specific setting",
        "🔄 Reset Config - Reset to defaults",
        "📁 Open Config File - Open configuration in editor",
        "🔙 Back to main menu",
    ]

    try:
        questions = [
            inquirer.List(
                "action", message="Select configuration action:", choices=choices, carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return

        action = answers["action"]

        if action.startswith("🧙"):
            run_config_wizard()
        elif action.startswith("📋"):
            list_configuration()
        elif action.startswith("✏️"):
            edit_setting_interactive()
        elif action.startswith("🔄"):
            reset_configuration()
        elif action.startswith("📁"):
            open_config_file()
        elif action.startswith("🔙"):
            return

    except KeyboardInterrupt:
        console.print("\n[dim]Configuration cancelled[/dim]")


def edit_setting_interactive() -> None:
    """Interactive setting editor"""

    config = load_config()

    # Build list of all settings
    settings = []

    def collect_settings(data: Dict, prefix: str = "") -> None:
        for key, value in data.items():
            if isinstance(value, dict):
                collect_settings(value, f"{prefix}{key}.")
            else:
                settings.append(f"{prefix}{key}")

    collect_settings(config)

    try:
        questions = [
            inquirer.List("setting", message="Select setting to edit:", choices=settings),
            inquirer.Text("value", message="Enter new value:"),
        ]

        answers = inquirer.prompt(questions)
        if answers:
            set_config_value(f"{answers['setting']}={answers['value']}")

    except KeyboardInterrupt:
        pass


def open_config_file() -> None:
    """Open configuration file in default editor"""

    try:
        import os

        # Try different editors
        editors = ["code", "subl", "atom", "nano", "vim"]

        for editor in editors:
            try:
                subprocess.run([editor, str(CONFIG_FILE)], check=True)
                console.print(f"[green]Opened configuration in {editor}[/green]")
                return
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue

        # Fallback to system default
        if os.name == "darwin":  # macOS
            subprocess.run(["open", str(CONFIG_FILE)])
        elif os.name == "nt":  # Windows
            subprocess.run(["start", str(CONFIG_FILE)], shell=True)
        else:  # Linux
            subprocess.run(["xdg-open", str(CONFIG_FILE)])

        console.print("[green]Opened configuration file[/green]")

    except Exception as e:
        show_error(f"Failed to open configuration file: {e}")
        console.print(f"[dim]Configuration file location: {CONFIG_FILE}[/dim]")

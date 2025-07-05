"""
Doctor command - Check development environment health
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()


@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
def doctor_command(verbose: bool) -> None:
    """
    🩺 Check development environment health

    Verifies that all required tools are installed and configured correctly
    for Flutter development with Flow CLI.
    """
    show_section_header("Environment Health Check", "🩺")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        # Collect all checks
        checks = [
            ("Checking Flutter SDK...", check_flutter),
            ("Checking Python environment...", check_python),
            ("Checking Android SDK...", check_android),
            ("Checking iOS development (macOS only)...", check_ios),
            ("Checking Git...", check_git),
            ("Checking required Python packages...", check_python_packages),
        ]

        results = []

        for description, check_func in checks:
            task = progress.add_task(description, total=None)
            result = check_func(verbose)
            results.append(result)
            progress.remove_task(task)

    # Display results
    display_results(results, verbose)


def check_flutter(verbose: bool) -> Tuple[str, str, str, str]:
    """Check Flutter SDK installation"""
    try:
        result = subprocess.run(
            ["flutter", "--version"], capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version_line = result.stdout.strip().split("\n")[0]
            # Extract version like "Flutter 3.16.0"
            parts = version_line.split()
            version = parts[1] if len(parts) >= 2 else "Unknown"

            # Check Flutter doctor
            doctor_result = subprocess.run(
                ["flutter", "doctor", "--no-version-check"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if "No issues found!" in doctor_result.stdout:
                status = "✅"
                message = f"Flutter {version}"
                details = "All Flutter dependencies are satisfied"
            else:
                status = "⚠️"
                message = f"Flutter {version} (with issues)"
                details = "Run 'flutter doctor' for more details"

            return ("Flutter SDK", status, message, details)
        else:
            return (
                "Flutter SDK",
                "❌",
                "Not found",
                "Install Flutter SDK from https://flutter.dev",
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return (
            "Flutter SDK",
            "❌",
            "Not found or not responding",
            "Install Flutter SDK from https://flutter.dev",
        )


def check_python(verbose: bool) -> Tuple[str, str, str, str]:
    """Check Python installation"""
    try:
        version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 8):
            return ("Python", "✅", f"Python {version}", "Python version is compatible")
        else:
            return ("Python", "⚠️", f"Python {version}", "Python 3.8+ recommended")
    except Exception:
        return ("Python", "❌", "Error checking version", "Unable to determine Python version")


def check_android(verbose: bool) -> Tuple[str, str, str, str]:
    """Check Android SDK and tools"""
    try:
        # Check if Android SDK is available
        android_home = Path.home() / "Library" / "Android" / "sdk"  # macOS default
        if not android_home.exists():
            android_home = Path.home() / "Android" / "Sdk"  # Linux default

        if not android_home.exists():
            # Try environment variable
            import os

            android_home_env = os.environ.get("ANDROID_HOME")
            if android_home_env:
                android_home = Path(android_home_env)

        if android_home.exists():
            # Check for adb
            adb_path = android_home / "platform-tools" / "adb"
            if not adb_path.exists():
                adb_path = android_home / "platform-tools" / "adb.exe"  # Windows

            if adb_path.exists():
                # Check adb version
                result = subprocess.run(
                    [str(adb_path), "version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    return ("Android SDK", "✅", "Android SDK found", f"SDK at {android_home}")
                else:
                    return (
                        "Android SDK",
                        "⚠️",
                        "SDK found, ADB issues",
                        "ADB may not be working properly",
                    )
            else:
                return ("Android SDK", "⚠️", "SDK found, no ADB", "Platform tools may be missing")
        else:
            return ("Android SDK", "❌", "Not found", "Install Android SDK via Android Studio")
    except Exception as e:
        return ("Android SDK", "❌", "Error checking", f"Error: {str(e)}")


def check_ios(verbose: bool) -> Tuple[str, str, str, str]:
    """Check iOS development tools (macOS only)"""
    import platform

    if platform.system() != "Darwin":
        return ("iOS Development", "ℹ️", "Not applicable", "iOS development requires macOS")

    try:
        # Check Xcode
        result = subprocess.run(["xcrun", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # Check for iOS simulators
            sim_result = subprocess.run(
                ["xcrun", "simctl", "list", "devices"], capture_output=True, text=True, timeout=10
            )
            if "iOS" in sim_result.stdout:
                return ("iOS Development", "✅", "Xcode available", "iOS simulators found")
            else:
                return ("iOS Development", "⚠️", "Xcode available", "No iOS simulators found")
        else:
            return ("iOS Development", "❌", "Xcode not found", "Install Xcode from Mac App Store")
    except Exception:
        return (
            "iOS Development",
            "❌",
            "Error checking Xcode",
            "Unable to verify Xcode installation",
        )


def check_git(verbose: bool) -> Tuple[str, str, str, str]:
    """Check Git installation"""
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            version = result.stdout.strip().split()[-1]
            return ("Git", "✅", f"Git {version}", "Git is available")
        else:
            return ("Git", "❌", "Not found", "Install Git from https://git-scm.com")
    except FileNotFoundError:
        return ("Git", "❌", "Not found", "Install Git from https://git-scm.com")


def check_python_packages(verbose: bool) -> Tuple[str, str, str, str]:
    """Check required Python packages"""
    required_packages = [
        "click",
        "rich",
        "inquirer",
        "pyyaml",
        "requests",
        "colorama",
        "Pillow",
        "ruamel.yaml",
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if not missing_packages:
        return (
            "Python Packages",
            "✅",
            "All packages available",
            f"All {len(required_packages)} packages found",
        )
    else:
        missing_str = ", ".join(missing_packages)
        return (
            "Python Packages",
            "⚠️",
            f"{len(missing_packages)} missing",
            f"Missing: {missing_str}",
        )


def display_results(results: List[Tuple[str, str, str, str]], verbose: bool) -> None:
    """Display check results in a nice table"""

    table = Table(title="🩺 Environment Health Check Results", box=box.ROUNDED)
    table.add_column("Component", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold", no_wrap=True)
    table.add_column("Version/Info", style="bright_white")
    if verbose:
        table.add_column("Details", style="dim")

    success_count = 0
    warning_count = 0
    error_count = 0

    for component, status, info, details in results:
        if status == "✅":
            success_count += 1
            style = "green"
        elif status == "⚠️":
            warning_count += 1
            style = "yellow"
        elif status == "❌":
            error_count += 1
            style = "red"
        else:  # ℹ️
            style = "blue"

        if verbose:
            table.add_row(component, status, info, details, style=style)
        else:
            table.add_row(component, status, info, style=style)

    console.print(table)

    # Summary
    total = len(results)
    if error_count == 0 and warning_count == 0:
        summary_style = "green"
        summary_icon = "🎉"
        summary_text = "Perfect! Your development environment is ready!"
    elif error_count == 0:
        summary_style = "yellow"
        summary_icon = "⚠️"
        summary_text = f"Good! {warning_count} minor issues found."
    else:
        summary_style = "red"
        summary_icon = "❌"
        summary_text = f"Issues found: {error_count} errors, {warning_count} warnings."

    summary = f"[{summary_style}]{summary_icon} {summary_text}[/{summary_style}]\n\n"
    summary += f"✅ {success_count} OK  ⚠️ {warning_count} Warnings  ❌ {error_count} Errors"

    summary_panel = Panel(summary, title="📋 Summary", border_style=summary_style, box=box.ROUNDED)
    console.print(summary_panel)

    # Show recommendations
    if error_count > 0 or warning_count > 0:
        show_recommendations(results)


def show_recommendations(results: List[Tuple[str, str, str, str]]) -> None:
    """Show recommendations for fixing issues"""
    recommendations = []

    for component, status, info, details in results:
        if status in ["❌", "⚠️"]:
            recommendations.append(f"• {component}: {details}")

    if recommendations:
        rec_text = "\n".join(recommendations)
        rec_panel = Panel(
            rec_text, title="💡 Recommendations", border_style="blue", box=box.ROUNDED
        )
        console.print(rec_panel)

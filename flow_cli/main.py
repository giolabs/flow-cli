#!/usr/bin/env python3
"""
Flow CLI - Main entry point
A beautiful, interactive CLI tool for Flutter developers
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

from flow_cli.core.ui.banner import show_banner
from flow_cli.core.flutter import FlutterProject
from flow_cli.commands.doctor import doctor_command
from flow_cli.commands.analyze import analyze_command
from flow_cli.commands.android.main import android_group
from flow_cli.commands.ios.main import ios_group
from flow_cli.commands.generate.main import generate_group
from flow_cli.commands.config import config_command
from flow_cli.commands.deployment.main import deployment_group

console = Console()


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, version: bool, verbose: bool) -> None:
    """
    🚀 Flow CLI - A beautiful, interactive CLI tool for Flutter developers

    Build amazing Flutter apps with ease using our comprehensive set of tools
    for Android, iOS, and multi-flavor development.
    """
    if ctx.obj is None:
        ctx.obj = {}

    ctx.obj["verbose"] = verbose

    if version:
        show_version()
        return

    if ctx.invoked_subcommand is None:
        show_interactive_menu(ctx)


def show_version() -> None:
    """Show version information with beautiful formatting"""
    from flow_cli import __version__, __author__

    version_panel = Panel(
        f"[bold cyan]Flow CLI[/bold cyan] v{__version__}\n"
        f"[dim]by {__author__}[/dim]\n\n"
        f"[green]A beautiful, interactive CLI tool for Flutter developers[/green]",
        title="🚀 Version Information",
        border_style="cyan",
        box=box.ROUNDED,
    )
    console.print(version_panel)


def show_interactive_menu(ctx: click.Context) -> None:
    """Show interactive main menu"""
    show_banner()

    # Check if we're in a Flutter project
    try:
        project = FlutterProject.find_project()
        if project:
            show_project_info(project)
        else:
            show_no_project_warning()
    except Exception:
        show_no_project_warning()

    # Show main menu
    show_main_menu(ctx)


def show_project_info(project: FlutterProject) -> None:
    """Show current Flutter project information"""
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="bright_white")

    table.add_row("📱 Project", project.name)
    table.add_row("📁 Path", str(project.path.relative_to(Path.cwd())))
    table.add_row("🦋 Flutter", project.flutter_version or "Unknown")

    if project.flavors:
        flavors_text = ", ".join(project.flavors)
        table.add_row("🎨 Flavors", flavors_text)

    project_panel = Panel(table, title="📋 Current Project", border_style="green", box=box.ROUNDED)
    console.print(project_panel)


def show_no_project_warning() -> None:
    """Show warning when not in a Flutter project"""
    warning_panel = Panel(
        "[yellow]⚠️  Not in a Flutter project directory[/yellow]\n\n"
        "Some commands require a Flutter project. Navigate to a Flutter\n"
        "project directory or use [cyan]flutter create[/cyan] to create a new one.",
        title="🔍 Project Detection",
        border_style="yellow",
        box=box.ROUNDED,
    )
    console.print(warning_panel)


def show_main_menu(ctx: click.Context) -> None:
    """Show main menu with available commands"""
    import inquirer

    choices = [
        "🩺 Doctor - Check development environment",
        "📊 Analyze - Analyze Flutter project",
        "🤖 Android - Android development tools",
        "🍎 iOS - iOS development tools",
        "🎨 Generate - Asset generation tools",
        "🚀 Deployment - Release and deployment tools",
        "⚙️  Configure - Setup and configuration",
        "ℹ️  Help - Show detailed help",
        "🚪 Exit",
    ]

    try:
        questions = [
            inquirer.List(
                "action", message="What would you like to do?", choices=choices, carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            console.print("[dim]Goodbye! 👋[/dim]")
            sys.exit(0)

        action = answers["action"]

        # Route to appropriate command
        if action.startswith("🩺"):
            ctx.invoke(doctor_command)
        elif action.startswith("📊"):
            ctx.invoke(analyze_command)
        elif action.startswith("🤖"):
            ctx.invoke(android_group)
        elif action.startswith("🍎"):
            ctx.invoke(ios_group)
        elif action.startswith("🎨"):
            ctx.invoke(generate_group)
        elif action.startswith("🚀"):
            ctx.invoke(deployment_group)
        elif action.startswith("⚙️"):
            ctx.invoke(config_command)
        elif action.startswith("ℹ️"):
            show_help()
        elif action.startswith("🚪"):
            console.print("[dim]Goodbye! 👋[/dim]")
            sys.exit(0)

    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye! 👋[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def show_config_menu(ctx: click.Context) -> None:
    """Show configuration menu - deprecated, now handled by config_command"""
    ctx.invoke(config_command)


def show_help() -> None:
    """Show detailed help information"""
    help_text = Text()
    help_text.append("Flow CLI Commands\n\n", style="bold cyan")
    help_text.append("Global Commands:\n", style="bold")
    help_text.append("  flow doctor          Check development environment health\n")
    help_text.append("  flow analyze         Analyze Flutter project for issues\n")
    help_text.append("  flow generate        Generate app assets (icons, splash screens)\n\n")

    help_text.append("Platform Commands:\n", style="bold")
    help_text.append("  flow android         Android development tools\n")
    help_text.append("  flow ios             iOS development tools\n\n")

    help_text.append("Examples:\n", style="bold")
    help_text.append("  flow android build flowstore    Build Android APK for flowstore flavor\n")
    help_text.append("  flow ios run                     Run iOS app on simulator\n")
    help_text.append("  flow generate icons              Generate app icons\n")

    help_panel = Panel(help_text, title="📚 Help", border_style="blue", box=box.ROUNDED)
    console.print(help_panel)


# Add subcommands
cli.add_command(doctor_command, name="doctor")
cli.add_command(analyze_command, name="analyze")
cli.add_command(android_group, name="android")
cli.add_command(ios_group, name="ios")
cli.add_command(generate_group, name="generate")
cli.add_command(deployment_group, name="deployment")
cli.add_command(config_command, name="config")


def main() -> None:
    """Main entry point"""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[dim]Goodbye! 👋[/dim]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

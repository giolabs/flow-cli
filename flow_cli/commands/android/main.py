"""
Android commands group - Android development tools
"""

import click
from typing import Optional

from flow_cli.commands.android.build import build_command
from flow_cli.commands.android.run import run_command
from flow_cli.commands.android.install import install_command
from flow_cli.commands.android.devices import devices_command
from flow_cli.commands.android.flavors import flavors_command


@click.group(invoke_without_command=True)
@click.pass_context
def android_group(ctx: click.Context) -> None:
    """
    🤖 Android development tools

    Comprehensive set of tools for Android Flutter development including
    building APKs, running on devices, managing flavors, and more.
    """
    if ctx.invoked_subcommand is None:
        show_android_menu(ctx)


def show_android_menu(ctx: click.Context) -> None:
    """Show interactive Android menu"""
    import inquirer
    from rich.console import Console
    from flow_cli.core.ui.banner import show_section_header

    console = Console()
    show_section_header("Android Development Tools", "🤖")

    choices = [
        "🏗️  Build - Build Android APK/AAB",
        "▶️  Run - Run on Android device/emulator",
        "📱 Install - Install APK on devices",
        "🔌 Devices - Manage Android devices",
        "🎨 Flavors - View available flavors",
        "🔙 Back to main menu",
    ]

    try:
        questions = [
            inquirer.List(
                "action", message="Select Android action:", choices=choices, carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return

        action = answers["action"]

        if action.startswith("🏗️"):
            ctx.invoke(build_command)
        elif action.startswith("▶️"):
            ctx.invoke(run_command)
        elif action.startswith("📱"):
            ctx.invoke(install_command)
        elif action.startswith("🔌"):
            ctx.invoke(devices_command)
        elif action.startswith("🎨"):
            ctx.invoke(flavors_command)
        elif action.startswith("🔙"):
            return

    except KeyboardInterrupt:
        console.print("\n[dim]Returning to main menu...[/dim]")
        return


# Add subcommands
android_group.add_command(build_command, name="build")
android_group.add_command(run_command, name="run")
android_group.add_command(install_command, name="install")
android_group.add_command(devices_command, name="devices")
android_group.add_command(flavors_command, name="flavors")

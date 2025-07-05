"""
iOS commands group - iOS development tools
"""

import platform
import click
from rich.console import Console

from flow_cli.commands.ios.devices import devices_command
from flow_cli.commands.ios.run import run_command
from flow_cli.commands.ios.flavors import flavors_command

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def ios_group(ctx: click.Context) -> None:
    """
    🍎 iOS development tools

    Comprehensive set of tools for iOS Flutter development including
    building, running on simulators, and managing iOS-specific configurations.

    Note: iOS development requires macOS.
    """

    # Check if running on macOS
    if platform.system() != "Darwin":
        console.print("[red]❌ iOS development is only available on macOS[/red]")
        console.print("[dim]iOS development requires Xcode and macOS-specific tools.[/dim]")
        return

    if ctx.invoked_subcommand is None:
        show_ios_menu(ctx)


def show_ios_menu(ctx: click.Context) -> None:
    """Show interactive iOS menu"""
    import inquirer
    from flow_cli.core.ui.banner import show_section_header

    show_section_header("iOS Development Tools", "🍎")

    choices = [
        "🏗️  Build - Build iOS app",
        "▶️  Run - Run on iOS simulator/device",
        "📱 Install - Install IPA on devices",
        "🔌 Devices - Manage iOS devices and simulators",
        "🎨 Flavors - View available flavors",
        "🔙 Back to main menu",
    ]

    try:
        questions = [
            inquirer.List("action", message="Select iOS action:", choices=choices, carousel=True),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return

        action = answers["action"]

        if action.startswith("🏗️"):
            console.print("[yellow]🚧 iOS build command coming soon![/yellow]")
            console.print("This will include:")
            console.print("  • Build for iOS simulator")
            console.print("  • Build for physical device")
            console.print("  • Archive for App Store")
            console.print("  • Flavor-specific builds")
        elif action.startswith("▶️"):
            ctx.invoke(run_command)
        elif action.startswith("📱"):
            console.print("[yellow]🚧 iOS install command coming soon![/yellow]")
            console.print("This will include:")
            console.print("  • Install IPA on connected devices")
            console.print("  • Install on simulators")
            console.print("  • TestFlight integration")
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
ios_group.add_command(devices_command, name="devices")
ios_group.add_command(run_command, name="run")
ios_group.add_command(flavors_command, name="flavors")

"""
Deployment commands group - Release and deployment tools with Fastlane
"""

import click
from rich.console import Console

from flow_cli.commands.deployment.setup import setup_fastlane_command
from flow_cli.commands.deployment.release import release_command
from flow_cli.commands.deployment.keystore import keystore_command

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
def deployment_group(ctx: click.Context) -> None:
    """
    🚀 Deployment and release tools

    Comprehensive deployment solution with Fastlane integration for
    automated releases to Google Play Store and Apple App Store.
    Includes keystore generation, CI/CD setup, and branch management.
    """
    if ctx.invoked_subcommand is None:
        show_deployment_menu(ctx)


def show_deployment_menu(ctx: click.Context) -> None:
    """Show interactive deployment menu"""
    import inquirer
    from flow_cli.core.ui.banner import show_section_header

    show_section_header("Deployment & Release Tools", "🚀")

    choices = [
        "⚙️  Setup - Configure Fastlane for project",
        "🔐 Keystore - Generate signing certificates",
        "📦 Release - Build and deploy to stores",
        "🔄 CI/CD - Setup automated deployment",
        "📋 Status - Check deployment configuration",
        "🔙 Back to main menu",
    ]

    try:
        questions = [
            inquirer.List(
                "action", message="Select deployment action:", choices=choices, carousel=True
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return

        action = answers["action"]

        if action.startswith("⚙️"):
            ctx.invoke(setup_fastlane_command)
        elif action.startswith("🔐"):
            ctx.invoke(keystore_command)
        elif action.startswith("📦"):
            ctx.invoke(release_command)
        elif action.startswith("🔄"):
            setup_cicd_interactive(ctx)
        elif action.startswith("📋"):
            show_deployment_status()
        elif action.startswith("🔙"):
            return

    except KeyboardInterrupt:
        console.print("\n[dim]Returning to main menu...[/dim]")
        return


def setup_cicd_interactive(ctx: click.Context) -> None:
    """Interactive CI/CD setup"""
    console.print("[yellow]🚧 CI/CD setup coming in next implementation![/yellow]")
    console.print("This will include:")
    console.print("  • GitHub Actions workflow generation")
    console.print("  • GitLab CI/CD pipeline setup")
    console.print("  • Automated store deployment")
    console.print("  • Environment-specific builds")


def show_deployment_status() -> None:
    """Show current deployment configuration status"""
    from flow_cli.core.flutter import FlutterProject
    from flow_cli.core.ui.banner import show_section_header, show_error
    from rich.table import Table
    from rich import box

    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        return

    show_section_header("Deployment Status", "📋")

    table = Table(title="🚀 Deployment Configuration Status", box=box.ROUNDED)
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    # Check Fastlane
    fastfile_path = project.path / "fastlane" / "Fastfile"
    if fastfile_path.exists():
        table.add_row("Fastlane", "[green]✅ Configured[/green]", "Fastfile found")
    else:
        table.add_row("Fastlane", "[red]❌ Not configured[/red]", "Run 'flow deployment setup'")

    # Check keystores
    keys_dir = project.path / "keys"
    android_keystore = keys_dir / "release-key.jks"
    ios_certificates = keys_dir / "ios"

    if android_keystore.exists():
        table.add_row("Android Keystore", "[green]✅ Generated[/green]", "release-key.jks")
    else:
        table.add_row("Android Keystore", "[red]❌ Missing[/red]", "Run 'flow deployment keystore'")

    if ios_certificates.exists():
        table.add_row("iOS Certificates", "[green]✅ Generated[/green]", "Certificates ready")
    else:
        table.add_row("iOS Certificates", "[red]❌ Missing[/red]", "Run 'flow deployment keystore'")

    # Check CI/CD
    github_workflow = project.path / ".github" / "workflows" / "release.yml"
    gitlab_ci = project.path / ".gitlab-ci.yml"

    if github_workflow.exists():
        table.add_row("GitHub Actions", "[green]✅ Configured[/green]", "release.yml workflow")
    elif gitlab_ci.exists():
        table.add_row("GitLab CI/CD", "[green]✅ Configured[/green]", ".gitlab-ci.yml pipeline")
    else:
        table.add_row("CI/CD", "[yellow]⚠️ Not configured[/yellow]", "Setup recommended")

    console.print(table)


# Add subcommands
deployment_group.add_command(setup_fastlane_command, name="setup")
deployment_group.add_command(keystore_command, name="keystore")
deployment_group.add_command(release_command, name="release")

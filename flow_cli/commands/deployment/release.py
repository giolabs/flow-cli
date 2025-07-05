"""
Release command - Build and deploy releases to app stores
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import click
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich import box

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()


@click.command()
@click.option(
    "--platform",
    type=click.Choice(["android", "ios", "both"]),
    default="both",
    help="Platform to release",
)
@click.option("--flavor", help="Flavor to build (optional)")
@click.option(
    "--track",
    type=click.Choice(["internal", "alpha", "beta", "production"]),
    default="internal",
    help="Release track",
)
@click.option("--build-only", is_flag=True, help="Only build, do not deploy")
@click.option("--skip-tests", is_flag=True, help="Skip running tests before build")
def release_command(
    platform: str, flavor: Optional[str], track: str, build_only: bool, skip_tests: bool
) -> None:
    """
    📦 Build and deploy releases to app stores

    Comprehensive release management with automated building, testing, and deployment
    to Google Play Store and Apple App Store using Fastlane.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Release Build: {project.name}", "📦")

    # Verify prerequisites
    if not verify_release_prerequisites(project, platform):
        return

    # Get release configuration
    release_config = get_release_configuration(project, platform, flavor, track, build_only)
    if not release_config:
        return

    # Show release summary
    show_release_summary(release_config)

    # Confirm release
    if not confirm_release(release_config):
        console.print("[dim]Release cancelled[/dim]")
        return

    # Execute release process
    execute_release_process(project, release_config, skip_tests)


def verify_release_prerequisites(project: FlutterProject, platform: str) -> bool:
    """Verify that all prerequisites for release are met"""

    console.print("[cyan]🔍 Verifying Release Prerequisites...[/cyan]")

    issues = []

    # Check Fastlane configuration
    fastfile_path = project.path / "fastlane" / "Fastfile"
    if not fastfile_path.exists():
        issues.append("Fastlane not configured. Run 'flow deployment setup' first.")

    # Check keystores
    if platform in ["android", "both"]:
        android_keystore = project.path / "keys" / "release-key.jks"
        keystore_properties = project.path / "keys" / "keystore.properties"

        if not android_keystore.exists():
            issues.append("Android keystore not found. Run 'flow deployment keystore' first.")
        elif not keystore_properties.exists():
            issues.append(
                "Android keystore properties not found. Run 'flow deployment keystore' first."
            )

    if platform in ["ios", "both"]:
        import platform as sys_platform

        if sys_platform.system() != "Darwin":
            issues.append("iOS releases require macOS")
        else:
            ios_keys_dir = project.path / "keys" / "ios"
            if not ios_keys_dir.exists():
                issues.append(
                    "iOS certificates not configured. Run 'flow deployment keystore' first."
                )

    # Check Flutter project validity
    pubspec_path = project.path / "pubspec.yaml"
    if not pubspec_path.exists():
        issues.append("Invalid Flutter project - pubspec.yaml not found")

    # Display issues
    if issues:
        table = Table(title="❌ Prerequisites Missing", box=box.ROUNDED)
        table.add_column("Issue", style="red")
        table.add_column("Solution", style="cyan")

        for issue in issues:
            if "Fastlane" in issue:
                table.add_row(issue, "flow deployment setup")
            elif "keystore" in issue or "certificates" in issue:
                table.add_row(issue, "flow deployment keystore")
            else:
                table.add_row(issue, "Check project configuration")

        console.print(table)
        return False

    console.print("[green]✅ All prerequisites verified[/green]")
    return True


def get_release_configuration(
    project: FlutterProject, platform: str, flavor: Optional[str], track: str, build_only: bool
) -> Optional[Dict[str, Any]]:
    """Get release configuration from user"""

    console.print("\n[cyan]📋 Release Configuration[/cyan]")

    try:
        # Get available flavors
        available_flavors = project.flavors or []

        questions = []

        # Flavor selection
        if not flavor and available_flavors:
            questions.append(
                inquirer.List(
                    "flavor",
                    message="Select flavor to release:",
                    choices=["default"] + available_flavors,
                    default="default",
                )
            )

        # Release track (if not build-only)
        if not build_only:
            track_choices = ["internal", "alpha", "beta", "production"]
            questions.append(
                inquirer.List(
                    "track", message="Select release track:", choices=track_choices, default=track
                )
            )

        # Build mode selection
        questions.extend(
            [
                inquirer.List(
                    "build_mode",
                    message="Select build mode:",
                    choices=["release", "profile"],
                    default="release",
                ),
                inquirer.Confirm("run_tests", message="Run tests before building?", default=True),
                inquirer.Confirm(
                    "increment_version",
                    message="Automatically increment version number?",
                    default=True,
                ),
            ]
        )

        # Add deployment confirmation if not build-only
        if not build_only:
            questions.append(
                inquirer.Confirm(
                    "deploy_to_store", message="Deploy to app store after building?", default=True
                )
            )

        answers = inquirer.prompt(questions)
        if not answers:
            return None

        # Build configuration
        config = {
            "platform": platform,
            "flavor": flavor or answers.get("flavor", "default"),
            "track": track if build_only else answers.get("track", "internal"),
            "build_mode": answers.get("build_mode", "release"),
            "run_tests": answers.get("run_tests", True),
            "increment_version": answers.get("increment_version", True),
            "build_only": build_only,
            "deploy_to_store": answers.get("deploy_to_store", not build_only),
        }

        return config

    except KeyboardInterrupt:
        return None


def show_release_summary(config: Dict[str, Any]) -> None:
    """Show release configuration summary"""

    table = Table(title="📦 Release Summary", box=box.ROUNDED)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="bright_white")

    table.add_row("Platform", config["platform"])
    table.add_row("Flavor", config["flavor"])
    table.add_row("Build Mode", config["build_mode"])
    table.add_row("Release Track", config["track"])
    table.add_row("Run Tests", "✅ Yes" if config["run_tests"] else "❌ No")
    table.add_row("Increment Version", "✅ Yes" if config["increment_version"] else "❌ No")
    table.add_row("Build Only", "✅ Yes" if config["build_only"] else "❌ No")

    if not config["build_only"]:
        table.add_row("Deploy to Store", "✅ Yes" if config["deploy_to_store"] else "❌ No")

    console.print(table)


def confirm_release(config: Dict[str, Any]) -> bool:
    """Confirm release with user"""

    action = "build and deploy" if config["deploy_to_store"] else "build"
    platform_text = config["platform"].upper()

    try:
        return inquirer.confirm(f"Ready to {action} {platform_text} release?", default=True)
    except KeyboardInterrupt:
        return False


def execute_release_process(
    project: FlutterProject, config: Dict[str, Any], skip_tests: bool
) -> None:
    """Execute the complete release process"""

    console.print("\n[cyan]🚀 Starting Release Process...[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        total_steps = calculate_total_steps(config, skip_tests)
        main_task = progress.add_task("Release Progress", total=total_steps)

        current_step = 0

        try:
            # Step 1: Pre-build tasks
            if config["increment_version"]:
                progress.update(main_task, description="Incrementing version number...")
                increment_version_number(project, config)
                current_step += 1
                progress.update(main_task, completed=current_step)

            # Step 2: Run tests
            if config["run_tests"] and not skip_tests:
                progress.update(main_task, description="Running tests...")
                if not run_tests(project, progress):
                    show_error("Tests failed. Release cancelled.")
                    return
                current_step += 1
                progress.update(main_task, completed=current_step)

            # Step 3: Clean build directory
            progress.update(main_task, description="Cleaning build directory...")
            clean_build_directory(project)
            current_step += 1
            progress.update(main_task, completed=current_step)

            # Step 4: Build for each platform
            if config["platform"] in ["android", "both"]:
                progress.update(main_task, description="Building Android release...")
                if not build_android_release(project, config, progress):
                    show_error("Android build failed")
                    return
                current_step += 1
                progress.update(main_task, completed=current_step)

            if config["platform"] in ["ios", "both"]:
                progress.update(main_task, description="Building iOS release...")
                if not build_ios_release(project, config, progress):
                    show_error("iOS build failed")
                    return
                current_step += 1
                progress.update(main_task, completed=current_step)

            # Step 5: Deploy to stores (if not build-only)
            if not config["build_only"] and config["deploy_to_store"]:
                if config["platform"] in ["android", "both"]:
                    progress.update(main_task, description="Deploying to Google Play...")
                    if not deploy_android_release(project, config, progress):
                        show_error("Android deployment failed")
                        return
                    current_step += 1
                    progress.update(main_task, completed=current_step)

                if config["platform"] in ["ios", "both"]:
                    progress.update(main_task, description="Deploying to App Store...")
                    if not deploy_ios_release(project, config, progress):
                        show_error("iOS deployment failed")
                        return
                    current_step += 1
                    progress.update(main_task, completed=current_step)

            progress.update(main_task, description="✅ Release completed successfully!")
            progress.update(main_task, completed=total_steps)

            # Show success message
            show_release_success(project, config)

        except Exception as e:
            progress.update(main_task, description=f"❌ Release failed: {str(e)}")
            show_error(f"Release process failed: {str(e)}")


def calculate_total_steps(config: Dict[str, Any], skip_tests: bool) -> int:
    """Calculate total steps for progress tracking"""

    steps = 1  # Clean build directory

    if config["increment_version"]:
        steps += 1

    if config["run_tests"] and not skip_tests:
        steps += 1

    # Build steps
    if config["platform"] in ["android", "both"]:
        steps += 1
    if config["platform"] in ["ios", "both"]:
        steps += 1

    # Deploy steps
    if not config["build_only"] and config["deploy_to_store"]:
        if config["platform"] in ["android", "both"]:
            steps += 1
        if config["platform"] in ["ios", "both"]:
            steps += 1

    return steps


def increment_version_number(project: FlutterProject, config: Dict[str, Any]) -> None:
    """Increment version number in pubspec.yaml"""

    pubspec_path = project.path / "pubspec.yaml"

    try:
        with open(pubspec_path, "r") as f:
            content = f.read()

        # Simple version increment (patch version)
        import re

        version_pattern = r"version:\s*(\d+)\.(\d+)\.(\d+)\+(\d+)"
        match = re.search(version_pattern, content)

        if match:
            major, minor, patch, build = match.groups()
            new_build = str(int(build) + 1)

            new_version = f"version: {major}.{minor}.{patch}+{new_build}"
            content = re.sub(version_pattern, new_version, content)

            with open(pubspec_path, "w") as f:
                f.write(content)

            console.print(
                f"[green]✅ Version incremented to {major}.{minor}.{patch}+{new_build}[/green]"
            )

    except Exception as e:
        show_warning(f"Failed to increment version: {e}")


def run_tests(project: FlutterProject, progress: Progress) -> bool:
    """Run Flutter tests"""

    try:
        result = subprocess.run(
            ["flutter", "test"], cwd=project.path, capture_output=True, text=True, timeout=300
        )

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False


def clean_build_directory(project: FlutterProject) -> None:
    """Clean Flutter build directory"""

    try:
        subprocess.run(["flutter", "clean"], cwd=project.path, capture_output=True, timeout=30)

        subprocess.run(["flutter", "pub", "get"], cwd=project.path, capture_output=True, timeout=60)

    except Exception as e:
        show_warning(f"Build cleanup warning: {e}")


def build_android_release(
    project: FlutterProject, config: Dict[str, Any], progress: Progress
) -> bool:
    """Build Android release"""

    try:
        # Build command
        cmd = ["flutter", "build", "appbundle", "--release"]

        if config["flavor"] != "default":
            cmd.extend(["--flavor", config["flavor"]])

        result = subprocess.run(cmd, cwd=project.path, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            console.print("[green]✅ Android build successful[/green]")
            return True
        else:
            console.print(f"[red]❌ Android build failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Android build timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Android build error: {e}[/red]")
        return False


def build_ios_release(project: FlutterProject, config: Dict[str, Any], progress: Progress) -> bool:
    """Build iOS release"""

    try:
        # Build command
        cmd = ["flutter", "build", "ios", "--release"]

        if config["flavor"] != "default":
            cmd.extend(["--flavor", config["flavor"]])

        result = subprocess.run(cmd, cwd=project.path, capture_output=True, text=True, timeout=600)

        if result.returncode == 0:
            console.print("[green]✅ iOS build successful[/green]")
            return True
        else:
            console.print(f"[red]❌ iOS build failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ iOS build timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ iOS build error: {e}[/red]")
        return False


def deploy_android_release(
    project: FlutterProject, config: Dict[str, Any], progress: Progress
) -> bool:
    """Deploy Android release using Fastlane"""

    try:
        # Use Fastlane to deploy
        result = subprocess.run(
            ["bundle", "exec", "fastlane", "android", config["track"]],
            cwd=project.path,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode == 0:
            console.print(f"[green]✅ Android deployed to {config['track']} track[/green]")
            return True
        else:
            console.print(f"[red]❌ Android deployment failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ Android deployment timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ Android deployment error: {e}[/red]")
        return False


def deploy_ios_release(project: FlutterProject, config: Dict[str, Any], progress: Progress) -> bool:
    """Deploy iOS release using Fastlane"""

    try:
        # Use Fastlane to deploy
        lane = "beta" if config["track"] in ["internal", "alpha", "beta"] else "release"

        result = subprocess.run(
            ["bundle", "exec", "fastlane", "ios", lane],
            cwd=project.path,
            capture_output=True,
            text=True,
            timeout=600,
        )

        if result.returncode == 0:
            console.print(f"[green]✅ iOS deployed to {config['track']} track[/green]")
            return True
        else:
            console.print(f"[red]❌ iOS deployment failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print("[red]❌ iOS deployment timed out[/red]")
        return False
    except Exception as e:
        console.print(f"[red]❌ iOS deployment error: {e}[/red]")
        return False


def show_release_success(project: FlutterProject, config: Dict[str, Any]) -> None:
    """Show success message after release"""

    success_message = f"""[bold green]🎉 Release Successful![/bold green]

[bold cyan]Release Details:[/bold cyan]
• Platform: {config['platform'].upper()}
• Flavor: {config['flavor']}
• Build Mode: {config['build_mode']}
• Track: {config['track']}

[bold yellow]Build Artifacts:[/bold yellow]"""

    if config["platform"] in ["android", "both"]:
        success_message += f"""
• Android AAB: build/app/outputs/bundle/release/app-release.aab"""

    if config["platform"] in ["ios", "both"]:
        success_message += f"""
• iOS Archive: build/ios/archive/Runner.xcarchive"""

    if not config["build_only"]:
        success_message += f"""

[bold green]Deployment Status:[/bold green]
• Successfully deployed to {config['track']} track
• Changes may take a few minutes to appear in stores

[bold cyan]Next Steps:[/bold cyan]
• Monitor store dashboards for approval status
• Test the deployed build thoroughly
• Promote to production when ready"""

    panel = Panel(
        success_message, title="🚀 Release Complete", border_style="green", box=box.ROUNDED
    )
    console.print(panel)

"""
Android build command - Build Android APKs and AABs
"""

import subprocess
import sys
from pathlib import Path
from typing import List, Optional

import click
import inquirer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Flavor to build")
@click.option(
    "--mode",
    "-m",
    type=click.Choice(["debug", "release", "profile"]),
    default="debug",
    help="Build mode",
)
@click.option(
    "--format", type=click.Choice(["apk", "appbundle"]), default="apk", help="Output format"
)
@click.option("--all-flavors", is_flag=True, help="Build all available flavors")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed build output")
def build_command(
    flavor: Optional[str], mode: str, format: str, all_flavors: bool, verbose: bool
) -> None:
    """
    🏗️ Build Android APK or App Bundle

    Build your Flutter app for Android with support for multiple flavors
    and build configurations. Supports both APK and App Bundle formats.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Building Android App: {project.name}", "🏗️")

    # Interactive mode if no options provided
    if not flavor and not all_flavors:
        flavor, mode, format, all_flavors = interactive_build_options(project)
        if not flavor and not all_flavors:
            return

    # Determine flavors to build
    flavors_to_build = []
    if all_flavors:
        flavors_to_build = project.flavors or [""]  # Empty string for default flavor
    else:
        if flavor:
            if flavor not in project.flavors:
                show_error(
                    f"Flavor '{flavor}' not found. Available flavors: {', '.join(project.flavors)}"
                )
                raise click.Abort()
            flavors_to_build = [flavor]
        else:
            flavors_to_build = [""]  # Default flavor

    # Build each flavor
    build_results = []
    for build_flavor in flavors_to_build:
        result = build_single_flavor(project, build_flavor, mode, format, verbose)
        build_results.append((build_flavor or "default", result))

    # Display results
    display_build_results(build_results, mode, format)


def interactive_build_options(project: FlutterProject) -> tuple:
    """Interactive selection of build options"""

    try:
        questions = []

        # Flavor selection
        if project.flavors:
            flavor_choices = project.flavors + ["All flavors", "Default (no flavor)"]
            questions.append(
                inquirer.List(
                    "flavor",
                    message="Select flavor to build:",
                    choices=flavor_choices,
                    default=flavor_choices[0],
                )
            )

        # Build mode
        questions.extend(
            [
                inquirer.List(
                    "mode",
                    message="Select build mode:",
                    choices=["debug", "release", "profile"],
                    default="debug",
                ),
                inquirer.List(
                    "format",
                    message="Select output format:",
                    choices=["apk", "appbundle"],
                    default="apk",
                ),
            ]
        )

        answers = inquirer.prompt(questions)
        if not answers:
            return None, None, None, False

        selected_flavor = None
        all_flavors = False

        if "flavor" in answers:
            if answers["flavor"] == "All flavors":
                all_flavors = True
            elif answers["flavor"] == "Default (no flavor)":
                selected_flavor = None
            else:
                selected_flavor = answers["flavor"]

        return selected_flavor, answers["mode"], answers["format"], all_flavors

    except KeyboardInterrupt:
        console.print("\n[dim]Build cancelled[/dim]")
        return None, None, None, False


def build_single_flavor(
    project: FlutterProject, flavor: str, mode: str, format: str, verbose: bool
) -> dict:
    """Build a single flavor"""

    flavor_name = flavor or "default"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:

        # Prepare build command
        cmd = ["flutter", "build"]

        if format == "appbundle":
            cmd.append("appbundle")
        else:
            cmd.append("apk")

        # Add mode
        if mode == "release":
            cmd.append("--release")
        elif mode == "profile":
            cmd.append("--profile")
        else:
            cmd.append("--debug")

        # Add flavor
        if flavor:
            cmd.extend(["--flavor", flavor])
            cmd.extend(["--target-platform", "android-arm64"])

        if verbose:
            cmd.append("--verbose")

        task = progress.add_task(f"Building {flavor_name} ({mode} {format})...", total=100)

        try:
            # Start build process
            process = subprocess.Popen(
                cmd, cwd=project.path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
            )

            output_lines = []

            # Read output line by line
            if process.stdout is not None:
                for line in iter(process.stdout.readline, ""):
                    if line:
                        output_lines.append(line.strip())

                        # Update progress based on build stages
                        if "Initializing gradle" in line:
                            progress.update(task, completed=10)
                        elif "Resolving dependencies" in line:
                            progress.update(task, completed=25)
                        elif "Compiling" in line:
                            progress.update(task, completed=50)
                        elif "Building" in line:
                            progress.update(task, completed=75)
                        elif "Built" in line:
                            progress.update(task, completed=100)

                        if verbose:
                            console.print(f"[dim]{line.strip()}[/dim]")

            process.wait()

            # Get build output path
            output_path = get_build_output_path(project, flavor, mode, format)

            return {
                "success": process.returncode == 0,
                "returncode": process.returncode,
                "output": "\n".join(output_lines),
                "output_path": output_path,
                "size_mb": (
                    get_file_size_mb(output_path) if output_path and output_path.exists() else 0
                ),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "output_path": None, "size_mb": 0}
        finally:
            progress.update(task, completed=100)


def get_build_output_path(
    project: FlutterProject, flavor: str, mode: str, format: str
) -> Optional[Path]:
    """Get the expected build output path"""

    if format == "appbundle":
        base_dir = project.path / "build" / "app" / "outputs" / "bundle"
        if flavor:
            expected_path = base_dir / f"{flavor}{mode.capitalize()}" / f"app-{flavor}-{mode}.aab"
        else:
            expected_path = base_dir / f"{mode}" / f"app-{mode}.aab"
    else:  # APK
        base_dir = project.path / "build" / "app" / "outputs" / "flutter-apk"
        if flavor:
            expected_path = base_dir / f"app-{flavor}-{mode}.apk"
        else:
            expected_path = base_dir / f"app-{mode}.apk"

    return expected_path if expected_path.exists() else None


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB"""
    try:
        size_bytes = file_path.stat().st_size
        return round(size_bytes / (1024 * 1024), 2)
    except Exception:
        return 0.0


def display_build_results(build_results: List[tuple], mode: str, format: str) -> None:
    """Display build results in a nice table"""

    table = Table(title=f"🏗️ Build Results ({mode} {format})", box=box.ROUNDED)
    table.add_column("Flavor", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")
    table.add_column("Size (MB)", style="yellow")
    table.add_column("Output Path", style="bright_white")

    successful_builds = 0
    total_size = 0

    for flavor_name, result in build_results:
        if result["success"]:
            successful_builds += 1
            total_size += result["size_mb"]
            status = "[green]✅ Success[/green]"
            size_str = str(result["size_mb"])
            output_path = (
                str(result["output_path"].relative_to(Path.cwd()))
                if result["output_path"]
                else "Not found"
            )
        else:
            status = "[red]❌ Failed[/red]"
            size_str = "-"
            output_path = "Build failed"

        table.add_row(flavor_name, status, size_str, output_path)

    console.print(table)

    # Summary
    total_builds = len(build_results)
    if successful_builds == total_builds:
        summary_style = "green"
        summary_icon = "🎉"
        summary_text = f"All {total_builds} builds completed successfully!"
    elif successful_builds > 0:
        summary_style = "yellow"
        summary_icon = "⚠️"
        summary_text = f"{successful_builds}/{total_builds} builds completed successfully"
    else:
        summary_style = "red"
        summary_icon = "❌"
        summary_text = "All builds failed"

    summary = f"[{summary_style}]{summary_icon} {summary_text}[/{summary_style}]"
    if total_size > 0:
        summary += f"\n💾 Total size: {total_size:.2f} MB"

    summary_panel = Panel(summary, title="📊 Summary", border_style=summary_style, box=box.ROUNDED)
    console.print(summary_panel)

    # Show failed builds details
    failed_builds = [(name, result) for name, result in build_results if not result["success"]]
    if failed_builds:
        show_build_failures(failed_builds)


def show_build_failures(failed_builds: List[tuple]) -> None:
    """Show details of failed builds"""

    for flavor_name, result in failed_builds:
        error_text = result.get("error", "Unknown error")
        if "output" in result and result["output"]:
            # Show last few lines of build output
            output_lines = result["output"].split("\n")
            error_text = "\n".join(output_lines[-10:])  # Last 10 lines

        error_panel = Panel(
            error_text, title=f"❌ Build Error: {flavor_name}", border_style="red", box=box.ROUNDED
        )
        console.print(error_panel)

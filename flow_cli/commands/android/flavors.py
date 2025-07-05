"""
Android flavors command - View and manage Android flavors
"""

import json
from pathlib import Path
from typing import List, Dict, Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Show details for specific flavor")
def flavors_command(flavor: Optional[str]) -> None:
    """
    🎨 View and manage Android flavors

    Display available flavors with their configurations, build status,
    and assets. Shows flavor-specific package names, app names, and resources.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Android Flavors: {project.name}", "🎨")

    if not project.flavors:
        show_no_flavors_message()
        return

    if flavor:
        show_flavor_details(project, flavor)
    else:
        show_all_flavors(project)


def show_no_flavors_message() -> None:
    """Show message when no flavors are found"""
    message = """[yellow]No flavors found in this project.[/yellow]

To add flavors to your Flutter project:

1. Create flavor directories:
   [cyan]assets/configs/[flavor-name]/[/cyan]

2. Add required files for each flavor:
   • [green]config.json[/green] - Flavor configuration
   • [green]icon.png[/green] - App icon (1024x1024px)
   • [green]splash.png[/green] - Splash screen image

3. Use Flow CLI to generate assets:
   [cyan]flow generate branding [flavor-name][/cyan]

Example flavor structure:
[dim]assets/
├── configs/
│   ├── production/
│   │   ├── config.json
│   │   ├── icon.png
│   │   └── splash.png
│   └── development/
│       ├── config.json
│       ├── icon.png
│       └── splash.png[/dim]"""

    panel = Panel(message, title="💡 Adding Flavors", border_style="blue", box=box.ROUNDED)
    console.print(panel)


def show_all_flavors(project: FlutterProject) -> None:
    """Show overview of all flavors"""

    # Collect flavor information
    flavor_data = []
    for flavor_name in project.flavors:
        data = analyze_flavor(project, flavor_name)
        flavor_data.append(data)

    # Main flavors table
    table = Table(title="🎨 Available Flavors", box=box.ROUNDED)
    table.add_column("Flavor", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold", no_wrap=True)
    table.add_column("App Name", style="bright_white")
    table.add_column("Package", style="green")
    table.add_column("Assets", style="yellow")

    complete_count = 0

    for data in flavor_data:
        # Status indicator
        if data["status"] == "complete":
            status_display = "[green]✅ Complete[/green]"
            complete_count += 1
        elif data["status"] == "partial":
            status_display = "[yellow]⚠️ Partial[/yellow]"
        else:
            status_display = "[red]❌ Missing[/red]"

        # Assets indicator
        assets_count = sum(
            [1 for asset in ["config", "icon", "splash"] if data.get(f"has_{asset}", False)]
        )
        assets_display = f"{assets_count}/3"

        table.add_row(
            data["name"],
            status_display,
            data.get("app_name", "Not set"),
            data.get("package_name", "Not set"),
            assets_display,
        )

    console.print(table)

    # Summary
    total_flavors = len(flavor_data)
    summary_text = f"[cyan]Total flavors: {total_flavors}[/cyan]"
    if complete_count == total_flavors:
        summary_text += f" | [green]✅ All complete[/green]"
    elif complete_count > 0:
        summary_text += f" | [green]✅ {complete_count} complete[/green], [yellow]⚠️ {total_flavors - complete_count} incomplete[/yellow]"
    else:
        summary_text += f" | [red]❌ All incomplete[/red]"

    console.print(f"\n{summary_text}")

    # Show build status
    show_build_status(project, flavor_data)


def show_flavor_details(project: FlutterProject, flavor: str) -> None:
    """Show detailed information for a specific flavor"""

    if flavor not in project.flavors:
        show_error(f"Flavor '{flavor}' not found. Available: {', '.join(project.flavors)}")
        return

    data = analyze_flavor(project, flavor)

    # Flavor header
    console.print(f"\n[bold cyan]🎨 Flavor: {flavor}[/bold cyan]")

    # Configuration details
    config_table = Table(title="📋 Configuration", box=box.SIMPLE)
    config_table.add_column("Property", style="cyan")
    config_table.add_column("Value", style="bright_white")

    config_table.add_row("App Name", data.get("app_name", "Not set"))
    config_table.add_row("Package Name", data.get("package_name", "Not set"))
    config_table.add_row("Main Color", data.get("main_color", "Not set"))
    config_table.add_row("Status", get_status_display(data["status"]))

    console.print(config_table)

    # Assets status
    assets_table = Table(title="🎨 Assets", box=box.SIMPLE)
    assets_table.add_column("Asset", style="cyan")
    assets_table.add_column("Status", style="bold")
    assets_table.add_column("Details", style="dim")

    assets = [
        ("config.json", data["has_config"], data.get("config_path", "")),
        ("icon.png", data["has_icon"], data.get("icon_path", "")),
        ("splash.png", data["has_splash"], data.get("splash_path", "")),
    ]

    for asset_name, exists, path in assets:
        status = "[green]✅ Found[/green]" if exists else "[red]❌ Missing[/red]"
        details = str(Path(path).relative_to(project.path)) if path and exists else "Required"
        assets_table.add_row(asset_name, status, details)

    console.print(assets_table)

    # Show config content if available
    if data["has_config"] and data.get("config_data"):
        show_config_details(data["config_data"])

    # Show build artifacts
    show_flavor_builds(project, flavor)


def analyze_flavor(project: FlutterProject, flavor: str) -> Dict:
    """Analyze a flavor's configuration and assets"""

    flavor_dir = project.path / "assets" / "configs" / flavor

    # Check required files
    config_file = flavor_dir / "config.json"
    icon_file = flavor_dir / "icon.png"
    splash_file = flavor_dir / "splash.png"

    has_config = config_file.exists()
    has_icon = icon_file.exists()
    has_splash = splash_file.exists()

    # Determine status
    if has_config and has_icon and has_splash:
        status = "complete"
    elif has_config or has_icon or has_splash:
        status = "partial"
    else:
        status = "missing"

    # Load config data
    config_data = {}
    if has_config:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass

    return {
        "name": flavor,
        "status": status,
        "has_config": has_config,
        "has_icon": has_icon,
        "has_splash": has_splash,
        "config_path": str(config_file) if has_config else "",
        "icon_path": str(icon_file) if has_icon else "",
        "splash_path": str(splash_file) if has_splash else "",
        "config_data": config_data,
        "app_name": config_data.get("appName", ""),
        "package_name": config_data.get("packageName", ""),
        "main_color": config_data.get("mainColor", ""),
    }


def get_status_display(status: str) -> str:
    """Get colored status display"""
    if status == "complete":
        return "[green]✅ Complete[/green]"
    elif status == "partial":
        return "[yellow]⚠️ Partial[/yellow]"
    else:
        return "[red]❌ Missing[/red]"


def show_config_details(config_data: Dict) -> None:
    """Show configuration file details"""

    if not config_data:
        return

    config_text = ""
    for key, value in config_data.items():
        config_text += f"[cyan]{key}:[/cyan] {value}\n"

    if config_text:
        config_panel = Panel(
            config_text.strip(), title="📄 config.json", border_style="green", box=box.ROUNDED
        )
        console.print(config_panel)


def show_build_status(project: FlutterProject, flavor_data: List[Dict]) -> None:
    """Show build status for flavors"""

    # Check for build artifacts
    build_artifacts = []
    apk_dir = project.path / "build" / "app" / "outputs" / "flutter-apk"

    if apk_dir.exists():
        for flavor_info in flavor_data:
            flavor_name = flavor_info["name"]

            # Look for APKs
            debug_apk = apk_dir / f"app-{flavor_name}-debug.apk"
            release_apk = apk_dir / f"app-{flavor_name}-release.apk"

            artifacts = []
            if debug_apk.exists():
                size_mb = round(debug_apk.stat().st_size / (1024 * 1024), 2)
                artifacts.append(f"Debug ({size_mb} MB)")

            if release_apk.exists():
                size_mb = round(release_apk.stat().st_size / (1024 * 1024), 2)
                artifacts.append(f"Release ({size_mb} MB)")

            if artifacts:
                build_artifacts.append((flavor_name, artifacts))

    if build_artifacts:
        console.print()
        build_table = Table(title="🏗️ Build Artifacts", box=box.ROUNDED)
        build_table.add_column("Flavor", style="cyan")
        build_table.add_column("Available Builds", style="bright_white")

        for flavor_name, artifacts in build_artifacts:
            build_table.add_row(flavor_name, ", ".join(artifacts))

        console.print(build_table)
    else:
        console.print(
            f"\n[dim]💡 No build artifacts found. Run 'flow android build' to create APKs.[/dim]"
        )


def show_flavor_builds(project: FlutterProject, flavor: str) -> None:
    """Show build artifacts for a specific flavor"""

    apk_dir = project.path / "build" / "app" / "outputs" / "flutter-apk"

    if not apk_dir.exists():
        console.print(
            f"\n[dim]💡 No builds found. Run 'flow android build {flavor}' to create APK.[/dim]"
        )
        return

    # Find APKs for this flavor
    apk_patterns = [
        f"app-{flavor}-debug.apk",
        f"app-{flavor}-release.apk",
        f"app-{flavor}-profile.apk",
    ]

    found_apks = []
    for pattern in apk_patterns:
        apk_path = apk_dir / pattern
        if apk_path.exists():
            size_mb = round(apk_path.stat().st_size / (1024 * 1024), 2)
            found_apks.append((pattern, size_mb, apk_path))

    if found_apks:
        builds_table = Table(title="🏗️ Build Artifacts", box=box.SIMPLE)
        builds_table.add_column("APK", style="cyan")
        builds_table.add_column("Size (MB)", style="yellow")
        builds_table.add_column("Path", style="dim")

        for apk_name, size_mb, apk_path in found_apks:
            rel_path = str(apk_path.relative_to(project.path))
            builds_table.add_row(apk_name, str(size_mb), rel_path)

        console.print(builds_table)
    else:
        console.print(
            f"\n[dim]💡 No builds found for {flavor}. Run 'flow android build {flavor}' to create APK.[/dim]"
        )

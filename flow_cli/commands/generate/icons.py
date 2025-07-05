"""
Icons generation command - Generate app icons using flutter_launcher_icons
"""

import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import click
import inquirer
import yaml
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Generate icons for specific flavor")
@click.option("--all-flavors", is_flag=True, help="Generate icons for all flavors")
@click.option(
    "--platform",
    type=click.Choice(["android", "ios", "both"]),
    default="both",
    help="Target platform",
)
def icons_command(flavor: Optional[str], all_flavors: bool, platform: str) -> None:
    """
    🎯 Generate app icons

    Generate app icons for Android and iOS using flutter_launcher_icons.
    Supports adaptive icons for Android and proper icon sizes for iOS.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header("Generate App Icons", "🎯")

    # Check if flutter_launcher_icons is installed
    if not project.has_dependency("flutter_launcher_icons"):
        show_error("flutter_launcher_icons package not found in dependencies")
        show_package_installation_help()
        raise click.Abort()

    # Interactive selection if needed
    if not flavor and not all_flavors:
        if not project.flavors:
            # Generate for main app (no flavor)
            generate_main_app_icons(project, platform)
        else:
            flavor, all_flavors = interactive_flavor_selection(project.flavors)
            if not flavor and not all_flavors:
                return

    # Generate icons
    if all_flavors:
        generate_all_flavor_icons(project, project.flavors, platform)
    elif flavor:
        generate_flavor_icons(project, flavor, platform)
    else:
        generate_main_app_icons(project, platform)


def interactive_flavor_selection(flavors: List[str]) -> tuple:
    """Interactive flavor selection for icon generation"""

    choices = flavors + ["All flavors", "Main app (no flavor)"]

    try:
        questions = [
            inquirer.List(
                "selection", message="Select target for icon generation:", choices=choices
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None, False

        selection = answers["selection"]
        if selection == "All flavors":
            return None, True
        elif selection == "Main app (no flavor)":
            return None, False
        else:
            return selection, False

    except KeyboardInterrupt:
        return None, False


def generate_main_app_icons(project: FlutterProject, platform: str) -> None:
    """Generate icons for main app (no flavor)"""

    console.print("[cyan]Generating icons for main app...[/cyan]")

    # Check for icon file
    icon_path = project.path / "assets" / "icon.png"
    if not icon_path.exists():
        show_error("Icon file not found: assets/icon.png")
        show_icon_requirements()
        return

    # Create configuration
    config = create_icon_config(None, platform, str(icon_path))

    # Generate icons
    result = run_flutter_launcher_icons(project, config)

    if result["success"]:
        show_success("Icons generated successfully for main app")
        show_generated_files(project, None)
    else:
        show_error(f"Icon generation failed: {result.get('error', 'Unknown error')}")


def generate_flavor_icons(project: FlutterProject, flavor: str, platform: str) -> None:
    """Generate icons for specific flavor"""

    console.print(f"[cyan]Generating icons for flavor: {flavor}...[/cyan]")

    # Check flavor configuration
    flavor_dir = project.path / "assets" / "configs" / flavor
    icon_path = flavor_dir / "icon.png"

    if not icon_path.exists():
        show_error(f"Icon file not found for flavor '{flavor}': {icon_path}")
        show_flavor_requirements(flavor)
        return

    # Create configuration
    config = create_icon_config(flavor, platform, str(icon_path))

    # Generate icons
    result = run_flutter_launcher_icons(project, config, flavor)

    if result["success"]:
        show_success(f"Icons generated successfully for flavor: {flavor}")
        show_generated_files(project, flavor)
    else:
        show_error(f"Icon generation failed for {flavor}: {result.get('error', 'Unknown error')}")


def generate_all_flavor_icons(project: FlutterProject, flavors: List[str], platform: str) -> None:
    """Generate icons for all flavors"""

    results = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        for flavor in flavors:
            task = progress.add_task(f"Generating icons for {flavor}...", total=None)

            # Check flavor icon
            flavor_dir = project.path / "assets" / "configs" / flavor
            icon_path = flavor_dir / "icon.png"

            if not icon_path.exists():
                results.append(
                    (flavor, {"success": False, "error": f"Icon file not found: {icon_path}"})
                )
                progress.remove_task(task)
                continue

            # Create config and generate
            config = create_icon_config(flavor, platform, str(icon_path))
            result = run_flutter_launcher_icons(project, config, flavor)
            results.append((flavor, result))

            progress.remove_task(task)

    # Display results
    display_batch_results(results, "Icons Generation")


def create_icon_config(flavor: Optional[str], platform: str, icon_path: str) -> Dict:
    """Create flutter_launcher_icons configuration"""

    config = {"flutter_launcher_icons": {"image_path": icon_path, "remove_alpha_ios": True}}

    # Platform settings
    if platform in ["android", "both"]:
        config["flutter_launcher_icons"]["android"] = True
        config["flutter_launcher_icons"]["adaptive_icon_foreground"] = icon_path
        config["flutter_launcher_icons"]["adaptive_icon_background"] = "#FFFFFF"

    if platform in ["ios", "both"]:
        config["flutter_launcher_icons"]["ios"] = True

    # Web support
    config["flutter_launcher_icons"]["web"] = {
        "generate": True,
        "image_path": icon_path,
        "background_color": "#FFFFFF",
        "theme_color": "#FFFFFF",
    }

    return config


def run_flutter_launcher_icons(
    project: FlutterProject, config: Dict, flavor: Optional[str] = None
) -> Dict:
    """Run flutter_launcher_icons with given configuration"""

    # Create temporary config file
    config_filename = (
        f"flutter_launcher_icons_{flavor}.yaml" if flavor else "flutter_launcher_icons.yaml"
    )
    config_path = project.path / config_filename

    try:
        # Write config file
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Run flutter_launcher_icons
        cmd = ["dart", "run", "flutter_launcher_icons", "-f", str(config_path)]

        result = subprocess.run(cmd, cwd=project.path, capture_output=True, text=True, timeout=120)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Icon generation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Clean up config file
        if config_path.exists():
            config_path.unlink()


def show_generated_files(project: FlutterProject, flavor: Optional[str]) -> None:
    """Show generated icon files"""

    generated_files = []

    # Android icons
    android_res = project.path / "android" / "app" / "src" / "main" / "res"
    if flavor:
        android_res = project.path / "android" / "app" / "src" / flavor / "res"

    if android_res.exists():
        mipmap_dirs = list(android_res.glob("mipmap-*"))
        for mipmap_dir in mipmap_dirs:
            icons = list(mipmap_dir.glob("*.png"))
            for icon in icons:
                generated_files.append(("Android", str(icon.relative_to(project.path))))

    # iOS icons
    ios_assets = project.path / "ios" / "Runner" / "Assets.xcassets" / "AppIcon.appiconset"
    if ios_assets.exists():
        icons = list(ios_assets.glob("*.png"))
        for icon in icons:
            generated_files.append(("iOS", str(icon.relative_to(project.path))))

    # Web icons
    web_icons = project.path / "web" / "icons"
    if web_icons.exists():
        icons = list(web_icons.glob("*.png"))
        for icon in icons:
            generated_files.append(("Web", str(icon.relative_to(project.path))))

    if generated_files:
        table = Table(title="📱 Generated Icon Files", box=box.ROUNDED)
        table.add_column("Platform", style="cyan")
        table.add_column("File Path", style="bright_white")

        for platform, file_path in generated_files[:10]:  # Show first 10
            table.add_row(platform, file_path)

        if len(generated_files) > 10:
            table.add_row("...", f"and {len(generated_files) - 10} more files")

        console.print(table)


def display_batch_results(results: List[tuple], operation: str) -> None:
    """Display batch operation results"""

    table = Table(title=f"📊 {operation} Results", box=box.ROUNDED)
    table.add_column("Flavor", style="cyan")
    table.add_column("Status", style="bold")
    table.add_column("Details", style="dim")

    successful = 0
    failed = 0

    for flavor, result in results:
        if result["success"]:
            successful += 1
            status = "[green]✅ Success[/green]"
            details = "Icons generated"
        else:
            failed += 1
            status = "[red]❌ Failed[/red]"
            details = result.get("error", "Unknown error")[:50] + "..."

        table.add_row(flavor, status, details)

    console.print(table)

    # Summary
    total = len(results)
    if failed == 0:
        summary_style = "green"
        summary_text = f"✅ All {total} flavors completed successfully!"
    elif successful > 0:
        summary_style = "yellow"
        summary_text = f"⚠️ {successful}/{total} flavors completed successfully"
    else:
        summary_style = "red"
        summary_text = f"❌ All {total} flavors failed"

    console.print(f"\n[{summary_style}]{summary_text}[/{summary_style}]")


def show_package_installation_help() -> None:
    """Show help for installing flutter_launcher_icons"""

    help_text = """[yellow]flutter_launcher_icons package not found.[/yellow]

To install flutter_launcher_icons:

1. [green]Add to pubspec.yaml:[/green]
   [cyan]dev_dependencies:
     flutter_launcher_icons: ^0.13.1[/cyan]

2. [green]Install package:[/green]
   [cyan]flutter pub get[/cyan]

3. [green]Generate icons:[/green]
   [cyan]flow generate icons[/cyan]

[dim]Package documentation:[/dim]
https://pub.dev/packages/flutter_launcher_icons"""

    panel = Panel(help_text, title="📦 Package Installation", border_style="blue", box=box.ROUNDED)
    console.print(panel)


def show_icon_requirements() -> None:
    """Show icon file requirements"""

    requirements_text = """[yellow]Icon file requirements:[/yellow]

📁 Required file location:
  [cyan]assets/icon.png[/cyan] (for main app)

📐 Icon specifications:
  • Format: PNG
  • Size: 1024x1024 pixels minimum
  • Square aspect ratio (1:1)
  • Transparent background recommended
  • High quality, sharp details

💡 Best practices:
  • Use vector source when possible
  • Avoid text (may be unreadable at small sizes)
  • Simple, recognizable design
  • High contrast colors"""

    panel = Panel(
        requirements_text, title="🎯 Icon Requirements", border_style="blue", box=box.ROUNDED
    )
    console.print(panel)


def show_flavor_requirements(flavor: str) -> None:
    """Show flavor icon requirements"""

    requirements_text = f"""[yellow]Icon file missing for flavor '{flavor}'[/yellow]

📁 Required file location:
  [cyan]assets/configs/{flavor}/icon.png[/cyan]

📐 Icon specifications:
  • Format: PNG
  • Size: 1024x1024 pixels minimum  
  • Square aspect ratio (1:1)
  • Transparent background recommended

🔧 Quick setup:
1. Create directory: [cyan]mkdir -p assets/configs/{flavor}[/cyan]
2. Add icon file: [cyan]assets/configs/{flavor}/icon.png[/cyan]
3. Generate icons: [cyan]flow generate icons --flavor {flavor}[/cyan]"""

    panel = Panel(
        requirements_text,
        title=f"🎯 Flavor '{flavor}' Requirements",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)

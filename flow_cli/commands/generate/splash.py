"""
Splash screen generation command - Generate splash screens using flutter_native_splash
"""

import json
import subprocess
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
@click.option("--flavor", "-f", help="Generate splash screen for specific flavor")
@click.option("--all-flavors", is_flag=True, help="Generate splash screens for all flavors")
@click.option(
    "--platform",
    type=click.Choice(["android", "ios", "both"]),
    default="both",
    help="Target platform",
)
def splash_command(flavor: Optional[str], all_flavors: bool, platform: str) -> None:
    """
    💧 Generate splash screens

    Generate splash screens for Android and iOS using flutter_native_splash.
    Supports Android 12+ splash screens and iOS launch images.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header("Generate Splash Screens", "💧")

    # Check if flutter_native_splash is installed
    if not project.has_dependency("flutter_native_splash"):
        show_error("flutter_native_splash package not found in dependencies")
        show_package_installation_help()
        raise click.Abort()

    # Interactive selection if needed
    if not flavor and not all_flavors:
        if not project.flavors:
            # Generate for main app (no flavor)
            generate_main_app_splash(project, platform)
        else:
            flavor, all_flavors = interactive_flavor_selection(project.flavors)
            if not flavor and not all_flavors:
                return

    # Generate splash screens
    if all_flavors:
        generate_all_flavor_splash(project, project.flavors, platform)
    elif flavor:
        generate_flavor_splash(project, flavor, platform)
    else:
        generate_main_app_splash(project, platform)


def interactive_flavor_selection(flavors: List[str]) -> tuple:
    """Interactive flavor selection for splash generation"""

    choices = flavors + ["All flavors", "Main app (no flavor)"]

    try:
        questions = [
            inquirer.List(
                "selection", message="Select target for splash screen generation:", choices=choices
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


def generate_main_app_splash(project: FlutterProject, platform: str) -> None:
    """Generate splash screen for main app (no flavor)"""

    console.print("[cyan]Generating splash screen for main app...[/cyan]")

    # Check for splash image
    splash_path = project.path / "assets" / "splash.png"
    if not splash_path.exists():
        show_error("Splash image not found: assets/splash.png")
        show_splash_requirements()
        return

    # Create configuration
    config = create_splash_config(None, platform, str(splash_path))

    # Generate splash
    result = run_flutter_native_splash(project, config)

    if result["success"]:
        show_success("Splash screen generated successfully for main app")
        show_generated_splash_files(project, None)
    else:
        show_error(f"Splash generation failed: {result.get('error', 'Unknown error')}")


def generate_flavor_splash(project: FlutterProject, flavor: str, platform: str) -> None:
    """Generate splash screen for specific flavor"""

    console.print(f"[cyan]Generating splash screen for flavor: {flavor}...[/cyan]")

    # Check flavor configuration
    flavor_dir = project.path / "assets" / "configs" / flavor
    splash_path = flavor_dir / "splash.png"
    config_path = flavor_dir / "config.json"

    if not splash_path.exists():
        show_error(f"Splash image not found for flavor '{flavor}': {splash_path}")
        show_flavor_splash_requirements(flavor)
        return

    # Load flavor config for colors
    flavor_config = {}
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                flavor_config = json.load(f)
        except Exception:
            pass

    # Create configuration
    config = create_splash_config(flavor, platform, str(splash_path), flavor_config)

    # Generate splash
    result = run_flutter_native_splash(project, config, flavor)

    if result["success"]:
        show_success(f"Splash screen generated successfully for flavor: {flavor}")
        show_generated_splash_files(project, flavor)
    else:
        show_error(f"Splash generation failed for {flavor}: {result.get('error', 'Unknown error')}")


def generate_all_flavor_splash(project: FlutterProject, flavors: List[str], platform: str) -> None:
    """Generate splash screens for all flavors"""

    results = []

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        for flavor in flavors:
            task = progress.add_task(f"Generating splash for {flavor}...", total=None)

            # Check flavor splash
            flavor_dir = project.path / "assets" / "configs" / flavor
            splash_path = flavor_dir / "splash.png"
            config_path = flavor_dir / "config.json"

            if not splash_path.exists():
                results.append(
                    (flavor, {"success": False, "error": f"Splash image not found: {splash_path}"})
                )
                progress.remove_task(task)
                continue

            # Load flavor config
            flavor_config = {}
            if config_path.exists():
                try:
                    with open(config_path, "r", encoding="utf-8") as f:
                        flavor_config = json.load(f)
                except Exception:
                    pass

            # Create config and generate
            config = create_splash_config(flavor, platform, str(splash_path), flavor_config)
            result = run_flutter_native_splash(project, config, flavor)
            results.append((flavor, result))

            progress.remove_task(task)

    # Display results
    display_batch_splash_results(results, "Splash Screen Generation")


def create_splash_config(
    flavor: Optional[str], platform: str, splash_path: str, flavor_config: Dict = {}
) -> Dict:
    """Create flutter_native_splash configuration"""

    # Get background color from flavor config or use default
    background_color = f"#{flavor_config.get('mainColor', 'FFFFFF').lstrip('#')}"

    config: Dict = {
        "flutter_native_splash": {
            "color": background_color,
            "image": splash_path,
            "branding_mode": "bottom",
            "color_dark": background_color,
            "image_dark": splash_path,
        }
    }

    # Platform settings
    if platform in ["android", "both"]:
        config["flutter_native_splash"]["android"] = "true"
        config["flutter_native_splash"]["android_12"] = json.dumps(
            {
                "image": splash_path,
                "icon_background_color": background_color,
                "image_dark": splash_path,
                "icon_background_color_dark": background_color,
            }
        )
    else:
        config["flutter_native_splash"]["android"] = "false"

    if platform in ["ios", "both"]:
        config["flutter_native_splash"]["ios"] = "true"
    else:
        config["flutter_native_splash"]["ios"] = "false"

    # Web configuration
    config["flutter_native_splash"]["web"] = "false"

    return config


def run_flutter_native_splash(
    project: FlutterProject, config: Dict, flavor: Optional[str] = None
) -> Dict:
    """Run flutter_native_splash with given configuration"""

    # Create temporary config file
    config_filename = (
        f"flutter_native_splash_{flavor}.yaml" if flavor else "flutter_native_splash.yaml"
    )
    config_path = project.path / config_filename

    try:
        # Write config file
        with open(config_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False)

        # Run flutter_native_splash
        cmd = ["dart", "run", "flutter_native_splash:create", f"--path={config_path}"]

        result = subprocess.run(cmd, cwd=project.path, capture_output=True, text=True, timeout=120)

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Splash generation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # Clean up config file
        if config_path.exists():
            config_path.unlink()


def show_generated_splash_files(project: FlutterProject, flavor: Optional[str]) -> None:
    """Show generated splash screen files"""

    generated_files = []

    # Android splash files
    android_res = project.path / "android" / "app" / "src" / "main" / "res"
    if flavor:
        android_res = project.path / "android" / "app" / "src" / flavor / "res"

    if android_res.exists():
        # Check for splash-related files
        splash_files = list(android_res.glob("**/launch_background.*"))
        splash_files.extend(list(android_res.glob("**/splash.*")))
        splash_files.extend(list(android_res.glob("drawable*/launch_background.xml")))

        for splash_file in splash_files:
            generated_files.append(("Android", str(splash_file.relative_to(project.path))))

    # iOS splash files
    ios_assets = project.path / "ios" / "Runner" / "Assets.xcassets" / "LaunchImage.imageset"
    if ios_assets.exists():
        splash_files = list(ios_assets.glob("*.png"))
        splash_files.extend(list(ios_assets.glob("Contents.json")))
        for splash_file in splash_files:
            generated_files.append(("iOS", str(splash_file.relative_to(project.path))))

    # Check for LaunchScreen.storyboard
    storyboard = project.path / "ios" / "Runner" / "Base.lproj" / "LaunchScreen.storyboard"
    if storyboard.exists():
        generated_files.append(("iOS", str(storyboard.relative_to(project.path))))

    if generated_files:
        table = Table(title="💧 Generated Splash Screen Files", box=box.ROUNDED)
        table.add_column("Platform", style="cyan")
        table.add_column("File Path", style="bright_white")

        for platform, file_path in generated_files[:15]:  # Show first 15
            table.add_row(platform, file_path)

        if len(generated_files) > 15:
            table.add_row("...", f"and {len(generated_files) - 15} more files")

        console.print(table)


def display_batch_splash_results(results: List[tuple], operation: str) -> None:
    """Display batch splash operation results"""

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
            details = "Splash screen generated"
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
    """Show help for installing flutter_native_splash"""

    help_text = """[yellow]flutter_native_splash package not found.[/yellow]

To install flutter_native_splash:

1. [green]Add to pubspec.yaml:[/green]
   [cyan]dev_dependencies:
     flutter_native_splash: ^2.3.2[/cyan]

2. [green]Install package:[/green]
   [cyan]flutter pub get[/cyan]

3. [green]Generate splash screens:[/green]
   [cyan]flow generate splash[/cyan]

[dim]Package documentation:[/dim]
https://pub.dev/packages/flutter_native_splash"""

    panel = Panel(help_text, title="📦 Package Installation", border_style="blue", box=box.ROUNDED)
    console.print(panel)


def show_splash_requirements() -> None:
    """Show splash image requirements"""

    requirements_text = """[yellow]Splash image requirements:[/yellow]

📁 Required file location:
  [cyan]assets/splash.png[/cyan] (for main app)

📐 Splash specifications:
  • Format: PNG
  • Minimum size: 1242x2436 pixels
  • Aspect ratio: Portrait orientation recommended
  • Transparent background supported
  • Center-focused design (safe area)

💡 Best practices:
  • Design for center 1/3 of screen
  • Avoid placing elements near edges
  • Use simple, recognizable imagery
  • Consider different screen sizes
  • Test on various devices

🎨 Android 12+ considerations:
  • Icon-based splash screen
  • Animated vector drawables supported
  • Background color matters"""

    panel = Panel(
        requirements_text, title="💧 Splash Requirements", border_style="blue", box=box.ROUNDED
    )
    console.print(panel)


def show_flavor_splash_requirements(flavor: str) -> None:
    """Show flavor splash requirements"""

    requirements_text = f"""[yellow]Splash image missing for flavor '{flavor}'[/yellow]

📁 Required files:
  [cyan]assets/configs/{flavor}/splash.png[/cyan]
  [cyan]assets/configs/{flavor}/config.json[/cyan] (for background color)

📐 Splash specifications:
  • Format: PNG
  • Minimum size: 1242x2436 pixels
  • Center-focused design
  • Transparent background supported

🎨 Color configuration (config.json):
  [cyan]{{
    "mainColor": "FF5722",
    "appName": "MyApp {flavor.title()}"
  }}[/cyan]

🔧 Quick setup:
1. Create directory: [cyan]mkdir -p assets/configs/{flavor}[/cyan]
2. Add splash image: [cyan]assets/configs/{flavor}/splash.png[/cyan]
3. Add config: [cyan]assets/configs/{flavor}/config.json[/cyan]
4. Generate: [cyan]flow generate splash --flavor {flavor}[/cyan]"""

    panel = Panel(
        requirements_text,
        title=f"💧 Flavor '{flavor}' Requirements",
        border_style="blue",
        box=box.ROUNDED,
    )
    console.print(panel)

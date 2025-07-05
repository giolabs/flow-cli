"""
Branding generation command - Complete branding asset generation
Based on the existing Python script in tools/generate_branding.py
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import inquirer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich import box

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Flavor to generate branding for")
@click.option("--all-flavors", is_flag=True, help="Generate branding for all flavors")
def branding_command(flavor: Optional[str], all_flavors: bool) -> None:
    """
    🎨 Generate complete branding package

    Generates app icons, splash screens, and platform-specific assets
    for your Flutter flavors. Includes Android adaptive icons, iOS app icons,
    and web manifest generation.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Generate Branding: {project.name}", "🎨")

    # Check if the original Python script exists
    original_script = project.path / "tools" / "generate_branding.py"
    if not original_script.exists():
        show_error("Original generate_branding.py script not found in tools/ directory")
        show_warning("This command requires the existing branding generation script")
        raise click.Abort()

    # Interactive selection if needed
    if not flavor and not all_flavors:
        if not project.flavors:
            show_error("No flavors found in project")
            show_no_flavors_help()
            raise click.Abort()

        flavor, all_flavors = interactive_flavor_selection(project.flavors)
        if not flavor and not all_flavors:
            return

    # Determine flavors to process
    flavors_to_process = []
    if all_flavors:
        flavors_to_process = project.flavors
    elif flavor:
        if flavor not in project.flavors:
            show_error(f"Flavor '{flavor}' not found. Available: {', '.join(project.flavors)}")
            raise click.Abort()
        flavors_to_process = [flavor]

    if not flavors_to_process:
        show_error("No flavors selected for processing")
        raise click.Abort()

    # Validate flavors before processing
    for flavor_name in flavors_to_process:
        if not validate_flavor_assets(project, flavor_name):
            show_error(f"Flavor '{flavor_name}' is missing required assets")
            show_flavor_requirements(flavor_name)
            raise click.Abort()

    # Process each flavor
    results = []
    for flavor_name in flavors_to_process:
        result = generate_flavor_branding(project, flavor_name, original_script)
        results.append((flavor_name, result))

    # Display results
    display_branding_results(results)


def interactive_flavor_selection(flavors: list) -> tuple:
    """Interactive flavor selection"""

    choices = flavors + ["All flavors"]

    try:
        questions = [
            inquirer.List(
                "selection", message="Select flavor for branding generation:", choices=choices
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None, False

        selection = answers["selection"]
        if selection == "All flavors":
            return None, True
        else:
            return selection, False

    except KeyboardInterrupt:
        return None, False


def validate_flavor_assets(project: FlutterProject, flavor: str) -> bool:
    """Validate that flavor has required assets"""

    flavor_dir = project.path / "assets" / "configs" / flavor

    required_files = ["config.json", "icon.png", "splash.png"]

    for file_name in required_files:
        file_path = flavor_dir / file_name
        if not file_path.exists():
            return False

    # Validate config.json format
    config_file = flavor_dir / "config.json"
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)

        required_keys = ["appName", "mainColor"]
        for key in required_keys:
            if key not in config:
                return False
    except Exception:
        return False

    return True


def generate_flavor_branding(project: FlutterProject, flavor: str, script_path: Path) -> dict:
    """Generate branding for a single flavor using the original script"""

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        task = progress.add_task(f"Generating branding for {flavor}...", total=None)

        try:
            # Run the original Python script
            result = subprocess.run(
                [sys.executable, str(script_path), flavor],
                cwd=project.path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes timeout
            )

            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Generation timed out (5 minutes)",
                "stdout": "",
                "stderr": "",
            }
        except Exception as e:
            return {"success": False, "error": str(e), "stdout": "", "stderr": ""}
        finally:
            progress.remove_task(task)


def display_branding_results(results: list) -> None:
    """Display branding generation results"""

    successful = 0
    failed = 0

    for flavor_name, result in results:
        if result["success"]:
            successful += 1
            show_success(f"Branding generated for {flavor_name}")
        else:
            failed += 1
            show_error(f"Failed to generate branding for {flavor_name}")

            # Show error details
            if "error" in result:
                console.print(f"  [red]Error: {result['error']}[/red]")
            elif result.get("stderr"):
                console.print(f"  [red]Error: {result['stderr'][:200]}...[/red]")

    # Summary
    total = len(results)
    if failed == 0:
        summary_style = "green"
        summary_icon = "🎉"
        summary_text = f"All {total} flavor(s) completed successfully!"
    elif successful > 0:
        summary_style = "yellow"
        summary_icon = "⚠️"
        summary_text = f"{successful}/{total} flavor(s) completed successfully"
    else:
        summary_style = "red"
        summary_icon = "❌"
        summary_text = "All branding generation failed"

    summary = f"[{summary_style}]{summary_icon} {summary_text}[/{summary_style}]"

    summary_panel = Panel(
        summary, title="📊 Branding Generation Summary", border_style=summary_style, box=box.ROUNDED
    )
    console.print(summary_panel)

    if successful > 0:
        show_next_steps()


def show_flavor_requirements(flavor: str) -> None:
    """Show requirements for a flavor"""

    requirements_text = f"""Required files for flavor '{flavor}':

📁 assets/configs/{flavor}/
  ├── 📄 config.json      (App configuration)
  ├── 🎯 icon.png         (App icon - 1024x1024px)
  └── 💧 splash.png       (Splash screen image)

config.json must contain:
{{
  "appName": "Your App Name",
  "mainColor": "#FF5722",
  "packageName": "com.yourcompany.yourapp"
}}

Icon requirements:
• Format: PNG
• Size: 1024x1024 pixels
• Square aspect ratio
• Transparent background recommended

Splash requirements:
• Format: PNG  
• Minimum size: 1242x2436 pixels
• Can be larger (will be scaled)"""

    requirements_panel = Panel(
        requirements_text, title="📋 Flavor Requirements", border_style="blue", box=box.ROUNDED
    )
    console.print(requirements_panel)


def show_no_flavors_help() -> None:
    """Show help for creating flavors"""

    help_text = """No flavors found in this project.

To create flavors:

1. Create flavor directories:
   [cyan]mkdir -p assets/configs/production
   mkdir -p assets/configs/development[/cyan]

2. Add configuration files:
   [cyan]# assets/configs/production/config.json
   {
     "appName": "MyApp",
     "mainColor": "#2196F3",
     "packageName": "com.company.myapp"
   }[/cyan]

3. Add required images:
   • icon.png (1024x1024px app icon)
   • splash.png (splash screen image)

4. Generate branding:
   [cyan]flow generate branding production[/cyan]"""

    help_panel = Panel(help_text, title="💡 Creating Flavors", border_style="blue", box=box.ROUNDED)
    console.print(help_panel)


def show_next_steps() -> None:
    """Show next steps after successful generation"""

    next_steps_text = """🎉 Branding generation completed!

Next steps:

1. [green]Review generated assets:[/green]
   • Android: android/app/src/[flavor]/res/
   • iOS: ios/Runner/Assets.xcassets/
   • Web: web/icons/ and web/manifest.json

2. [green]Build your app:[/green]
   [cyan]flow android build [flavor][/cyan]

3. [green]Test on devices:[/green]
   [cyan]flow android run [flavor][/cyan]

4. [green]Verify app appearance:[/green]
   • Check app icon on home screen
   • Verify splash screen appears
   • Test app name and branding"""

    next_steps_panel = Panel(
        next_steps_text, title="🚀 Next Steps", border_style="green", box=box.ROUNDED
    )
    console.print(next_steps_panel)

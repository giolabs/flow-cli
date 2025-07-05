"""
Fastlane setup command - Configure Fastlane for Flutter project
"""

import subprocess
import json
from pathlib import Path
from typing import Optional

import click
import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()


@click.command()
@click.option("--force", is_flag=True, help="Force setup even if Fastlane already exists")
@click.option("--skip-branch", is_flag=True, help="Skip creating feature branch")
def setup_fastlane_command(force: bool, skip_branch: bool) -> None:
    """
    ⚙️ Configure Fastlane for Flutter project

    Sets up Fastlane with Flutter-specific configuration for automated
    deployment to Google Play Store and Apple App Store.

    IMPORTANT: This will create a new feature branch to preserve your work.
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Setup Fastlane: {project.name}", "⚙️")

    # Check if Fastlane already exists
    fastfile_path = project.path / "fastlane" / "Fastfile"
    if fastfile_path.exists() and not force:
        show_warning("Fastlane is already configured in this project")
        console.print(
            "Use --force to reconfigure or run 'flow deployment status' to check configuration"
        )
        return

    # Show important warning about branch creation
    if not skip_branch:
        show_branch_warning()
        if not confirm_proceed():
            console.print("[dim]Setup cancelled[/dim]")
            return

        # Create feature branch
        if not create_feature_branch(project):
            show_error("Failed to create feature branch. Setup cancelled.")
            return

    # Check prerequisites
    if not check_prerequisites():
        show_error("Prerequisites check failed")
        return

    # Interactive configuration
    config = interactive_fastlane_config(project)
    if not config:
        return

    # Install and configure Fastlane
    setup_result = setup_fastlane(project, config)

    if setup_result["success"]:
        show_success("Fastlane configured successfully!")
        show_next_steps(project)
    else:
        show_error(f"Fastlane setup failed: {setup_result.get('error', 'Unknown error')}")


def show_branch_warning() -> None:
    """Show warning about creating feature branch"""

    warning_text = """[bold red]⚠️  IMPORTANT SAFETY NOTICE[/bold red]

Setting up Fastlane will modify your project structure and add new files.
To preserve your current work, Flow CLI will:

1. [cyan]Create a new feature branch[/cyan] called 'feature/fastlane-setup'
2. [cyan]Commit current changes[/cyan] (if any) to preserve your work
3. [cyan]Setup Fastlane[/cyan] in the new branch
4. [cyan]Provide merge instructions[/cyan] when complete

This ensures your main branch remains untouched and you can review
all changes before merging.

[bold yellow]Files that will be added/modified:[/bold yellow]
• fastlane/Fastfile
• fastlane/Appfile  
• android/app/build.gradle
• ios/fastlane/ (if iOS setup chosen)
• keys/ directory (for certificates)"""

    panel = Panel(
        warning_text, title="🔒 Branch Safety Protection", border_style="red", box=box.ROUNDED
    )
    console.print(panel)


def confirm_proceed() -> bool:
    """Confirm user wants to proceed with setup"""
    try:
        return inquirer.confirm("Do you want to proceed with Fastlane setup?", default=True)
    except KeyboardInterrupt:
        return False


def create_feature_branch(project: FlutterProject) -> bool:
    """Create feature branch for Fastlane setup"""

    console.print("[cyan]Creating feature branch for Fastlane setup...[/cyan]")

    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "status", "--porcelain"], cwd=project.path, capture_output=True, text=True
        )

        if result.returncode != 0:
            show_warning("Not a git repository. Skipping branch creation.")
            return True

        # Stash any uncommitted changes
        uncommitted = result.stdout.strip()
        if uncommitted:
            console.print("[yellow]Stashing uncommitted changes...[/yellow]")
            subprocess.run(
                ["git", "stash", "push", "-m", "Flow CLI: Pre-Fastlane setup stash"],
                cwd=project.path,
                check=True,
            )

        # Create and switch to feature branch
        branch_name = "feature/fastlane-setup"
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=project.path, check=True)

        show_success(f"Created and switched to branch: {branch_name}")

        # Restore stashed changes if any
        if uncommitted:
            subprocess.run(["git", "stash", "pop"], cwd=project.path, check=True)
            console.print("[green]Restored uncommitted changes[/green]")

        return True

    except subprocess.CalledProcessError as e:
        show_error(f"Git operation failed: {e}")
        return False
    except Exception as e:
        show_error(f"Failed to create feature branch: {e}")
        return False


def check_prerequisites() -> bool:
    """Check if all prerequisites are installed"""

    console.print("[cyan]Checking prerequisites...[/cyan]")

    prerequisites = [
        ("Ruby", check_ruby),
        ("Bundler", check_bundler),
        ("Fastlane", check_fastlane_gem),
    ]

    all_good = True

    for name, check_func in prerequisites:
        if check_func():
            console.print(f"[green]✅ {name} is available[/green]")
        else:
            console.print(f"[red]❌ {name} is not available[/red]")
            all_good = False

    if not all_good:
        show_installation_instructions()

    return all_good


def check_ruby() -> bool:
    """Check if Ruby is installed"""
    try:
        result = subprocess.run(["ruby", "--version"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_bundler() -> bool:
    """Check if Bundler is installed"""
    try:
        result = subprocess.run(["bundle", "--version"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def check_fastlane_gem() -> bool:
    """Check if Fastlane gem is available"""
    try:
        result = subprocess.run(["fastlane", "--version"], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def show_installation_instructions() -> None:
    """Show installation instructions for prerequisites"""

    instructions = """[bold red]Missing Prerequisites[/bold red]

To install the required tools:

[bold cyan]1. Install Ruby (if not available):[/bold cyan]
   # macOS (using Homebrew)
   brew install ruby
   
   # Or use rbenv for version management
   brew install rbenv
   rbenv install 3.0.0
   rbenv global 3.0.0

[bold cyan]2. Install Bundler:[/bold cyan]
   gem install bundler

[bold cyan]3. Install Fastlane:[/bold cyan]
   gem install fastlane

[bold cyan]Alternative - Use Bundler (Recommended):[/bold cyan]
   # Flow CLI will create a Gemfile for you
   # Then run: bundle install

[dim]After installation, run the setup command again.[/dim]"""

    panel = Panel(
        instructions, title="📦 Installation Instructions", border_style="blue", box=box.ROUNDED
    )
    console.print(panel)


def interactive_fastlane_config(project: FlutterProject) -> Optional[dict]:
    """Interactive Fastlane configuration"""

    console.print("\n[bold cyan]🔧 Fastlane Configuration[/bold cyan]")

    try:
        questions = [
            inquirer.Checkbox(
                "platforms",
                message="Select platforms to configure:",
                choices=["Android", "iOS"],
                default=["Android"],
            ),
            inquirer.Text(
                "app_identifier",
                message="App identifier (bundle ID)",
                default=f"com.example.{project.name.lower()}",
            ),
            inquirer.Text(
                "developer_name", message="Developer/Company name", default="Your Company"
            ),
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None

        config = answers.copy()

        # Platform-specific configuration
        if "Android" in config["platforms"]:
            config["android"] = configure_android_settings()

        if "iOS" in config["platforms"]:
            import platform

            if platform.system() == "Darwin":
                config["ios"] = configure_ios_settings()
            else:
                show_warning("iOS configuration skipped (requires macOS)")
                config["platforms"].remove("iOS")

        return config

    except KeyboardInterrupt:
        return None


def configure_android_settings() -> dict:
    """Configure Android-specific settings"""

    console.print("\n[bold green]🤖 Android Configuration[/bold green]")

    try:
        questions = [
            inquirer.Text(
                "package_name", message="Android package name", default="com.example.app"
            ),
            inquirer.List(
                "track",
                message="Default release track",
                choices=["internal", "alpha", "beta", "production"],
                default="internal",
            ),
            inquirer.Confirm(
                "upload_to_play_store",
                message="Configure automatic upload to Play Store?",
                default=True,
            ),
        ]

        return inquirer.prompt(questions) or {}

    except KeyboardInterrupt:
        return {}


def configure_ios_settings() -> dict:
    """Configure iOS-specific settings"""

    console.print("\n[bold blue]🍎 iOS Configuration[/bold blue]")

    try:
        questions = [
            inquirer.Text("team_id", message="Apple Developer Team ID (optional)", default=""),
            inquirer.Text(
                "itc_team_id", message="App Store Connect Team ID (optional)", default=""
            ),
            inquirer.Confirm(
                "upload_to_app_store",
                message="Configure automatic upload to App Store?",
                default=True,
            ),
        ]

        return inquirer.prompt(questions) or {}

    except KeyboardInterrupt:
        return {}


def setup_fastlane(project: FlutterProject, config: dict) -> dict:
    """Setup Fastlane with given configuration"""

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        try:
            # Create fastlane directory
            task = progress.add_task("Creating Fastlane directory...", total=None)
            fastlane_dir = project.path / "fastlane"
            fastlane_dir.mkdir(exist_ok=True)
            progress.update(task, description="✅ Fastlane directory created")
            progress.remove_task(task)

            # Generate Gemfile
            task = progress.add_task("Generating Gemfile...", total=None)
            generate_gemfile(project)
            progress.remove_task(task)

            # Generate Fastfile
            task = progress.add_task("Generating Fastfile...", total=None)
            generate_fastfile(project, config)
            progress.remove_task(task)

            # Generate Appfile
            task = progress.add_task("Generating Appfile...", total=None)
            generate_appfile(project, config)
            progress.remove_task(task)

            # Install dependencies
            task = progress.add_task("Installing Fastlane dependencies...", total=None)
            install_result = install_fastlane_dependencies(project)
            progress.remove_task(task)

            if not install_result["success"]:
                return install_result

            # Configure platform-specific files
            if "Android" in config.get("platforms", []):
                task = progress.add_task("Configuring Android...", total=None)
                configure_android_fastlane(project, config)
                progress.remove_task(task)

            if "iOS" in config.get("platforms", []):
                task = progress.add_task("Configuring iOS...", total=None)
                configure_ios_fastlane(project, config)
                progress.remove_task(task)

            return {"success": True}

        except Exception as e:
            return {"success": False, "error": str(e)}


def generate_gemfile(project: FlutterProject) -> None:
    """Generate Gemfile for Fastlane"""

    gemfile_content = """# Fastlane Gemfile
source "https://rubygems.org"

gem "fastlane"
gem "cocoapods", "~> 1.11" # For iOS dependencies

# Android
gem "google-api-client", "~> 0.53"

# iOS  
gem "spaceship", "~> 1.0"

# Optional but recommended
gem "dotenv"
"""

    gemfile_path = project.path / "Gemfile"
    with open(gemfile_path, "w") as f:
        f.write(gemfile_content)


def generate_fastfile(project: FlutterProject, config: dict) -> None:
    """Generate Fastfile with Flutter configuration"""

    platforms = config.get("platforms", [])

    fastfile_content = f"""# Fastfile for {project.name}
# Generated by Flow CLI

default_platform(:android)

platform :android do
  desc "Build and deploy Android app"
  lane :release do
    flutter_build_android
    upload_to_play_store(
      track: '{config.get("android", {}).get("track", "internal")}',
      aab: './build/app/outputs/bundle/release/app-release.aab'
    )
  end

  desc "Build Android APK"
  lane :build do
    flutter_build_android
  end

  desc "Deploy to internal testing"
  lane :internal do
    flutter_build_android
    upload_to_play_store(
      track: 'internal',
      aab: './build/app/outputs/bundle/release/app-release.aab'
    )
  end
end
"""

    if "iOS" in platforms:
        fastfile_content += """
platform :ios do
  desc "Build and deploy iOS app"
  lane :release do
    setup_ci if ENV['CI']
    match(type: "appstore")
    flutter_build_ios
    build_app(
      workspace: "ios/Runner.xcworkspace",
      scheme: "Runner",
      export_method: "app-store"
    )
    upload_to_app_store
  end

  desc "Build iOS app"
  lane :build do
    setup_ci if ENV['CI']
    match(type: "development")
    flutter_build_ios
    build_app(
      workspace: "ios/Runner.xcworkspace",
      scheme: "Runner",
      export_method: "development"
    )
  end

  desc "Deploy to TestFlight"
  lane :beta do
    setup_ci if ENV['CI']
    match(type: "appstore")
    flutter_build_ios
    build_app(
      workspace: "ios/Runner.xcworkspace",
      scheme: "Runner",
      export_method: "app-store"
    )
    upload_to_testflight
  end
end
"""

    fastfile_content += """
# Helper methods
def flutter_build_android
  sh("flutter build appbundle --release")
end

def flutter_build_ios
  sh("flutter build ios --release --no-codesign")
end
"""

    fastfile_path = project.path / "fastlane" / "Fastfile"
    with open(fastfile_path, "w") as f:
        f.write(fastfile_content)


def generate_appfile(project: FlutterProject, config: dict) -> None:
    """Generate Appfile with app-specific configuration"""

    app_identifier = config.get("app_identifier", f"com.example.{project.name.lower()}")

    appfile_content = f"""# Appfile for {project.name}
# Generated by Flow CLI

app_identifier("{app_identifier}")
apple_dev_portal_id("{config.get('developer_name', 'Your Apple ID')}")
"""

    # Add team IDs if provided
    ios_config = config.get("ios", {})
    if ios_config.get("team_id"):
        appfile_content += f'team_id("{ios_config["team_id"]}")\n'

    if ios_config.get("itc_team_id"):
        appfile_content += f'itc_team_id("{ios_config["itc_team_id"]}")\n'

    appfile_path = project.path / "fastlane" / "Appfile"
    with open(appfile_path, "w") as f:
        f.write(appfile_content)


def install_fastlane_dependencies(project: FlutterProject) -> dict:
    """Install Fastlane dependencies using Bundler"""

    try:
        result = subprocess.run(
            ["bundle", "install"],
            cwd=project.path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minutes
        )

        if result.returncode == 0:
            return {"success": True}
        else:
            return {"success": False, "error": f"Bundle install failed: {result.stderr}"}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Bundle install timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def configure_android_fastlane(project: FlutterProject, config: dict) -> None:
    """Configure Android-specific Fastlane settings"""

    # Create Android fastlane directory
    android_fastlane_dir = project.path / "android" / "fastlane"
    android_fastlane_dir.mkdir(exist_ok=True)

    # Generate Android-specific Appfile
    android_config = config.get("android", {})
    package_name = android_config.get("package_name", config.get("app_identifier"))

    android_appfile = f"""# Android Appfile
json_key_file("../keys/google-play-service-account.json")
package_name("{package_name}")
"""

    with open(android_fastlane_dir / "Appfile", "w") as f:
        f.write(android_appfile)


def configure_ios_fastlane(project: FlutterProject, config: dict) -> None:
    """Configure iOS-specific Fastlane settings"""

    # Create iOS fastlane directory
    ios_fastlane_dir = project.path / "ios" / "fastlane"
    ios_fastlane_dir.mkdir(exist_ok=True)

    # Generate iOS-specific Appfile
    ios_config = config.get("ios", {})
    app_identifier = config.get("app_identifier")

    ios_appfile = f"""# iOS Appfile
app_identifier("{app_identifier}")
"""

    if ios_config.get("team_id"):
        ios_appfile += f'team_id("{ios_config["team_id"]}")\n'

    with open(ios_fastlane_dir / "Appfile", "w") as f:
        f.write(ios_appfile)


def show_next_steps(project: FlutterProject) -> None:
    """Show next steps after Fastlane setup"""

    next_steps = f"""[bold green]🎉 Fastlane Setup Complete![/bold green]

[bold cyan]Next Steps:[/bold cyan]

1. [green]Generate signing certificates:[/green]
   [cyan]flow deployment keystore[/cyan]

2. [green]Test Fastlane configuration:[/green]
   [cyan]cd {project.path}[/cyan]
   [cyan]bundle exec fastlane android build[/cyan]

3. [green]Configure store credentials:[/green]
   • Android: Add Google Play service account JSON
   • iOS: Configure App Store Connect API key

4. [green]Create release:[/green]
   [cyan]flow deployment release[/cyan]

5. [green]Merge feature branch:[/green]
   [cyan]git checkout main[/cyan]
   [cyan]git merge feature/fastlane-setup[/cyan]

[bold yellow]Files Created:[/bold yellow]
• fastlane/Fastfile - Main configuration
• fastlane/Appfile - App settings  
• Gemfile - Ruby dependencies
• android/fastlane/ - Android config
• ios/fastlane/ - iOS config (if applicable)

[dim]Run 'flow deployment status' to check configuration[/dim]"""

    panel = Panel(next_steps, title="🚀 Next Steps", border_style="green", box=box.ROUNDED)
    console.print(panel)

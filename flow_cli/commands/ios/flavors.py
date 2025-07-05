"""
iOS flavors command - View and manage iOS flavors and schemes
"""

import json
import subprocess
import platform
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
@click.option('--flavor', '-f', help='Show details for specific flavor')
@click.option('--schemes', is_flag=True, help='Show Xcode schemes')
def flavors_command(flavor: Optional[str], schemes: bool) -> None:
    """
    🎨 View and manage iOS flavors and schemes
    
    Display available iOS flavors with their configurations, bundle IDs,
    and Xcode schemes. Shows iOS-specific settings and build configurations.
    """
    
    # Check if running on macOS
    if platform.system() != "Darwin":
        show_error("iOS development is only available on macOS")
        return
    
    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()
    
    show_section_header(f"iOS Flavors: {project.name}", "🎨")
    
    if schemes:
        show_xcode_schemes(project)
        return
    
    if not project.flavors:
        show_no_flavors_message()
        return
    
    if flavor:
        show_flavor_details(project, flavor)
    else:
        show_all_ios_flavors(project)

def show_all_ios_flavors(project: FlutterProject) -> None:
    """Show overview of all iOS flavors"""
    
    # Collect iOS flavor information
    flavor_data = []
    for flavor_name in project.flavors:
        data = analyze_ios_flavor(project, flavor_name)
        flavor_data.append(data)
    
    # Main iOS flavors table
    table = Table(title="🍎 iOS Flavors Configuration", box=box.ROUNDED)
    table.add_column("Flavor", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold", no_wrap=True)
    table.add_column("Bundle ID", style="bright_white")
    table.add_column("App Name", style="green")
    table.add_column("Scheme", style="yellow")
    
    complete_count = 0
    
    for data in flavor_data:
        # Status indicator
        if data['ios_configured']:
            status_display = "[green]✅ Configured[/green]"
            complete_count += 1
        else:
            status_display = "[yellow]⚠️ Needs Setup[/yellow]"
        
        # Scheme status
        scheme_status = "✅" if data.get('has_scheme', False) else "❌"
        
        table.add_row(
            data['name'],
            status_display,
            data.get('bundle_id', 'Not set'),
            data.get('app_name', 'Not set'),
            f"{scheme_status} {data.get('scheme_name', 'Missing')}"
        )
    
    console.print(table)
    
    # Summary
    total_flavors = len(flavor_data)
    summary_text = f"[cyan]Total iOS flavors: {total_flavors}[/cyan]"
    if complete_count == total_flavors:
        summary_text += f" | [green]✅ All configured[/green]"
    elif complete_count > 0:
        summary_text += f" | [green]✅ {complete_count} configured[/green], [yellow]⚠️ {total_flavors - complete_count} need setup[/yellow]"
    else:
        summary_text += f" | [red]❌ All need configuration[/red]"
    
    console.print(f"\n{summary_text}")
    
    # Show iOS-specific information
    show_ios_project_info(project)

def show_flavor_details(project: FlutterProject, flavor: str) -> None:
    """Show detailed information for a specific iOS flavor"""
    
    if flavor not in project.flavors:
        show_error(f"Flavor '{flavor}' not found. Available: {', '.join(project.flavors)}")
        return
    
    data = analyze_ios_flavor(project, flavor)
    
    # Flavor header
    console.print(f"\n[bold cyan]🍎 iOS Flavor: {flavor}[/bold cyan]")
    
    # Configuration details
    config_table = Table(title="📋 iOS Configuration", box=box.SIMPLE)
    config_table.add_column("Property", style="cyan")
    config_table.add_column("Value", style="bright_white")
    
    config_table.add_row("App Name", data.get('app_name', 'Not set'))
    config_table.add_row("Bundle ID", data.get('bundle_id', 'Not set'))
    config_table.add_row("Display Name", data.get('display_name', 'Not set'))
    config_table.add_row("Version", data.get('version', 'Not set'))
    config_table.add_row("Build Number", data.get('build_number', 'Not set'))
    config_table.add_row("Scheme Name", data.get('scheme_name', 'Not found'))
    
    console.print(config_table)
    
    # Xcode scheme status
    scheme_table = Table(title="🔧 Xcode Scheme", box=box.SIMPLE)
    scheme_table.add_column("Component", style="cyan")
    scheme_table.add_column("Status", style="bold")
    scheme_table.add_column("Details", style="dim")
    
    scheme_components = [
        ('Scheme File', data['has_scheme'], data.get('scheme_path', '')),
        ('Build Configuration', data.get('has_build_config', False), 'Debug/Release configs'),
        ('Info.plist', data.get('has_info_plist', False), data.get('info_plist_path', '')),
        ('App Icons', data.get('has_app_icons', False), 'iOS app icon sets')
    ]
    
    for component, exists, details in scheme_components:
        status = "[green]✅ Found[/green]" if exists else "[red]❌ Missing[/red]"
        scheme_table.add_row(component, status, details)
    
    console.print(scheme_table)
    
    # Show build targets if available
    if data.get('build_targets'):
        show_build_targets(data['build_targets'])

def analyze_ios_flavor(project: FlutterProject, flavor: str) -> Dict:
    """Analyze iOS flavor configuration"""
    
    ios_dir = project.path / "ios"
    runner_dir = ios_dir / "Runner"
    
    # Load basic config
    flavor_config = load_flavor_config(project, flavor)
    
    # Check for Xcode scheme
    scheme_name = f"Runner-{flavor}" if flavor != "main" else "Runner"
    scheme_path = ios_dir / "Runner.xcodeproj" / "xcshareddata" / "xcschemes" / f"{scheme_name}.xcscheme"
    has_scheme = scheme_path.exists()
    
    # Check Info.plist
    info_plist_path = runner_dir / "Info.plist"
    has_info_plist = info_plist_path.exists()
    
    # Extract Info.plist data
    plist_data = {}
    if has_info_plist:
        plist_data = extract_plist_data(info_plist_path)
    
    # Check app icons
    assets_dir = runner_dir / "Assets.xcassets" / "AppIcon.appiconset"
    has_app_icons = assets_dir.exists() and any(assets_dir.glob("*.png"))
    
    # Determine iOS configuration status
    ios_configured = (
        has_scheme and 
        has_info_plist and 
        plist_data.get('CFBundleIdentifier') and
        plist_data.get('CFBundleDisplayName')
    )
    
    return {
        'name': flavor,
        'ios_configured': ios_configured,
        'app_name': flavor_config.get('appName', ''),
        'bundle_id': plist_data.get('CFBundleIdentifier', flavor_config.get('packageName', '')),
        'display_name': plist_data.get('CFBundleDisplayName', ''),
        'version': plist_data.get('CFBundleShortVersionString', ''),
        'build_number': plist_data.get('CFBundleVersion', ''),
        'scheme_name': scheme_name,
        'scheme_path': str(scheme_path) if has_scheme else '',
        'has_scheme': has_scheme,
        'has_info_plist': has_info_plist,
        'has_app_icons': has_app_icons,
        'info_plist_path': str(info_plist_path) if has_info_plist else '',
        'build_targets': get_build_targets(ios_dir) if has_scheme else []
    }

def load_flavor_config(project: FlutterProject, flavor: str) -> Dict:
    """Load flavor configuration from config.json"""
    config_file = project.path / "assets" / "configs" / flavor / "config.json"
    
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    
    return {}

def extract_plist_data(plist_path: Path) -> Dict:
    """Extract data from Info.plist file"""
    try:
        result = subprocess.run(
            ['plutil', '-convert', 'json', '-o', '-', str(plist_path)],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
    
    except Exception:
        pass
    
    return {}

def get_build_targets(ios_dir: Path) -> List[str]:
    """Get available build targets from Xcode project"""
    try:
        result = subprocess.run(
            ['xcodebuild', '-list', '-project', str(ios_dir / "Runner.xcodeproj")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ios_dir
        )
        
        if result.returncode == 0:
            lines = result.stdout.split('\n')
            targets = []
            in_targets = False
            
            for line in lines:
                line = line.strip()
                if line == "Targets:":
                    in_targets = True
                    continue
                elif line == "Build Configurations:" or line == "Schemes:":
                    in_targets = False
                    continue
                elif in_targets and line:
                    targets.append(line)
            
            return targets
    
    except Exception:
        pass
    
    return []

def show_build_targets(targets: List[str]) -> None:
    """Show available build targets"""
    if targets:
        targets_table = Table(title="🎯 Build Targets", box=box.SIMPLE)
        targets_table.add_column("Target", style="cyan")
        
        for target in targets:
            targets_table.add_row(target)
        
        console.print(targets_table)

def show_xcode_schemes(project: FlutterProject) -> None:
    """Show Xcode schemes"""
    ios_dir = project.path / "ios"
    
    try:
        result = subprocess.run(
            ['xcodebuild', '-list', '-project', str(ios_dir / "Runner.xcodeproj")],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=ios_dir
        )
        
        if result.returncode != 0:
            show_error("Failed to get Xcode schemes")
            return
        
        lines = result.stdout.split('\n')
        schemes = []
        in_schemes = False
        
        for line in lines:
            line = line.strip()
            if line == "Schemes:":
                in_schemes = True
                continue
            elif in_schemes and line:
                schemes.append(line)
        
        if schemes:
            table = Table(title="🔧 Xcode Schemes", box=box.ROUNDED)
            table.add_column("Scheme", style="cyan")
            table.add_column("Status", style="bold")
            
            for scheme in schemes:
                # Check if scheme file exists
                scheme_path = ios_dir / "Runner.xcodeproj" / "xcshareddata" / "xcschemes" / f"{scheme}.xcscheme"
                status = "[green]✅ Available[/green]" if scheme_path.exists() else "[yellow]⚠️ Shared needed[/yellow]"
                table.add_row(scheme, status)
            
            console.print(table)
        else:
            show_warning("No Xcode schemes found")
    
    except Exception as e:
        show_error(f"Error getting Xcode schemes: {str(e)}")

def show_ios_project_info(project: FlutterProject) -> None:
    """Show iOS project information"""
    ios_dir = project.path / "ios"
    
    # Check Xcode project existence
    xcodeproj = ios_dir / "Runner.xcodeproj"
    workspace = ios_dir / "Runner.xcworkspace"
    
    project_info = []
    
    if xcodeproj.exists():
        project_info.append("✅ Xcode project found")
    else:
        project_info.append("❌ Xcode project missing")
    
    if workspace.exists():
        project_info.append("✅ Xcode workspace found")
    else:
        project_info.append("⚠️ Xcode workspace missing (normal)")
    
    # Check Podfile
    podfile = ios_dir / "Podfile"
    if podfile.exists():
        project_info.append("✅ Podfile found")
    else:
        project_info.append("❌ Podfile missing")
    
    # Check CocoaPods
    try:
        result = subprocess.run(['pod', '--version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            pod_version = result.stdout.strip()
            project_info.append(f"✅ CocoaPods v{pod_version}")
        else:
            project_info.append("❌ CocoaPods not found")
    except Exception:
        project_info.append("❌ CocoaPods not found")
    
    if project_info:
        info_text = "\n".join(project_info)
        info_panel = Panel(
            info_text,
            title="🍎 iOS Project Status",
            border_style="blue",
            box=box.ROUNDED
        )
        console.print(info_panel)

def show_no_flavors_message() -> None:
    """Show message when no flavors are found"""
    message = """[yellow]No flavors found in this project.[/yellow]

To set up iOS flavors:

1. [green]Create flavor configurations:[/green]
   [cyan]assets/configs/[flavor-name]/config.json[/cyan]

2. [green]Create Xcode schemes:[/green]
   • Open ios/Runner.xcodeproj in Xcode
   • Duplicate "Runner" scheme
   • Rename to "Runner-[flavor-name]"
   • Configure build settings

3. [green]Set up bundle identifiers:[/green]
   • In Xcode, select target
   • Set different bundle ID for each flavor
   • Configure app name and display name

4. [green]Generate iOS assets:[/green]
   [cyan]flow generate branding [flavor-name][/cyan]

Example flavor config:
[dim]{
  "appName": "MyApp Pro",
  "packageName": "com.company.myapp.pro",
  "mainColor": "#2196F3"
}[/dim]

[cyan]Common iOS commands:[/cyan]
• flow ios schemes              # Show Xcode schemes
• flow ios flavors              # Show flavor status
• open ios/Runner.xcodeproj     # Open in Xcode"""
    
    panel = Panel(
        message,
        title="💡 Setting Up iOS Flavors",
        border_style="blue",
        box=box.ROUNDED
    )
    console.print(panel)
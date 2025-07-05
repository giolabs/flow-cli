"""
Android install command - Install APKs on Android devices
"""

import subprocess
from pathlib import Path
from typing import Optional, List, Dict

import click
import inquirer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error, show_warning

console = Console()

@click.command()
@click.option('--apk', help='Path to APK file to install')
@click.option('--flavor', '-f', help='Install APK for specific flavor')
@click.option('--all', is_flag=True, help='Install all available APKs')
def install_command(apk: Optional[str], flavor: Optional[str], all: bool) -> None:
    """
    📱 Install APK on connected Android devices
    
    Install APK files on all connected Android devices and emulators.
    Supports automatic APK detection or manual APK file specification.
    """
    
    show_section_header("Install APK on Android Devices", "📱")
    
    # Check for connected devices
    devices = get_connected_devices()
    if not devices:
        show_error("No Android devices connected. Connect a device or start an emulator.")
        raise click.Abort()
    
    console.print(f"[green]Found {len(devices)} connected device(s):[/green]")
    for device in devices:
        console.print(f"  📱 {device['name']} ({device['id']})")
    console.print()
    
    # Find Flutter project for APK detection
    project = FlutterProject.find_project()
    
    # Determine APKs to install
    apks_to_install = []
    
    if apk:
        # Specific APK file provided
        apk_path = Path(apk)
        if not apk_path.exists():
            show_error(f"APK file not found: {apk}")
            raise click.Abort()
        apks_to_install.append(apk_path)
    elif all and project:
        # Install all available APKs
        apks_to_install = find_all_apks(project)
    elif flavor and project:
        # Install specific flavor APK
        flavor_apk = find_flavor_apk(project, flavor)
        if flavor_apk:
            apks_to_install.append(flavor_apk)
        else:
            show_error(f"APK for flavor '{flavor}' not found")
            raise click.Abort()
    else:
        # Interactive selection
        if project:
            apks_to_install = interactive_apk_selection(project)
        else:
            show_error("No Flutter project found and no APK specified")
            raise click.Abort()
    
    if not apks_to_install:
        show_warning("No APKs selected for installation")
        return
    
    # Install APKs
    install_apks_on_devices(apks_to_install, devices)

def get_connected_devices() -> List[Dict[str, str]]:
    """Get list of connected Android devices"""
    try:
        result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
        devices = []
        
        lines = result.stdout.strip().split('\n')
        for line in lines[1:]:  # Skip header
            if line.strip() and 'device' in line:
                device_id = line.split()[0]
                
                # Get device name
                name_result = subprocess.run(
                    ['adb', '-s', device_id, 'shell', 'getprop', 'ro.product.model'],
                    capture_output=True, text=True
                )
                device_name = name_result.stdout.strip() if name_result.returncode == 0 else device_id
                
                devices.append({
                    'id': device_id,
                    'name': device_name,
                    'status': 'device'
                })
        
        return devices
    except FileNotFoundError:
        show_error("ADB not found. Make sure Android SDK is installed and adb is in PATH.")
        return []
    except Exception:
        return []

def find_all_apks(project: FlutterProject) -> List[Path]:
    """Find all APK files in the project"""
    apk_dir = project.path / "build" / "app" / "outputs" / "flutter-apk"
    if not apk_dir.exists():
        return []
    
    return list(apk_dir.glob("*.apk"))

def find_flavor_apk(project: FlutterProject, flavor: str) -> Optional[Path]:
    """Find APK for specific flavor"""
    apk_dir = project.path / "build" / "app" / "outputs" / "flutter-apk"
    
    # Try different naming patterns
    possible_names = [
        f"app-{flavor}-debug.apk",
        f"app-{flavor}-release.apk",
        f"app-{flavor}-profile.apk"
    ]
    
    for name in possible_names:
        apk_path = apk_dir / name
        if apk_path.exists():
            return apk_path
    
    return None

def interactive_apk_selection(project: FlutterProject) -> List[Path]:
    """Interactive APK selection"""
    available_apks = find_all_apks(project)
    
    if not available_apks:
        show_warning("No APK files found. Build your app first.")
        return []
    
    # Create choices with APK info
    choices = []
    for apk in available_apks:
        size_mb = round(apk.stat().st_size / (1024 * 1024), 2)
        flavor_info = extract_flavor_from_filename(apk.name)
        choice_text = f"{apk.name} ({size_mb} MB)"
        if flavor_info:
            choice_text += f" - {flavor_info}"
        choices.append((choice_text, apk))
    
    choices.append(("All APKs", "all"))
    
    try:
        questions = [
            inquirer.Checkbox(
                'apks',
                message="Select APK(s) to install:",
                choices=[choice[0] for choice in choices]
            )
        ]
        
        answers = inquirer.prompt(questions)
        if not answers or not answers['apks']:
            return []
        
        selected_apks = []
        for selection in answers['apks']:
            if selection == "All APKs":
                return available_apks
            else:
                # Find corresponding APK
                for choice_text, apk in choices:
                    if choice_text == selection:
                        selected_apks.append(apk)
                        break
        
        return selected_apks
    except KeyboardInterrupt:
        return []

def extract_flavor_from_filename(filename: str) -> Optional[str]:
    """Extract flavor information from APK filename"""
    if 'debug' in filename:
        return 'Debug build'
    elif 'release' in filename:
        return 'Release build'
    elif 'profile' in filename:
        return 'Profile build'
    return None

def install_apks_on_devices(apks: List[Path], devices: List[Dict[str, str]]) -> None:
    """Install APKs on all connected devices"""
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        total_installations = len(apks) * len(devices)
        completed_installations = 0
        failed_installations = []
        
        for apk in apks:
            console.print(f"\n[cyan]Installing {apk.name}...[/cyan]")
            
            for device in devices:
                task = progress.add_task(f"Installing on {device['name']}...", total=None)
                
                try:
                    result = subprocess.run(
                        ['adb', '-s', device['id'], 'install', '-r', str(apk)],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if result.returncode == 0:
                        completed_installations += 1
                        show_success(f"Installed on {device['name']}")
                    else:
                        failed_installations.append((apk.name, device['name'], result.stderr))
                        show_error(f"Failed to install on {device['name']}")
                
                except subprocess.TimeoutExpired:
                    failed_installations.append((apk.name, device['name'], "Installation timed out"))
                    show_error(f"Installation timed out on {device['name']}")
                except Exception as e:
                    failed_installations.append((apk.name, device['name'], str(e)))
                    show_error(f"Installation error on {device['name']}: {str(e)}")
                finally:
                    progress.remove_task(task)
    
    # Display summary
    display_installation_summary(completed_installations, total_installations, failed_installations)

def display_installation_summary(completed: int, total: int, failed: List[tuple]) -> None:
    """Display installation summary"""
    
    # Summary table
    summary_table = Table(title="📊 Installation Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Value", style="bright_white")
    
    success_rate = (completed / total * 100) if total > 0 else 0
    
    summary_table.add_row("Total Installations", str(total))
    summary_table.add_row("Successful", f"[green]{completed}[/green]")
    summary_table.add_row("Failed", f"[red]{len(failed)}[/red]")
    summary_table.add_row("Success Rate", f"{success_rate:.1f}%")
    
    console.print(summary_table)
    
    # Show failed installations details
    if failed:
        console.print("\n[red]❌ Failed Installations:[/red]")
        for apk_name, device_name, error in failed:
            console.print(f"  • {apk_name} on {device_name}: {error}")
    
    if completed == total:
        show_success("All installations completed successfully! 🎉")
    elif completed > 0:
        show_warning(f"{completed}/{total} installations completed")
    else:
        show_error("All installations failed")
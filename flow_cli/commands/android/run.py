"""
Android run command - Run Flutter app on Android devices
"""

import subprocess
from typing import Optional, List, Dict

import click
import inquirer
from rich.console import Console

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_section_header, show_success, show_error

console = Console()

@click.command()
@click.option('--flavor', '-f', help='Flavor to run')
@click.option('--device', '-d', help='Device ID to run on')
def run_command(flavor: Optional[str], device: Optional[str]) -> None:
    """
    ▶️ Run Flutter app on Android device or emulator
    
    Launches your Flutter app on a connected Android device or emulator
    with support for hot reload and debugging.
    """
    
    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()
    
    show_section_header(f"Running: {project.name}", "▶️")
    
    # Interactive selection if needed
    if not device:
        devices = get_android_devices()
        if not devices:
            show_error("No Android devices found. Connect a device or start an emulator.")
            raise click.Abort()
        
        device = select_device(devices)
        if not device:
            return
    
    if not flavor and project.flavors:
        flavor = select_flavor(project.flavors)
        if not flavor:
            return
    
    # Run the app
    run_flutter_app(project, flavor, device)

def get_android_devices() -> List[Dict[str, str]]:
    """Get list of connected Android devices"""
    try:
        result = subprocess.run(['flutter', 'devices'], capture_output=True, text=True)
        devices = []
        
        for line in result.stdout.split('\n'):
            if 'android' in line.lower() and '•' in line:
                parts = line.split('•')
                if len(parts) >= 3:
                    name = parts[0].strip()
                    device_id = parts[1].strip()
                    devices.append({
                        'name': name,
                        'id': device_id,
                        'platform': 'android'
                    })
        
        return devices
    except Exception:
        return []

def select_device(devices: List[Dict[str, str]]) -> Optional[str]:
    """Interactive device selection"""
    choices = [f"{device['name']} ({device['id']})" for device in devices]
    
    try:
        questions = [
            inquirer.List(
                'device',
                message="Select Android device:",
                choices=choices
            )
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return None
        
        # Extract device ID from selection
        selected = answers['device']
        for device in devices:
            if device['id'] in selected:
                return device['id']
        
        return None
    except KeyboardInterrupt:
        return None

def select_flavor(flavors: List[str]) -> Optional[str]:
    """Interactive flavor selection"""
    choices = flavors + ["Default (no flavor)"]
    
    try:
        questions = [
            inquirer.List(
                'flavor',
                message="Select flavor:",
                choices=choices
            )
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return None
        
        selected = answers['flavor']
        return None if selected == "Default (no flavor)" else selected
    except KeyboardInterrupt:
        return None

def run_flutter_app(project: FlutterProject, flavor: Optional[str], device: str) -> None:
    """Run Flutter app with specified parameters"""
    
    cmd = ['flutter', 'run']
    
    if device:
        cmd.extend(['-d', device])
    
    if flavor:
        cmd.extend(['--flavor', flavor])
    
    console.print(f"[cyan]Running on device: {device}[/cyan]")
    if flavor:
        console.print(f"[cyan]Using flavor: {flavor}[/cyan]")
    
    console.print("\n[yellow]Press 'q' to quit, 'r' to hot reload, 'R' to hot restart[/yellow]\n")
    
    try:
        subprocess.run(cmd, cwd=project.path)
    except KeyboardInterrupt:
        console.print("\n[dim]App stopped[/dim]")
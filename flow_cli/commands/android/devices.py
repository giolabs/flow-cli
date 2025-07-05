"""
Android devices command - Manage Android devices and emulators
"""

import subprocess
from typing import List, Dict

import click
from rich.console import Console
from rich.table import Table
from rich import box

from flow_cli.core.ui.banner import show_section_header, show_success, show_error

console = Console()

@click.command()
def devices_command() -> None:
    """
    🔌 Manage Android devices and emulators
    
    Shows connected Android devices and running emulators with detailed
    information including device specs and status.
    """
    
    show_section_header("Android Devices & Emulators", "🔌")
    
    # Get connected devices
    devices = get_all_devices()
    
    if not devices:
        show_error("No Android devices or emulators found")
        console.print("\n[dim]To connect a device:[/dim]")
        console.print("  1. Enable Developer Options and USB Debugging")
        console.print("  2. Connect via USB cable")
        console.print("  3. Accept debugging authorization on device")
        console.print("\n[dim]To start an emulator:[/dim]")
        console.print("  flutter emulators --launch <emulator-id>")
        return
    
    display_devices_table(devices)

def get_all_devices() -> List[Dict[str, str]]:
    """Get all Android devices and emulators"""
    devices = []
    
    # Get connected devices via adb
    try:
        result = subprocess.run(['adb', 'devices', '-l'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        for line in lines[1:]:  # Skip header
            if line.strip() and not line.startswith('*'):
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    status = parts[1]
                    
                    # Extract additional info
                    device_info = ' '.join(parts[2:]) if len(parts) > 2 else ''
                    
                    # Get device properties
                    device_data = get_device_properties(device_id)
                    device_data.update({
                        'id': device_id,
                        'status': status,
                        'info': device_info,
                        'type': 'emulator' if 'emulator' in device_id else 'device'
                    })
                    
                    devices.append(device_data)
    
    except FileNotFoundError:
        show_error("ADB not found. Install Android SDK and add to PATH.")
    except Exception as e:
        show_error(f"Error getting devices: {str(e)}")
    
    return devices

def get_device_properties(device_id: str) -> Dict[str, str]:
    """Get device properties via adb"""
    properties = {}
    
    prop_commands = {
        'name': 'ro.product.model',
        'manufacturer': 'ro.product.manufacturer', 
        'android_version': 'ro.build.version.release',
        'api_level': 'ro.build.version.sdk',
        'architecture': 'ro.product.cpu.abi',
    }
    
    for prop_name, prop_key in prop_commands.items():
        try:
            result = subprocess.run(
                ['adb', '-s', device_id, 'shell', 'getprop', prop_key],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                properties[prop_name] = result.stdout.strip()
            else:
                properties[prop_name] = 'Unknown'
                
        except Exception:
            properties[prop_name] = 'Unknown'
    
    return properties

def display_devices_table(devices: List[Dict[str, str]]) -> None:
    """Display devices in a formatted table"""
    
    table = Table(title="🔌 Android Devices & Emulators", box=box.ROUNDED)
    table.add_column("Device", style="cyan", no_wrap=True)
    table.add_column("Type", style="bright_white", no_wrap=True)
    table.add_column("Status", style="bold", no_wrap=True)
    table.add_column("Android", style="green")
    table.add_column("Architecture", style="yellow")
    table.add_column("ID", style="dim")
    
    emulator_count = 0
    device_count = 0
    
    for device in devices:
        # Device type icon and count
        if device['type'] == 'emulator':
            type_display = "🖥️ Emulator"
            emulator_count += 1
        else:
            type_display = "📱 Physical"
            device_count += 1
        
        # Status styling
        status = device['status']
        if status == 'device':
            status_display = "[green]✅ Ready[/green]"
        elif status == 'unauthorized':
            status_display = "[yellow]⚠️ Unauthorized[/yellow]"
        elif status == 'offline':
            status_display = "[red]❌ Offline[/red]"
        else:
            status_display = f"[dim]{status}[/dim]"
        
        # Device name with manufacturer
        device_name = device.get('name', 'Unknown')
        manufacturer = device.get('manufacturer', '')
        if manufacturer and manufacturer != 'Unknown':
            device_display = f"{manufacturer} {device_name}"
        else:
            device_display = device_name
        
        # Android version display
        android_version = device.get('android_version', 'Unknown')
        api_level = device.get('api_level', '')
        if api_level and api_level != 'Unknown':
            android_display = f"{android_version} (API {api_level})"
        else:
            android_display = android_version
        
        table.add_row(
            device_display,
            type_display,
            status_display,
            android_display,
            device.get('architecture', 'Unknown'),
            device['id']
        )
    
    console.print(table)
    
    # Summary
    total_devices = len(devices)
    ready_devices = sum(1 for d in devices if d['status'] == 'device')
    
    summary_text = f"[cyan]Total: {total_devices} devices[/cyan]"
    if device_count > 0:
        summary_text += f" | [green]📱 {device_count} physical[/green]"
    if emulator_count > 0:
        summary_text += f" | [blue]🖥️ {emulator_count} emulators[/blue]"
    if ready_devices > 0:
        summary_text += f" | [green]✅ {ready_devices} ready[/green]"
    
    console.print(f"\n{summary_text}")
    
    # Show tips for unauthorized devices
    unauthorized_devices = [d for d in devices if d['status'] == 'unauthorized']
    if unauthorized_devices:
        console.print("\n[yellow]💡 Tips for unauthorized devices:[/yellow]")
        console.print("  • Check device screen for USB debugging authorization dialog")
        console.print("  • Try: adb kill-server && adb start-server")
        console.print("  • Reconnect USB cable")
    
    # Show available emulators if no emulators running
    if emulator_count == 0:
        show_available_emulators()

def show_available_emulators() -> None:
    """Show available emulators that can be started"""
    try:
        result = subprocess.run(['flutter', 'emulators'], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout.strip():
            emulator_lines = [line.strip() for line in result.stdout.split('\n') if line.strip() and '•' in line]
            
            if emulator_lines:
                console.print("\n[cyan]📱 Available emulators:[/cyan]")
                for line in emulator_lines:
                    console.print(f"  {line}")
                console.print("\n[dim]Start an emulator with: flutter emulators --launch <emulator-id>[/dim]")
    
    except Exception:
        pass  # Silently ignore if flutter emulators command fails
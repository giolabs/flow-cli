"""
iOS devices command - Manage iOS devices and simulators
"""

import json
import platform
import subprocess
from typing import Dict, List, Optional

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()


@click.command()
@click.option("--start", help="Start specific simulator by name or UDID")
@click.option("--shutdown", help="Shutdown specific simulator by name or UDID")
@click.option("--list-runtimes", is_flag=True, help="List available iOS runtimes")
def devices_command(start: Optional[str], shutdown: Optional[str], list_runtimes: bool) -> None:
    """
    🔌 Manage iOS devices and simulators

    Shows connected iOS devices and available simulators with detailed
    information including iOS versions, device types, and status.

    Supports starting and stopping simulators directly.
    """

    # Check if running on macOS
    if platform.system() != "Darwin":
        show_error("iOS development is only available on macOS")
        return

    show_section_header("iOS Devices & Simulators", "🔌")

    # Handle specific actions
    if start:
        start_simulator(start)
        return

    if shutdown:
        shutdown_simulator(shutdown)
        return

    if list_runtimes:
        show_ios_runtimes()
        return

    # Get all devices and simulators
    simulators = get_simulators()
    physical_devices = get_physical_devices()

    if not simulators and not physical_devices:
        show_no_devices_message()
        return

    # Display devices
    if physical_devices:
        display_physical_devices(physical_devices)

    if simulators:
        display_simulators(simulators)

    show_device_summary(simulators, physical_devices)


def get_simulators() -> List[Dict]:
    """Get list of iOS simulators"""
    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return []

        data = json.loads(result.stdout)
        simulators = []

        for runtime, devices in data.get("devices", {}).items():
            # Skip non-iOS runtimes
            if "iOS" not in runtime and "watchOS" not in runtime and "tvOS" not in runtime:
                continue

            runtime_name = runtime.replace("com.apple.CoreSimulator.SimRuntime.", "").replace(
                "-", " "
            )

            for device in devices:
                if device.get("isAvailable", False):  # Only show available simulators
                    simulators.append(
                        {
                            "name": device["name"],
                            "udid": device["udid"],
                            "state": device["state"],
                            "runtime": runtime_name,
                            "device_type": device.get("deviceTypeIdentifier", "").split(".")[-1],
                            "is_simulator": True,
                        }
                    )

        return simulators

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        return []


def get_physical_devices() -> List[Dict]:
    """Get list of connected physical iOS devices"""
    try:
        # Check for connected iOS devices via flutter
        result = subprocess.run(
            ["flutter", "devices", "--machine"], capture_output=True, text=True, timeout=10
        )

        if result.returncode != 0:
            return []

        devices_data = json.loads(result.stdout)
        ios_devices = []

        for device in devices_data:
            if device.get("platform") == "ios" and not device.get("emulator", False):
                ios_devices.append(
                    {
                        "name": device["name"],
                        "id": device["id"],
                        "platform_type": device.get("platformType", "ios"),
                        "sdk": device.get("sdk", "Unknown"),
                        "is_simulator": False,
                    }
                )

        return ios_devices

    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
        # Fallback: try using instruments
        try:
            result = subprocess.run(
                ["instruments", "-s", "devices"], capture_output=True, text=True, timeout=10
            )

            devices = []
            if result.returncode == 0:
                lines = result.stdout.split("\n")
                for line in lines:
                    # Look for iOS device pattern: "Device Name (iOS Version) [UDID]"
                    if "[" in line and "]" in line and "iOS" in line and "Simulator" not in line:
                        parts = line.split("[")
                        if len(parts) >= 2:
                            name_version = parts[0].strip()
                            udid = parts[1].split("]")[0]

                            devices.append(
                                {
                                    "name": name_version,
                                    "id": udid,
                                    "platform_type": "ios",
                                    "sdk": "Unknown",
                                    "is_simulator": False,
                                }
                            )

            return devices
        except Exception:
            return []


def display_physical_devices(devices: List[Dict]) -> None:
    """Display physical iOS devices"""

    table = Table(title="📱 Physical iOS Devices", box=box.ROUNDED)
    table.add_column("Device", style="cyan", no_wrap=True)
    table.add_column("Platform", style="bright_white")
    table.add_column("SDK Version", style="green")
    table.add_column("Device ID", style="dim")

    for device in devices:
        table.add_row(
            f"📱 {device['name']}",
            device.get("platform_type", "ios").upper(),
            device.get("sdk", "Unknown"),
            device["id"][:8] + "..." if len(device["id"]) > 8 else device["id"],
        )

    console.print(table)


def display_simulators(simulators: List[Dict]) -> None:
    """Display iOS simulators grouped by runtime"""

    # Group simulators by runtime
    by_runtime: Dict[str, List[Dict]] = {}
    for sim in simulators:
        runtime = sim["runtime"]
        if runtime not in by_runtime:
            by_runtime[runtime] = []
        by_runtime[runtime].append(sim)

    # Sort runtimes (newest first)
    sorted_runtimes = sorted(by_runtime.keys(), reverse=True)

    for runtime in sorted_runtimes:
        runtime_sims = by_runtime[runtime]

        table = Table(title=f"📱 {runtime} Simulators", box=box.ROUNDED)
        table.add_column("Device", style="cyan", no_wrap=True)
        table.add_column("Status", style="bold", no_wrap=True)
        table.add_column("Device Type", style="bright_white")
        table.add_column("UDID", style="dim")

        for sim in sorted(runtime_sims, key=lambda x: x["name"]):
            # Status styling
            state = sim["state"]
            if state == "Booted":
                status_display = "[green]🟢 Running[/green]"
            elif state == "Shutdown":
                status_display = "[dim]⚫ Stopped[/dim]"
            else:
                status_display = f"[yellow]⚠️ {state}[/yellow]"

            # Device icon based on type
            device_type = sim.get("device_type", "")
            if "iPad" in device_type:
                device_icon = "📱"
            elif "iPhone" in device_type:
                device_icon = "📱"
            elif "Apple-Watch" in device_type:
                device_icon = "⌚"
            elif "Apple-TV" in device_type:
                device_icon = "📺"
            else:
                device_icon = "📱"

            table.add_row(
                f"{device_icon} {sim['name']}",
                status_display,
                device_type.replace("-", " "),
                sim["udid"][:8] + "...",
            )

        console.print(table)


def show_device_summary(simulators: List[Dict], physical_devices: List[Dict]) -> None:
    """Show device summary and tips"""

    # Count by status
    running_sims = sum(1 for sim in simulators if sim["state"] == "Booted")
    total_sims = len(simulators)
    total_physical = len(physical_devices)

    summary_text = f"[cyan]Total devices: {total_physical + total_sims}[/cyan]"
    if total_physical > 0:
        summary_text += f" | [green]📱 {total_physical} physical[/green]"
    if total_sims > 0:
        summary_text += f" | [blue]🖥️ {total_sims} simulators[/blue]"
    if running_sims > 0:
        summary_text += f" | [green]🟢 {running_sims} running[/green]"

    console.print(f"\n{summary_text}")

    # Show quick commands
    if total_sims > 0:
        console.print("\n[cyan]💡 Quick actions:[/cyan]")
        console.print('  • Start simulator: [dim]flow ios devices --start "iPhone 15"[/dim]')
        console.print('  • Shutdown simulator: [dim]flow ios devices --shutdown "iPhone 15"[/dim]')
        console.print("  • List runtimes: [dim]flow ios devices --list-runtimes[/dim]")
        console.print("  • Run on simulator: [dim]flow ios run[/dim]")


def start_simulator(identifier: str) -> None:
    """Start a specific simulator"""

    # Find simulator by name or UDID
    simulators = get_simulators()
    target_sim = None

    for sim in simulators:
        if identifier in sim["name"] or identifier == sim["udid"]:
            target_sim = sim
            break

    if not target_sim:
        show_error(f"Simulator '{identifier}' not found")
        console.print("\n[dim]Available simulators:[/dim]")
        for sim in simulators[:5]:  # Show first 5
            console.print(f"  • {sim['name']} ({sim['runtime']})")
        return

    if target_sim["state"] == "Booted":
        show_warning(f"Simulator '{target_sim['name']}' is already running")
        return

    console.print(f"[cyan]Starting simulator: {target_sim['name']}...[/cyan]")

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "boot", target_sim["udid"]],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            show_success(f"Simulator '{target_sim['name']}' started successfully")

            # Try to open Simulator.app
            subprocess.run(["open", "-a", "Simulator"], capture_output=True)
        else:
            show_error(f"Failed to start simulator: {result.stderr}")

    except subprocess.TimeoutExpired:
        show_error("Simulator startup timed out")
    except Exception as e:
        show_error(f"Error starting simulator: {str(e)}")


def shutdown_simulator(identifier: str) -> None:
    """Shutdown a specific simulator"""

    # Find simulator by name or UDID
    simulators = get_simulators()
    target_sim = None

    for sim in simulators:
        if identifier in sim["name"] or identifier == sim["udid"]:
            target_sim = sim
            break

    if not target_sim:
        show_error(f"Simulator '{identifier}' not found")
        return

    if target_sim["state"] != "Booted":
        show_warning(f"Simulator '{target_sim['name']}' is not running")
        return

    console.print(f"[cyan]Shutting down simulator: {target_sim['name']}...[/cyan]")

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "shutdown", target_sim["udid"]],
            capture_output=True,
            text=True,
            timeout=15,
        )

        if result.returncode == 0:
            show_success(f"Simulator '{target_sim['name']}' shutdown successfully")
        else:
            show_error(f"Failed to shutdown simulator: {result.stderr}")

    except subprocess.TimeoutExpired:
        show_error("Simulator shutdown timed out")
    except Exception as e:
        show_error(f"Error shutting down simulator: {str(e)}")


def show_ios_runtimes() -> None:
    """Show available iOS runtimes"""

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "runtimes", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            show_error("Failed to get iOS runtimes")
            return

        data = json.loads(result.stdout)
        runtimes = data.get("runtimes", [])

        # Filter iOS runtimes
        ios_runtimes = [r for r in runtimes if "iOS" in r.get("name", "")]

        if not ios_runtimes:
            show_warning("No iOS runtimes found")
            return

        table = Table(title="📱 Available iOS Runtimes", box=box.ROUNDED)
        table.add_column("Runtime", style="cyan")
        table.add_column("Version", style="bright_white")
        table.add_column("Build", style="green")
        table.add_column("Available", style="bold")

        for runtime in sorted(ios_runtimes, key=lambda x: x.get("version", ""), reverse=True):
            available = "✅ Yes" if runtime.get("isAvailable", False) else "❌ No"

            table.add_row(
                runtime.get("name", "Unknown"),
                runtime.get("version", "Unknown"),
                runtime.get("buildversion", "Unknown"),
                available,
            )

        console.print(table)

    except Exception as e:
        show_error(f"Error getting runtimes: {str(e)}")


def show_no_devices_message() -> None:
    """Show message when no devices are found"""

    message = """[yellow]No iOS devices or simulators found.[/yellow]

To set up iOS development:

1. [green]Install Xcode:[/green]
   Download from Mac App Store or Apple Developer Portal

2. [green]Install iOS Simulators:[/green]
   • Open Xcode
   • Go to Xcode → Preferences → Components
   • Download iOS Simulator runtimes

3. [green]Connect physical device:[/green]
   • Connect iPhone/iPad via USB
   • Trust computer on device
   • Enable Developer Mode (iOS 16+)

4. [green]Create simulators:[/green]
   • Open Xcode → Window → Devices and Simulators
   • Click '+' to add simulator

[dim]Common commands:[/dim]
• xcrun simctl list devices
• open -a Simulator
• instruments -s devices"""

    panel = Panel(message, title="💡 iOS Development Setup", border_style="blue", box=box.ROUNDED)
    console.print(panel)

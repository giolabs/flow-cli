"""
iOS run command - Run Flutter app on iOS simulators and devices
"""
# mypy: ignore-errors

import json
import platform
import subprocess
from typing import Dict, List, Optional

import click
import inquirer
from rich.console import Console

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Flavor to run")
@click.option("--device", "-d", help="Device ID or name to run on")
@click.option("--release", is_flag=True, help="Run in release mode")
def run_command(flavor: Optional[str], device: Optional[str], release: bool) -> None:
    """
    ▶️ Run Flutter app on iOS simulator or device

    Launches your Flutter app on an iOS simulator or connected device
    with support for hot reload, debugging, and flavor selection.
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

    show_section_header(f"Running iOS App: {project.name}", "▶️")

    # Get available devices
    ios_devices = get_ios_devices()
    if not ios_devices:
        show_error("No iOS devices or simulators available")
        show_setup_instructions()
        raise click.Abort()

    # Interactive device selection if needed
    if not device:
        device = select_ios_device(ios_devices)
        if not device:
            return
    else:
        # Validate provided device
        if not validate_device(device, ios_devices):
            show_error(f"Device '{device}' not found or not available")
            show_available_devices(ios_devices)
            raise click.Abort()

    # Interactive flavor selection if needed
    if not flavor and project.flavors:
        flavor = select_flavor(project.flavors)
        if not flavor:
            return

    # Ensure simulator is booted if it's a simulator
    selected_device = get_device_by_identifier(device, ios_devices)
    if selected_device and selected_device.get("is_simulator", False):
        if not ensure_simulator_running(selected_device):
            show_error("Failed to start simulator")
            raise click.Abort()

    # Run the Flutter app
    run_flutter_app(project, flavor, device, release)


def get_ios_devices() -> List[Dict]:
    """Get list of available iOS devices and simulators"""
    devices = []

    try:
        # Get Flutter devices
        result = subprocess.run(
            ["flutter", "devices", "--machine"], capture_output=True, text=True, timeout=15
        )

        if result.returncode == 0:
            flutter_devices = json.loads(result.stdout)
            for device in flutter_devices:
                if device.get("platform") == "ios":
                    devices.append(
                        {
                            "id": device["id"],
                            "name": device["name"],
                            "platform": device.get("platform", "ios"),
                            "is_simulator": device.get("emulator", False),
                            "sdk": device.get("sdk", "Unknown"),
                            "available": True,
                        }
                    )

    except Exception:
        # Fallback: get simulators directly
        devices.extend(get_simulators_direct())

    return devices


def get_simulators_direct() -> List[Dict]:
    """Get simulators directly using simctl"""
    simulators = []

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "available", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)

            for runtime, devices in data.get("devices", {}).items():
                if "iOS" not in runtime:
                    continue

                runtime_name = runtime.replace("com.apple.CoreSimulator.SimRuntime.", "").replace(
                    "-", " "
                )

                for device in devices:
                    if device.get("isAvailable", False):
                        simulators.append(
                            {
                                "id": device["udid"],
                                "name": f"{device['name']} ({runtime_name})",
                                "platform": "ios",
                                "is_simulator": True,
                                "state": device.get("state", "Shutdown"),
                                "runtime": runtime_name,
                                "available": True,
                            }
                        )

    except Exception:
        pass

    return simulators


def select_ios_device(devices: List[Dict]) -> Optional[str]:
    """Interactive iOS device selection"""

    # Separate physical devices and simulators
    physical_devices = [d for d in devices if not d.get("is_simulator", False)]
    simulators = [d for d in devices if d.get("is_simulator", False)]

    choices = []

    # Add physical devices first
    if physical_devices:
        choices.append("--- Physical Devices ---")
        for device in physical_devices:
            choice_text = f"📱 {device['name']} (Physical)"
            choices.append((choice_text, device["id"]))  # type: ignore

    # Add simulators
    if simulators:
        if physical_devices:
            choices.append("--- Simulators ---")

        # Group simulators by runtime
        by_runtime: Dict[str, List[Dict]] = {}
        for sim in simulators:
            runtime = sim.get("runtime", "Unknown")
            if runtime not in by_runtime:
                by_runtime[runtime] = []
            by_runtime[runtime].append(sim)

        # Sort and add simulators
        for runtime in sorted(by_runtime.keys(), reverse=True):
            for sim in sorted(by_runtime[runtime], key=lambda x: x["name"]):
                status_icon = "🟢" if sim.get("state") == "Booted" else "⚫"
                choice_text = f"{status_icon} {sim['name']}"
                choices.append((choice_text, sim["id"]))  # type: ignore

    if not choices:
        return None

    try:
        # Filter out separator lines for inquirer
        inquirer_choices = []
        choice_map: Dict[str, str] = {}

        for item in choices:
            if isinstance(item, tuple):
                text, device_id = item
                inquirer_choices.append(text)
                choice_map[text] = device_id
            else:
                inquirer_choices.append(item)  # Separator

        questions = [
            inquirer.List(
                "device", message="Select iOS device or simulator:", choices=inquirer_choices
            )
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None

        selection = answers["device"]

        # Skip separators
        if selection.startswith("---"):
            return None

        return choice_map.get(selection)

    except KeyboardInterrupt:
        return None


def select_flavor(flavors: List[str]) -> Optional[str]:
    """Interactive flavor selection"""
    choices = flavors + ["Default (no flavor)"]

    try:
        questions = [
            inquirer.List("flavor", message="Select flavor:", choices=choices, default=choices[0])
        ]

        answers = inquirer.prompt(questions)
        if not answers:
            return None

        selected = answers["flavor"]
        return None if selected == "Default (no flavor)" else selected

    except KeyboardInterrupt:
        return None


def validate_device(device_identifier: str, devices: List[Dict]) -> bool:
    """Validate that device exists and is available"""
    for device in devices:
        if device_identifier in [device["id"], device["name"]]:
            return device.get("available", False)
    return False


def get_device_by_identifier(device_identifier: str, devices: List[Dict]) -> Optional[Dict]:
    """Get device info by ID or name"""
    for device in devices:
        if device_identifier in [device["id"], device["name"]]:
            return device
    return None


def ensure_simulator_running(simulator: Dict) -> bool:
    """Ensure simulator is running before launching app"""

    if simulator.get("state") == "Booted":
        return True

    console.print(f"[cyan]Starting simulator: {simulator['name']}...[/cyan]")

    try:
        result = subprocess.run(
            ["xcrun", "simctl", "boot", simulator["id"]], capture_output=True, text=True, timeout=30
        )

        if result.returncode == 0:
            # Try to open Simulator.app
            subprocess.run(["open", "-a", "Simulator"], capture_output=True)
            show_success("Simulator started successfully")
            return True
        else:
            show_error(f"Failed to start simulator: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        show_error("Simulator startup timed out")
        return False
    except Exception as e:
        show_error(f"Error starting simulator: {str(e)}")
        return False


def run_flutter_app(
    project: FlutterProject, flavor: Optional[str], device: str, release: bool
) -> None:
    """Run Flutter app with specified parameters"""

    cmd = ["flutter", "run"]

    # Add device
    cmd.extend(["-d", device])

    # Add flavor if specified
    if flavor:
        cmd.extend(["--flavor", flavor])

    # Add build mode
    if release:
        cmd.append("--release")
    else:
        cmd.append("--debug")

    # Display run information
    console.print(f"[cyan]Running on device: {device}[/cyan]")
    if flavor:
        console.print(f"[cyan]Using flavor: {flavor}[/cyan]")
    console.print(f"[cyan]Build mode: {'release' if release else 'debug'}[/cyan]")

    console.print("\n[yellow]Flutter controls:[/yellow]")
    console.print("  • Press 'r' to hot reload")
    console.print("  • Press 'R' to hot restart")
    console.print("  • Press 'q' to quit")
    console.print("  • Press 'h' for help")
    console.print()

    try:
        # Run Flutter
        subprocess.run(cmd, cwd=project.path)
    except KeyboardInterrupt:
        console.print("\n[dim]App stopped[/dim]")


def show_available_devices(devices: List[Dict]) -> None:
    """Show list of available devices"""
    console.print("\n[cyan]Available devices:[/cyan]")

    # Group and display
    physical = [d for d in devices if not d.get("is_simulator", False)]
    simulators = [d for d in devices if d.get("is_simulator", False)]

    if physical:
        console.print("  [green]📱 Physical Devices:[/green]")
        for device in physical:
            console.print(f"    • {device['name']} ({device['id']})")

    if simulators:
        console.print("  [blue]🖥️ Simulators:[/blue]")
        for device in simulators[:5]:  # Show first 5
            status = "🟢" if device.get("state") == "Booted" else "⚫"
            console.print(f"    {status} {device['name']} ({device['id'][:8]}...)")


def show_setup_instructions() -> None:
    """Show iOS setup instructions"""

    instructions = """[yellow]No iOS devices available.[/yellow]

To set up iOS development:

1. [green]For Simulators:[/green]
   • Open Xcode
   • Go to Window → Devices and Simulators
   • Click '+' to add simulator
   • Or run: [cyan]xcrun simctl create "iPhone 15" "iPhone 15"[/cyan]

2. [green]For Physical Devices:[/green]
   • Connect iPhone/iPad via USB
   • Trust computer on device
   • Enable Developer Mode (iOS 16+)
   • Ensure device is registered in Apple Developer portal

3. [green]Check available devices:[/green]
   [cyan]flow ios devices[/cyan]

4. [green]Start a simulator:[/green]
   [cyan]flow ios devices --start "iPhone 15"[/cyan]"""

    from rich import box
    from rich.panel import Panel

    panel = Panel(
        instructions, title="💡 iOS Setup Instructions", border_style="blue", box=box.ROUNDED
    )
    console.print(panel)

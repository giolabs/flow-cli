"""
Banner and visual elements for Flow CLI
"""

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def show_banner() -> None:
    """Show the main Flow CLI banner"""

    # Create banner art
    banner_text = Text()
    banner_text.append(
        "╔═══════════════════════════════════════════════════════════════╗\n", style="bright_cyan"
    )
    banner_text.append("║", style="bright_cyan")
    banner_text.append(
        "                        Flow CLI                              ", style="bold bright_white"
    )
    banner_text.append("║\n", style="bright_cyan")
    banner_text.append("║", style="bright_cyan")
    banner_text.append(
        "            🚀 Flutter Development Made Easy 🚀               ", style="bright_blue"
    )
    banner_text.append("║\n", style="bright_cyan")
    banner_text.append(
        "╚═══════════════════════════════════════════════════════════════╝", style="bright_cyan"
    )

    console.print()
    console.print(Align.center(banner_text))
    console.print()


def show_section_header(title: str, icon: str = "📋") -> None:
    """Show a section header with consistent styling"""
    header_text = f"{icon} {title}"
    panel = Panel(header_text, style="cyan", box=box.SIMPLE, padding=(0, 1))
    console.print(panel)


def show_success(message: str) -> None:
    """Show a success message"""
    console.print(f"[green]✅ {message}[/green]")


def show_error(message: str) -> None:
    """Show an error message"""
    console.print(f"[red]❌ {message}[/red]")


def show_warning(message: str) -> None:
    """Show a warning message"""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def show_info(message: str) -> None:
    """Show an info message"""
    console.print(f"[blue]ℹ️  {message}[/blue]")

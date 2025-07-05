"""
Generate commands group - Asset generation tools
"""

import click
from flow_cli.commands.generate.icons import icons_command
from flow_cli.commands.generate.splash import splash_command
from flow_cli.commands.generate.branding import branding_command

@click.group(invoke_without_command=True)
@click.pass_context
def generate_group(ctx: click.Context) -> None:
    """
    🎨 Asset generation tools
    
    Generate app icons, splash screens, and branding assets for your
    Flutter project with support for multiple flavors and platforms.
    """
    if ctx.invoked_subcommand is None:
        show_generate_menu(ctx)

def show_generate_menu(ctx: click.Context) -> None:
    """Show interactive generate menu"""
    import inquirer
    from rich.console import Console
    from flow_cli.core.ui.banner import show_section_header
    
    console = Console()
    show_section_header("Asset Generation Tools", "🎨")
    
    choices = [
        "🎯 Icons - Generate app icons",
        "💧 Splash - Generate splash screens", 
        "🎨 Branding - Complete branding package",
        "🔙 Back to main menu"
    ]
    
    try:
        questions = [
            inquirer.List(
                'action',
                message="Select generation action:",
                choices=choices,
                carousel=True
            ),
        ]
        
        answers = inquirer.prompt(questions)
        if not answers:
            return
            
        action = answers['action']
        
        if action.startswith("🎯"):
            ctx.invoke(icons_command)
        elif action.startswith("💧"):
            ctx.invoke(splash_command)
        elif action.startswith("🎨"):
            ctx.invoke(branding_command)
        elif action.startswith("🔙"):
            return
            
    except KeyboardInterrupt:
        console.print("\n[dim]Returning to main menu...[/dim]")
        return

# Add subcommands
generate_group.add_command(icons_command, name='icons')
generate_group.add_command(splash_command, name='splash')
generate_group.add_command(branding_command, name='branding')
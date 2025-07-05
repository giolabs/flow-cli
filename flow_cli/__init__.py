"""
Flow CLI - A beautiful, interactive CLI tool for Flutter developers
"""

__version__ = "1.0.0"
__author__ = "Flow CLI Team"
__email__ = "team@flowcli.dev"
__description__ = "A beautiful, interactive CLI tool for Flutter developers"
__url__ = "https://github.com/flowstore/flow-cli"

# Export main components
from flow_cli.main import cli, main

__all__ = ["cli", "main", "__version__"]
"""
Analyze command - Analyze Flutter project for issues and metrics
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from flow_cli.core.flutter import FlutterProject
from flow_cli.core.ui.banner import show_error, show_section_header, show_success, show_warning

console = Console()


@click.command()
@click.option("--flavor", "-f", help="Analyze specific flavor")
@click.option(
    "--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format"
)
@click.option("--verbose", "-v", is_flag=True, help="Show detailed analysis")
def analyze_command(flavor: Optional[str], output: str, verbose: bool) -> None:
    """
    📊 Analyze Flutter project for issues and metrics

    Performs comprehensive analysis of your Flutter project including:
    - Code quality and lint issues
    - Dependencies analysis
    - Build artifacts analysis
    - Flavor configuration validation
    """

    # Find Flutter project
    project = FlutterProject.find_project()
    if not project:
        show_error("No Flutter project found in current directory")
        raise click.Abort()

    show_section_header(f"Analyzing Project: {project.name}", "📊")

    with Progress(
        SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
    ) as progress:

        # Collect analysis tasks
        analyses = [
            ("Analyzing Flutter code...", analyze_flutter_code),
            ("Checking dependencies...", analyze_dependencies),
            ("Analyzing build artifacts...", analyze_build_artifacts),
            ("Validating flavors...", analyze_flavors),
            ("Checking project structure...", analyze_project_structure),
        ]

        results = {}

        for description, analyze_func in analyses:
            task = progress.add_task(description, total=None)
            try:
                result = analyze_func(project, flavor, verbose)
                results[analyze_func.__name__] = result
            except Exception as e:
                results[analyze_func.__name__] = {"error": str(e)}
            finally:
                progress.remove_task(task)

    # Display results based on output format
    if output == "json":
        display_json_results(results)
    else:
        display_text_results(results, project, verbose)


def analyze_flutter_code(project: FlutterProject, flavor: Optional[str], verbose: bool) -> Dict:
    """Analyze Flutter code using flutter analyze"""
    try:
        result = subprocess.run(
            ["flutter", "analyze", "--no-congratulate"],
            cwd=project.path,
            capture_output=True,
            text=True,
            timeout=60,
        )

        issues = []
        if result.stdout:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "•" in line and ("error" in line or "warning" in line or "info" in line):
                    issues.append(line.strip())

        return {
            "success": result.returncode == 0,
            "issues_count": len(issues),
            "issues": issues if verbose else issues[:5],  # Limit to 5 unless verbose
            "no_issues": result.returncode == 0 and len(issues) == 0,
        }
    except subprocess.TimeoutExpired:
        return {"error": "Analysis timed out"}
    except Exception as e:
        return {"error": str(e)}


def analyze_dependencies(project: FlutterProject, flavor: Optional[str], verbose: bool) -> Dict:
    """Analyze project dependencies"""
    deps = project.get_dependencies()
    dev_deps = project.get_dev_dependencies()

    # Check for common Flutter packages
    flutter_packages = {
        "flutter_launcher_icons": "App icons generation",
        "flutter_native_splash": "Splash screen generation",
        "flutter_flavorizr": "Flavor configuration",
        "build_runner": "Code generation",
        "json_annotation": "JSON serialization",
        "provider": "State management",
        "bloc": "State management",
        "riverpod": "State management",
        "dio": "HTTP client",
        "shared_preferences": "Local storage",
        "sqflite": "SQLite database",
    }

    found_packages = []
    missing_recommended = []

    for package, description in flutter_packages.items():
        if project.has_dependency(package):
            found_packages.append((package, description))
        elif package in ["flutter_launcher_icons", "flutter_native_splash"]:
            missing_recommended.append((package, description))

    return {
        "total_dependencies": len(deps),
        "total_dev_dependencies": len(dev_deps),
        "found_packages": found_packages,
        "missing_recommended": missing_recommended,
        "has_flutter_dependency": "flutter" in deps,
    }


def analyze_build_artifacts(project: FlutterProject, flavor: Optional[str], verbose: bool) -> Dict:
    """Analyze build artifacts (APKs, AABs, etc.)"""
    outputs = project.get_build_outputs()

    artifacts = []
    total_size = 0

    for platform, files in outputs.items():
        for file_path in files:
            if file_path.exists():
                size = file_path.stat().st_size if file_path.is_file() else 0
                total_size += size

                artifacts.append(
                    {
                        "platform": platform,
                        "name": file_path.name,
                        "size_mb": round(size / (1024 * 1024), 2),
                        "path": str(file_path.relative_to(project.path)),
                    }
                )

    return {
        "total_artifacts": len(artifacts),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "artifacts": artifacts,
        "has_builds": len(artifacts) > 0,
    }


def analyze_flavors(project: FlutterProject, flavor: Optional[str], verbose: bool) -> Dict:
    """Analyze flavor configurations"""
    flavors = project.flavors
    flavor_details = []

    configs_dir = project.path / "assets" / "configs"

    for flavor_name in flavors:
        flavor_dir = configs_dir / flavor_name
        config_file = flavor_dir / "config.json"
        icon_file = flavor_dir / "icon.png"
        splash_file = flavor_dir / "splash.png"

        status = "complete"
        missing_files = []

        if not config_file.exists():
            missing_files.append("config.json")
            status = "incomplete"
        if not icon_file.exists():
            missing_files.append("icon.png")
            status = "incomplete"
        if not splash_file.exists():
            missing_files.append("splash.png")
            status = "incomplete"

        # Read config if available
        config_data = {}
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)
            except Exception:
                status = "error"

        flavor_details.append(
            {
                "name": flavor_name,
                "status": status,
                "missing_files": missing_files,
                "config": config_data,
                "app_name": config_data.get("appName", ""),
                "package_name": config_data.get("packageName", ""),
            }
        )

    return {
        "total_flavors": len(flavors),
        "flavors": flavor_details,
        "complete_flavors": sum(1 for f in flavor_details if f["status"] == "complete"),
    }


def analyze_project_structure(
    project: FlutterProject, flavor: Optional[str], verbose: bool
) -> Dict:
    """Analyze project structure and organization"""
    lib_dir = project.path / "lib"
    test_dir = project.path / "test"

    # Count Dart files
    dart_files = list(lib_dir.rglob("*.dart")) if lib_dir.exists() else []
    test_files = list(test_dir.rglob("*.dart")) if test_dir.exists() else []

    # Check for common directories
    common_dirs = {
        "lib/models": "Data models",
        "lib/services": "Business logic",
        "lib/widgets": "Custom widgets",
        "lib/screens": "Screen/page widgets",
        "lib/utils": "Utility functions",
        "test/unit": "Unit tests",
        "test/widget": "Widget tests",
        "test/integration": "Integration tests",
    }

    existing_dirs = []
    missing_dirs = []

    for dir_path, description in common_dirs.items():
        full_path = project.path / dir_path
        if full_path.exists():
            existing_dirs.append((dir_path, description))
        else:
            missing_dirs.append((dir_path, description))

    return {
        "dart_files": len(dart_files),
        "test_files": len(test_files),
        "test_coverage": len(test_files) / max(len(dart_files), 1) * 100,
        "existing_dirs": existing_dirs,
        "missing_dirs": missing_dirs,
        "has_tests": len(test_files) > 0,
    }


def display_text_results(results: Dict, project: FlutterProject, verbose: bool) -> None:
    """Display analysis results in text format"""

    # Project Overview
    overview_table = Table(title="📋 Project Overview", box=box.ROUNDED)
    overview_table.add_column("Property", style="cyan")
    overview_table.add_column("Value", style="bright_white")

    overview_table.add_row("Project Name", project.name)
    overview_table.add_row("Flutter Version", project.flutter_version or "Unknown")
    overview_table.add_row("Project Version", project.version or "Unknown")
    overview_table.add_row("Flavors", str(len(project.flavors)))

    console.print(overview_table)

    # Code Analysis
    if "analyze_flutter_code" in results:
        code_result = results["analyze_flutter_code"]
        if "error" not in code_result:
            status = (
                "✅ Clean"
                if code_result["no_issues"]
                else f"⚠️ {code_result['issues_count']} issues"
            )

            code_table = Table(title="🔍 Code Analysis", box=box.ROUNDED)
            code_table.add_column("Metric", style="cyan")
            code_table.add_column("Value", style="bright_white")

            code_table.add_row("Status", status)
            code_table.add_row("Issues Found", str(code_result["issues_count"]))

            console.print(code_table)

            if code_result["issues"] and verbose:
                issues_text = "\n".join(code_result["issues"])
                issues_panel = Panel(
                    issues_text, title="⚠️ Issues", border_style="yellow", box=box.ROUNDED
                )
                console.print(issues_panel)

    # Dependencies Analysis
    if "analyze_dependencies" in results:
        deps_result = results["analyze_dependencies"]
        if "error" not in deps_result:
            deps_table = Table(title="📦 Dependencies", box=box.ROUNDED)
            deps_table.add_column("Metric", style="cyan")
            deps_table.add_column("Value", style="bright_white")

            deps_table.add_row("Dependencies", str(deps_result["total_dependencies"]))
            deps_table.add_row("Dev Dependencies", str(deps_result["total_dev_dependencies"]))
            deps_table.add_row("Flutter Packages", str(len(deps_result["found_packages"])))

            console.print(deps_table)

    # Build Artifacts
    if "analyze_build_artifacts" in results:
        build_result = results["analyze_build_artifacts"]
        if "error" not in build_result and build_result["has_builds"]:
            build_table = Table(title="🏗️ Build Artifacts", box=box.ROUNDED)
            build_table.add_column("Platform", style="cyan")
            build_table.add_column("File", style="bright_white")
            build_table.add_column("Size (MB)", style="yellow")

            for artifact in build_result["artifacts"]:
                platform_emoji = {
                    "android_apks": "🤖",
                    "android_bundles": "📱",
                    "ios_apps": "🍎",
                    "web_builds": "🌐",
                }.get(artifact["platform"], "📄")

                build_table.add_row(
                    f"{platform_emoji} {artifact['platform'].replace('_', ' ').title()}",
                    artifact["name"],
                    str(artifact["size_mb"]),
                )

            console.print(build_table)

    # Flavors Analysis
    if "analyze_flavors" in results:
        flavors_result = results["analyze_flavors"]
        if "error" not in flavors_result and flavors_result["total_flavors"] > 0:
            flavors_table = Table(title="🎨 Flavors Configuration", box=box.ROUNDED)
            flavors_table.add_column("Flavor", style="cyan")
            flavors_table.add_column("Status", style="bright_white")
            flavors_table.add_column("App Name", style="green")

            for flavor in flavors_result["flavors"]:
                status_emoji = {"complete": "✅", "incomplete": "⚠️", "error": "❌"}.get(
                    flavor["status"], "❓"
                )

                flavors_table.add_row(
                    flavor["name"],
                    f"{status_emoji} {flavor['status'].title()}",
                    flavor["app_name"] or "Not set",
                )

            console.print(flavors_table)

    # Project Structure
    if "analyze_project_structure" in results:
        struct_result = results["analyze_project_structure"]
        if "error" not in struct_result:
            struct_table = Table(title="📁 Project Structure", box=box.ROUNDED)
            struct_table.add_column("Metric", style="cyan")
            struct_table.add_column("Value", style="bright_white")

            struct_table.add_row("Dart Files", str(struct_result["dart_files"]))
            struct_table.add_row("Test Files", str(struct_result["test_files"]))
            struct_table.add_row("Test Coverage", f"{struct_result['test_coverage']:.1f}%")

            console.print(struct_table)

    # Summary
    display_analysis_summary(results)


def display_json_results(results: Dict) -> None:
    """Display analysis results in JSON format"""
    console.print(json.dumps(results, indent=2))


def display_analysis_summary(results: Dict) -> None:
    """Display analysis summary"""
    summary_points = []

    # Code quality
    if "analyze_flutter_code" in results:
        code_result = results["analyze_flutter_code"]
        if "error" not in code_result:
            if code_result["no_issues"]:
                summary_points.append("✅ No code issues found")
            else:
                summary_points.append(f"⚠️ {code_result['issues_count']} code issues found")

    # Flavors
    if "analyze_flavors" in results:
        flavors_result = results["analyze_flavors"]
        if "error" not in flavors_result:
            complete = flavors_result["complete_flavors"]
            total = flavors_result["total_flavors"]
            if complete == total and total > 0:
                summary_points.append("✅ All flavors properly configured")
            elif total > 0:
                summary_points.append(f"⚠️ {total - complete} flavors need configuration")

    # Tests
    if "analyze_project_structure" in results:
        struct_result = results["analyze_project_structure"]
        if "error" not in struct_result:
            if struct_result["has_tests"]:
                coverage = struct_result["test_coverage"]
                if coverage >= 80:
                    summary_points.append("✅ Good test coverage")
                elif coverage >= 50:
                    summary_points.append("⚠️ Moderate test coverage")
                else:
                    summary_points.append("❌ Low test coverage")
            else:
                summary_points.append("❌ No tests found")

    if summary_points:
        summary_text = "\n".join(summary_points)
        summary_panel = Panel(
            summary_text, title="📊 Analysis Summary", border_style="cyan", box=box.ROUNDED
        )
        console.print(summary_panel)

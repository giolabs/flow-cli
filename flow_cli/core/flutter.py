"""
Flutter project detection and management
"""

import subprocess
import yaml
from pathlib import Path
from typing import Optional, List, Dict, Any


class FlutterProject:
    """Represents a Flutter project with its configuration"""

    def __init__(self, path: Path):
        self.path = path
        self.pubspec_path = path / "pubspec.yaml"
        self._pubspec_data: Optional[Dict[str, Any]] = None

    @property
    def name(self) -> str:
        """Get project name from pubspec.yaml"""
        if self.pubspec_data:
            return self.pubspec_data.get("name", self.path.name)
        return self.path.name

    @property
    def version(self) -> Optional[str]:
        """Get project version from pubspec.yaml"""
        if self.pubspec_data:
            return self.pubspec_data.get("version")
        return None

    @property
    def pubspec_data(self) -> Optional[Dict[str, Any]]:
        """Get pubspec.yaml data"""
        if self._pubspec_data is None and self.pubspec_path.exists():
            try:
                with open(self.pubspec_path, "r", encoding="utf-8") as f:
                    self._pubspec_data = yaml.safe_load(f)
            except Exception:
                self._pubspec_data = {}
        return self._pubspec_data

    @property
    def flutter_version(self) -> Optional[str]:
        """Get Flutter version"""
        try:
            result = subprocess.run(
                ["flutter", "--version"], capture_output=True, text=True, cwd=self.path
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines:
                    # Extract version from first line like "Flutter 3.16.0 • channel stable"
                    parts = lines[0].split()
                    if len(parts) >= 2:
                        return parts[1]
            return None
        except Exception:
            return None

    @property
    def flavors(self) -> List[str]:
        """Get available flavors from project structure"""
        flavors = []

        # Check for flavor configurations in assets/configs
        configs_dir = self.path / "assets" / "configs"
        if configs_dir.exists():
            for flavor_dir in configs_dir.iterdir():
                if flavor_dir.is_dir() and (flavor_dir / "config.json").exists():
                    flavors.append(flavor_dir.name)

        # Check Android flavors
        android_flavors_dir = self.path / "android" / "app" / "src"
        if android_flavors_dir.exists():
            for flavor_dir in android_flavors_dir.iterdir():
                if flavor_dir.is_dir() and flavor_dir.name not in ["main", "debug", "release"]:
                    if flavor_dir.name not in flavors:
                        flavors.append(flavor_dir.name)

        return sorted(flavors)

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid Flutter project"""
        return (
            self.pubspec_path.exists()
            and self.pubspec_data is not None
            and "flutter" in self.pubspec_data
        )

    def get_dependencies(self) -> Dict[str, Any]:
        """Get project dependencies"""
        if self.pubspec_data:
            return self.pubspec_data.get("dependencies", {})
        return {}

    def get_dev_dependencies(self) -> Dict[str, Any]:
        """Get project dev dependencies"""
        if self.pubspec_data:
            return self.pubspec_data.get("dev_dependencies", {})
        return {}

    def has_dependency(self, package_name: str) -> bool:
        """Check if project has a specific dependency"""
        deps = self.get_dependencies()
        dev_deps = self.get_dev_dependencies()
        return package_name in deps or package_name in dev_deps

    @staticmethod
    def find_project(start_path: Optional[Path] = None) -> Optional["FlutterProject"]:
        """Find Flutter project by walking up the directory tree"""
        if start_path is None:
            start_path = Path.cwd()

        current_path = start_path.resolve()

        while current_path != current_path.parent:
            pubspec_file = current_path / "pubspec.yaml"
            if pubspec_file.exists():
                project = FlutterProject(current_path)
                if project.is_valid:
                    return project
            current_path = current_path.parent

        return None

    def get_build_outputs(self) -> Dict[str, List[Path]]:
        """Get build output files (APKs, IPAs, etc.)"""
        outputs = {"android_apks": [], "android_bundles": [], "ios_apps": [], "web_builds": []}

        # Android APKs
        apk_dir = self.path / "build" / "app" / "outputs" / "flutter-apk"
        if apk_dir.exists():
            outputs["android_apks"] = list(apk_dir.glob("*.apk"))

        # Android App Bundles
        bundle_dir = self.path / "build" / "app" / "outputs" / "bundle"
        if bundle_dir.exists():
            outputs["android_bundles"] = list(bundle_dir.glob("**/*.aab"))

        # iOS builds
        ios_build_dir = self.path / "build" / "ios"
        if ios_build_dir.exists():
            outputs["ios_apps"] = list(ios_build_dir.glob("**/*.app"))

        # Web builds
        web_build_dir = self.path / "build" / "web"
        if web_build_dir.exists() and web_build_dir.is_dir():
            outputs["web_builds"] = [web_build_dir]

        return outputs

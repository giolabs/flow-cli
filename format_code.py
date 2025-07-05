#!/usr/bin/env python3
"""
Script to format code with Black
Run this script after installing dependencies to format the codebase
"""

import subprocess
import sys
from pathlib import Path

def main():
    """Format code with Black"""
    try:
        # Run Black on the codebase
        result = subprocess.run([
            sys.executable, "-m", "black", 
            "flow_cli", "tests"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Code formatted successfully with Black")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Black formatting failed: {e}")
        print(f"Error output: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ Black is not installed. Install it with:")
        print("pip install black")
        sys.exit(1)

if __name__ == "__main__":
    main()
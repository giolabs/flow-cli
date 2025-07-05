#!/usr/bin/env python3
"""
Helper script to run pytest directly without default arguments
"""
import sys
import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["tests/test_doctor.py", "-v"])) 
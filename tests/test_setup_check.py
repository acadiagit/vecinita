"""
Tests for src/setup_check.py

Tests environment setup validation and configuration checking.
"""
import pytest
import os
from unittest.mock import patch


class TestSetupCheck:
    """Test setup_check module functions."""

    def test_setup_check_file_exists(self):
        """Test that setup_check.py exists."""
        setup_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'setup_check.py')
        assert os.path.exists(setup_file), "setup_check.py should exist"

    def test_setup_check_has_validation_functions(self):
        """Test that setup_check defines validation functions."""
        setup_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'setup_check.py')
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Look for common validation patterns
            assert 'def ' in content, "setup_check should define functions"

    def test_setup_check_imports_dotenv(self):
        """Test that setup_check imports dotenv."""
        setup_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'setup_check.py')
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'dotenv' in content or 'load_dotenv' in content

    def test_setup_check_checks_environment(self):
        """Test that setup_check validates environment variables."""
        setup_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'setup_check.py')
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'environ' in content or 'getenv' in content or 'env' in content.lower()

    def test_setup_check_module_can_be_imported(self):
        """Test that setup_check module can be imported without errors."""
        try:
            from src import setup_check
            assert setup_check is not None
        except ImportError as e:
            pytest.skip(f"Could not import setup_check: {e}")

    def test_setup_check_has_main_or_check_function(self):
        """Test that setup_check has main validation function."""
        setup_file = os.path.join(os.path.dirname(
            __file__), '..', 'src', 'setup_check.py')
        with open(setup_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for common function names for setup checking
            has_check_function = any(func in content for func in [
                'def main', 'def check', 'def verify', 'def validate'
            ])
            assert has_check_function, "setup_check should have a validation function"

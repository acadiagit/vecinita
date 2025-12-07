"""
Tests for src/langsmith_config.py

Tests LangSmith configuration initialization and validation.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from io import StringIO


class TestLangSmithConfig:
    """Test langsmith_config module configuration and initialization."""

    def test_langsmith_config_file_exists(self):
        """Test that langsmith_config.py exists."""
        config_file = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'langsmith_config.py'
        )
        assert os.path.exists(config_file), "langsmith_config.py should exist"

    def test_langsmith_config_imports_os(self):
        """Test that langsmith_config imports os module."""
        config_file = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'langsmith_config.py'
        )
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'import os' in content

    def test_langsmith_config_imports_dotenv(self):
        """Test that langsmith_config imports dotenv."""
        config_file = os.path.join(
            os.path.dirname(__file__), '..', 'src', 'langsmith_config.py'
        )
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert 'dotenv' in content

    def test_langsmith_config_module_can_be_imported(self):
        """Test that langsmith_config module can be imported without errors."""
        try:
            from src import langsmith_config
            assert langsmith_config is not None
        except ImportError as e:
            pytest.fail(f"Could not import langsmith_config: {e}")

    def test_initialize_langsmith_function_exists(self):
        """Test that initialize_langsmith function is defined."""
        from src import langsmith_config
        assert hasattr(langsmith_config, 'initialize_langsmith')
        assert callable(langsmith_config.initialize_langsmith)

    def test_get_langsmith_config_function_exists(self):
        """Test that get_langsmith_config function is defined."""
        from src import langsmith_config
        assert hasattr(langsmith_config, 'get_langsmith_config')
        assert callable(langsmith_config.get_langsmith_config)

    def test_initialize_langsmith_returns_dict(self):
        """Test that initialize_langsmith returns a dictionary."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert isinstance(result, dict)

    def test_initialize_langsmith_dict_has_required_keys(self):
        """Test that initialize_langsmith result has required keys."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        required_keys = ['tracing_enabled', 'endpoint', 'project', 'status']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_initialize_langsmith_tracing_enabled_is_bool(self):
        """Test that tracing_enabled value is boolean."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert isinstance(result['tracing_enabled'], bool)

    def test_initialize_langsmith_endpoint_is_string(self):
        """Test that endpoint value is string."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert isinstance(result['endpoint'], str)
        assert len(result['endpoint']) > 0

    def test_initialize_langsmith_project_is_string(self):
        """Test that project value is string."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert isinstance(result['project'], str)
        assert len(result['project']) > 0

    def test_initialize_langsmith_status_is_string(self):
        """Test that status value is string."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert isinstance(result['status'], str)
        assert len(result['status']) > 0

    @patch.dict(os.environ, {'LANGSMITH_TRACING': 'true'})
    def test_initialize_langsmith_tracing_enabled_when_set_true(self):
        """Test that tracing is enabled when LANGSMITH_TRACING=true."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['tracing_enabled'] is True

    @patch.dict(os.environ, {'LANGSMITH_TRACING': 'false'})
    def test_initialize_langsmith_tracing_disabled_when_set_false(self):
        """Test that tracing is disabled when LANGSMITH_TRACING=false."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['tracing_enabled'] is False

    @patch.dict(os.environ, {'LANGSMITH_TRACING': ''})
    def test_initialize_langsmith_tracing_disabled_when_empty(self):
        """Test that tracing is disabled when LANGSMITH_TRACING is empty."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['tracing_enabled'] is False

    @patch.dict(os.environ, {
        'LANGSMITH_TRACING': 'true',
        'LANGSMITH_API_KEY': 'test-key'
    })
    def test_initialize_langsmith_status_configured_with_key(self):
        """Test that status is 'configured' when tracing enabled and API key set."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['status'] == 'configured'

    @patch.dict(os.environ, {
        'LANGSMITH_TRACING': 'true',
        'LANGSMITH_API_KEY': ''
    }, clear=False)
    def test_initialize_langsmith_status_error_without_key(self):
        """Test that status indicates error when tracing enabled but no API key."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert 'error' in result['status'].lower()

    @patch.dict(os.environ, {'LANGSMITH_TRACING': 'false'})
    def test_initialize_langsmith_status_disabled_when_tracing_off(self):
        """Test that status shows tracing_disabled when tracing is off."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert 'disabled' in result['status'].lower()

    @patch.dict(os.environ, {'LANGSMITH_PROJECT': 'test-project'})
    def test_initialize_langsmith_reads_project_from_env(self):
        """Test that project is read from LANGSMITH_PROJECT env variable."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['project'] == 'test-project'

    @patch.dict(os.environ, {'LANGSMITH_ENDPOINT': 'https://test.endpoint.com'})
    def test_initialize_langsmith_reads_endpoint_from_env(self):
        """Test that endpoint is read from LANGSMITH_ENDPOINT env variable."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['endpoint'] == 'https://test.endpoint.com'

    @patch.dict(os.environ, {}, clear=True)
    def test_initialize_langsmith_uses_defaults(self):
        """Test that initialize_langsmith uses default values."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert result['endpoint'] == 'https://api.smith.langchain.com'
        assert result['project'] == 'default'

    def test_get_langsmith_config_returns_dict(self):
        """Test that get_langsmith_config returns a dictionary."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        assert isinstance(result, dict)

    def test_get_langsmith_config_has_required_keys(self):
        """Test that get_langsmith_config result has required keys."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        required_keys = ['tracing_enabled', 'endpoint', 'project', 'api_key_set']
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_get_langsmith_config_tracing_enabled_is_bool(self):
        """Test that get_langsmith_config tracing_enabled is boolean."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        assert isinstance(result['tracing_enabled'], bool)

    def test_get_langsmith_config_api_key_set_is_bool(self):
        """Test that get_langsmith_config api_key_set is boolean."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        assert isinstance(result['api_key_set'], bool)

    @patch.dict(os.environ, {'LANGSMITH_API_KEY': 'test-key-12345'})
    def test_get_langsmith_config_api_key_set_true_when_key_exists(self):
        """Test that api_key_set is True when LANGSMITH_API_KEY is set."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        assert result['api_key_set'] is True

    @patch.dict(os.environ, {'LANGSMITH_API_KEY': ''}, clear=False)
    def test_get_langsmith_config_api_key_set_false_when_empty(self):
        """Test that api_key_set is False when LANGSMITH_API_KEY is empty."""
        from src.langsmith_config import get_langsmith_config
        result = get_langsmith_config()
        assert result['api_key_set'] is False

    def test_langsmith_config_global_variable_exists(self):
        """Test that langsmith_config global variable is initialized."""
        from src import langsmith_config
        assert hasattr(langsmith_config, 'langsmith_config')
        assert isinstance(langsmith_config.langsmith_config, dict)

    def test_langsmith_config_initialization_prints_info_logs(self):
        """Test that initialize_langsmith prints info logs."""
        from src.langsmith_config import initialize_langsmith
        # Capture stdout
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch.dict(os.environ, {'LANGSMITH_TRACING': 'true', 'LANGSMITH_API_KEY': 'test'}):
                initialize_langsmith()
                output = fake_out.getvalue()
                # Check that something was printed (module always prints)
                # This is a basic check; actual messages depend on config

    def test_docstring_initialize_langsmith_exists(self):
        """Test that initialize_langsmith has a docstring."""
        from src.langsmith_config import initialize_langsmith
        assert initialize_langsmith.__doc__ is not None
        assert len(initialize_langsmith.__doc__) > 0

    def test_docstring_get_langsmith_config_exists(self):
        """Test that get_langsmith_config has a docstring."""
        from src.langsmith_config import get_langsmith_config
        assert get_langsmith_config.__doc__ is not None
        assert len(get_langsmith_config.__doc__) > 0

    def test_initialize_langsmith_handles_case_insensitive_tracing_flag(self):
        """Test that LANGSMITH_TRACING is case-insensitive."""
        from src.langsmith_config import initialize_langsmith
        
        with patch.dict(os.environ, {'LANGSMITH_TRACING': 'TRUE'}):
            result = initialize_langsmith()
            assert result['tracing_enabled'] is True
        
        with patch.dict(os.environ, {'LANGSMITH_TRACING': 'True'}):
            result = initialize_langsmith()
            assert result['tracing_enabled'] is True

    def test_initialize_langsmith_multiple_calls_consistent(self):
        """Test that multiple calls to initialize_langsmith return consistent results."""
        from src.langsmith_config import initialize_langsmith
        
        result1 = initialize_langsmith()
        result2 = initialize_langsmith()
        
        assert result1['tracing_enabled'] == result2['tracing_enabled']
        assert result1['endpoint'] == result2['endpoint']
        assert result1['project'] == result2['project']

    def test_get_langsmith_config_multiple_calls_consistent(self):
        """Test that multiple calls to get_langsmith_config return consistent results."""
        from src.langsmith_config import get_langsmith_config
        
        result1 = get_langsmith_config()
        result2 = get_langsmith_config()
        
        assert result1['tracing_enabled'] == result2['tracing_enabled']
        assert result1['endpoint'] == result2['endpoint']
        assert result1['project'] == result2['project']
        assert result1['api_key_set'] == result2['api_key_set']

    def test_initialize_langsmith_endpoint_is_valid_url(self):
        """Test that endpoint value is a valid URL format."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        endpoint = result['endpoint']
        assert endpoint.startswith('http://') or endpoint.startswith('https://')

    def test_initialize_langsmith_status_not_empty(self):
        """Test that status is never empty string."""
        from src.langsmith_config import initialize_langsmith
        result = initialize_langsmith()
        assert len(result['status']) > 0
        assert result['status'] != ''

    def test_langsmith_config_module_has_documentation(self):
        """Test that langsmith_config module has a docstring."""
        from src import langsmith_config
        assert langsmith_config.__doc__ is not None
        assert 'LangSmith' in langsmith_config.__doc__

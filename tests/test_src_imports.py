import pytest

# Example: Test that src/__main__.py runs without error


def test_main_runs():
    import src.__main__
    assert True  # If import succeeds, test passes

# Example: Test agent_config loads


@pytest.mark.parametrize("module_name", [
    "agent_config",
    "rag_agent",
    "setup_check",
    "supabase_retriever",
    "workflow_diagram"
])
def test_src_module_import(module_name):
    mod = __import__(f"src.{module_name}", fromlist=[None])
    assert mod is not None

# Test that src/main.py file exists and has expected attributes/functions


def test_src_main_file_exists():
    import os
    main_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'main.py')
    assert os.path.exists(main_path), "src/main.py should exist"

    with open(main_path, 'r') as f:
        content = f.read()
        assert 'FastAPI' in content, "main.py should reference FastAPI"
        assert 'app' in content, "main.py should define an app object"

"""
Tests for src/agent_config.py

Tests agent configuration constants and prompt templates.
"""
import pytest
from src import agent_config


class TestAgentConfig:
    """Test agent_config module configuration constants."""

    def test_agent_config_has_model_name(self):
        """Test that agent_config defines CHAT_MODEL_NAME."""
        assert hasattr(agent_config, 'CHAT_MODEL_NAME')
        assert isinstance(agent_config.CHAT_MODEL_NAME, str)
        assert len(agent_config.CHAT_MODEL_NAME) > 0

    def test_agent_config_temperature_is_valid(self):
        """Test that TEMPERATURE is in valid range."""
        assert hasattr(agent_config, 'TEMPERATURE')
        temp = agent_config.TEMPERATURE
        assert isinstance(temp, (int, float))
        assert 0 <= temp <= 2  # Allow up to 2 for various LLM APIs

    def test_agent_config_has_embedding_model(self):
        """Test that agent_config defines EMBEDDING_MODEL_NAME."""
        assert hasattr(agent_config, 'EMBEDDING_MODEL_NAME')
        assert isinstance(agent_config.EMBEDDING_MODEL_NAME, str)
        assert len(agent_config.EMBEDDING_MODEL_NAME) > 0

    def test_agent_config_similarity_threshold(self):
        """Test that SIMILARITY_THRESHOLD is configured."""
        assert hasattr(agent_config, 'SIMILARITY_THRESHOLD')
        threshold = agent_config.SIMILARITY_THRESHOLD
        assert isinstance(threshold, (int, float))
        assert 0 <= threshold <= 1, "Similarity threshold should be between 0 and 1"

    def test_agent_config_max_retrieved_docs(self):
        """Test that MAX_RETRIEVED_DOCS is configured."""
        assert hasattr(agent_config, 'MAX_RETRIEVED_DOCS')
        assert isinstance(agent_config.MAX_RETRIEVED_DOCS, int)
        assert agent_config.MAX_RETRIEVED_DOCS > 0

    def test_agent_config_has_prompts(self):
        """Test that agent_config defines prompt templates."""
        prompt_names = ['GRADE_PROMPT', 'REWRITE_PROMPT', 'GENERATE_PROMPT_EN']
        for prompt_name in prompt_names:
            assert hasattr(
                agent_config, prompt_name), f"{prompt_name} should be defined"
            prompt = getattr(agent_config, prompt_name)
            assert isinstance(prompt, str)
            assert len(prompt) > 0

    def test_grade_prompt_has_placeholders(self):
        """Test that GRADE_PROMPT has context and question placeholders."""
        assert '{context}' in agent_config.GRADE_PROMPT
        assert '{question}' in agent_config.GRADE_PROMPT

    def test_rewrite_prompt_has_question_placeholder(self):
        """Test that REWRITE_PROMPT has question placeholder."""
        assert '{question}' in agent_config.REWRITE_PROMPT

    def test_generate_prompt_has_required_placeholders(self):
        """Test that GENERATE_PROMPT_EN has context and question placeholders."""
        assert '{context}' in agent_config.GENERATE_PROMPT_EN
        assert '{question}' in agent_config.GENERATE_PROMPT_EN

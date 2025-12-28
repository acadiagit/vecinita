"""Static response tool for Vecinita agent.

This tool provides predefined answers to frequently asked questions (FAQs)
without needing to search the database or external sources.
"""

import logging
import string
from typing import Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Minimum query length for partial matching to avoid false positives
MIN_QUERY_LENGTH = 10

# FAQ Database - can be expanded or moved to Supabase table
FAQ_DATABASE = {
    "en": {
        "what is vecinita": "Vecinita is a community-based Q&A assistant designed to help people find information about local services, community programs, and resources. It uses RAG (Retrieval-Augmented Generation) technology to provide accurate answers based on trusted sources.",
        "how does this work": "Vecinita works by searching through a database of community documents and resources. When you ask a question, it finds the most relevant information and provides an answer with source citations.",
        "who created vecinita": "Vecinita is an open-source project created to support community information access. The project uses LangChain, LangGraph, and Supabase technologies.",
    },
    "es": {
        "qué es vecinita": "Vecinita es un asistente comunitario de preguntas y respuestas diseñado para ayudar a las personas a encontrar información sobre servicios locales, programas comunitarios y recursos. Utiliza tecnología RAG (Generación Aumentada por Recuperación) para proporcionar respuestas precisas basadas en fuentes confiables.",
        "cómo funciona esto": "Vecinita funciona buscando en una base de datos de documentos y recursos comunitarios. Cuando haces una pregunta, encuentra la información más relevante y proporciona una respuesta con citas de fuentes.",
        "quién creó vecinita": "Vecinita es un proyecto de código abierto creado para apoyar el acceso a la información comunitaria. El proyecto utiliza tecnologías LangChain, LangGraph y Supabase.",
    }
}


@tool
def static_response_tool(query: str, language: str = "en") -> Optional[str]:
    """Check if the query matches a frequently asked question (FAQ).

    Use this tool FIRST before searching the database or web. It provides
    instant answers to common questions about Vecinita itself or frequently
    asked topics.

    Args:
        query: The user's question (lowercase)
        language: The detected language code ('en' or 'es')

    Returns:
        A predefined answer if the query matches an FAQ, otherwise an empty string.

    Example:
        >>> answer = static_response_tool("what is vecinita", "en")
        >>> if answer:
        ...     print(f"FAQ Answer: {answer}")
    """
    try:
        logger.info(
            f"Static Response: Checking FAQ for query: '{query}' in language: {language}")

        # Normalize query: lowercase and strip + remove punctuation (incl. Spanish ¿¡)
        normalized_query = query.lower().strip()
        punctuation_table = str.maketrans('', '', string.punctuation + "¿¡")
        normalized_query_clean = normalized_query.translate(punctuation_table)

        # Get FAQs for the detected language, default to English
        faqs = FAQ_DATABASE.get(language, FAQ_DATABASE.get("en", {}))

        # Check for exact match first (highest priority)
        if normalized_query in faqs:
            logger.info(
                f"Static Response: Found exact FAQ match for: '{normalized_query}'")
            return faqs[normalized_query]
        # Also check exact match against cleaned query to handle punctuation
        for faq_key, faq_answer in faqs.items():
            if faq_key.translate(punctuation_table) == normalized_query_clean:
                logger.info(
                    f"Static Response: Found exact cleaned FAQ match for: '{normalized_query_clean}'")
                return faq_answer

        # Check for partial matches only if query is substantial (avoid false positives)
        # Minimum length threshold prevents matching short words like "what", "how", "the"
        if len(normalized_query_clean) >= MIN_QUERY_LENGTH:
            for faq_key, faq_answer in faqs.items():
                # Compare against cleaned versions to handle punctuation
                faq_key_clean = faq_key.translate(punctuation_table)
                # Match if FAQ key is contained in query or vice versa
                if faq_key_clean in normalized_query_clean or normalized_query_clean in faq_key_clean:
                    logger.info(
                        f"Static Response: Found partial FAQ match for key: '{faq_key}'")
                    return faq_answer

        logger.info("Static Response: No FAQ match found")
        # Important: tool outputs must be strings for the chat API.
        # Return empty string when no match to avoid invalid 'role:tool' content.
        return ""

    except Exception as e:
        logger.error(f"Static Response: Error checking FAQs: {e}")
        return ""


def add_faq(question: str, answer: str, language: str = "en") -> None:
    """Add a new FAQ entry to the database.

    Args:
        question: The FAQ question (will be normalized to lowercase)
        answer: The predefined answer
        language: The language code ('en' or 'es')
    """
    normalized_question = question.lower().strip()
    if language not in FAQ_DATABASE:
        FAQ_DATABASE[language] = {}
    FAQ_DATABASE[language][normalized_question] = answer
    logger.info(f"Added new FAQ: '{normalized_question}' in {language}")


def list_faqs(language: str = "en") -> dict:
    """List all FAQs for a given language.

    Args:
        language: The language code ('en' or 'es')

    Returns:
        Dictionary of FAQ questions and answers
    """
    return FAQ_DATABASE.get(language, {})

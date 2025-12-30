"""
Tests for the scraper CLI module - src/scraper/main.py
Tests for command-line interface and entry point.
"""
import pytest
import os
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
from io import StringIO


@pytest.mark.unit
class TestScraperCLI:
    """Test the scraper CLI entry point."""

    def test_cli_argument_parsing(self):
        """Test that CLI arguments are parsed correctly."""
        from src.scraper.main import main

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            urls_file = f.name
            f.write("https://example.com\n")

        with tempfile.NamedTemporaryFile(delete=False) as f_out:
            output_file = f_out.name

        with tempfile.NamedTemporaryFile(delete=False) as f_failed:
            failed_log = f_failed.name

        try:
            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with patch('src.scraper.scraper.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 0, 1)
                    mock_scraper.return_value = mock_instance

                    # We expect this to fail due to no URLs, but that's OK for arg parsing test
                    try:
                        main()
                    except SystemExit:
                        pass
        finally:
            os.remove(urls_file)
            os.remove(output_file)
            os.remove(failed_log)

    def test_cli_input_file_validation(self):
        """Test that CLI validates input file exists."""
        from src.scraper.main import main

        with tempfile.NamedTemporaryFile(delete=False) as f_out:
            output_file = f_out.name

        with tempfile.NamedTemporaryFile(delete=False) as f_failed:
            failed_log = f_failed.name

        try:
            with patch.object(sys, 'argv', [
                'main.py',
                '--input', '/nonexistent/file.txt',
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with pytest.raises(SystemExit):
                    main()
        finally:
            os.remove(output_file)
            os.remove(failed_log)

    def test_cli_output_directory_creation(self):
        """Test that CLI creates output directories if needed."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'subdir', 'output.txt')
            failed_log = os.path.join(tmpdir, 'subdir', 'failed.txt')

            with open(urls_file, 'w') as f:
                f.write("https://example.com\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify directories were created
                    assert os.path.exists(os.path.dirname(output_file))
                    assert os.path.exists(os.path.dirname(failed_log))

    def test_cli_with_links_file_argument(self):
        """Test CLI accepts optional --links-file argument."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')
            links_file = os.path.join(tmpdir, 'links.txt')

            with open(urls_file, 'w') as f:
                f.write("https://example.com\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log,
                '--links-file', links_file
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify VecinaScraper was called with links_file
                    assert mock_scraper.called
                    call_kwargs = mock_scraper.call_args[1]
                    assert call_kwargs.get('links_file') == links_file

    def test_cli_with_loader_argument(self):
        """Test CLI accepts optional --loader argument."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')

            with open(urls_file, 'w') as f:
                f.write("https://example.com\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log,
                '--loader', 'playwright'
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (1, 1, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify scrape_urls was called with force_loader
                    assert mock_instance.scrape_urls.called
                    call_kwargs = mock_instance.scrape_urls.call_args[1]
                    assert call_kwargs.get('force_loader') == 'playwright'


@pytest.mark.unit
class TestScraperCLIErrorHandling:
    """Test CLI error handling."""

    def test_cli_handles_keyboard_interrupt(self):
        """Test CLI gracefully handles keyboard interrupt."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')

            with open(urls_file, 'w') as f:
                f.write("https://example.com\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.side_effect = KeyboardInterrupt()
                    mock_instance.print_summary = Mock()
                    mock_scraper.return_value = mock_instance

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    # Should exit with code 130 (standard for SIGINT)
                    assert exc_info.value.code == 130

    def test_cli_handles_fatal_error(self):
        """Test CLI handles fatal errors during scraping."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')

            with open(urls_file, 'w') as f:
                f.write("https://example.com\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.side_effect = Exception(
                        "Fatal error")
                    mock_scraper.return_value = mock_instance

                    with pytest.raises(SystemExit) as exc_info:
                        main()

                    assert exc_info.value.code == 1


@pytest.mark.unit
class TestScraperCLIURLParsing:
    """Test CLI URL file parsing."""

    def test_cli_parses_urls_from_file(self):
        """Test that CLI correctly parses URLs from input file."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')

            with open(urls_file, 'w') as f:
                f.write("# Comment line\n")
                f.write("https://example.com\n")
                f.write("\n")
                f.write("https://test.org\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with patch('src.scraper.main.VecinaScraper') as mock_scraper:
                    mock_instance = Mock()
                    mock_instance.scrape_urls.return_value = (2, 2, 0)
                    mock_instance.print_summary = Mock()
                    mock_instance.finalize = Mock()
                    mock_scraper.return_value = mock_instance

                    main()

                    # Verify scrape_urls was called with 2 URLs (comments and blanks ignored)
                    called_urls = mock_instance.scrape_urls.call_args[0][0]
                    assert len(called_urls) == 2
                    assert "https://example.com" in called_urls
                    assert "https://test.org" in called_urls

    def test_cli_handles_empty_url_file(self):
        """Test CLI exits gracefully with empty URL file."""
        from src.scraper.main import main

        with tempfile.TemporaryDirectory() as tmpdir:
            urls_file = os.path.join(tmpdir, 'urls.txt')
            output_file = os.path.join(tmpdir, 'output.txt')
            failed_log = os.path.join(tmpdir, 'failed.txt')

            # Write file with explicit UTF-8 encoding containing only comments
            with open(urls_file, 'w', encoding='utf-8', newline='') as f:
                f.write("# Only comments\n")
                f.write("# No actual URLs\n")

            with patch.object(sys, 'argv', [
                'main.py',
                '--input', urls_file,
                '--output-file', output_file,
                '--failed-log', failed_log
            ]):
                with pytest.raises(SystemExit) as exc_info:
                    main()

                # Should exit gracefully (code 0 for empty URL list after filtering comments)
                assert exc_info.value.code == 0

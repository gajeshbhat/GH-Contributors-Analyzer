"""
Tests for CLI functionality.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from click.testing import CliRunner

from src.github_analyzer.cli import cli


class TestCLI:
    """Test cases for CLI commands."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()

    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "GitHub Contributors Analyzer" in result.output

    @patch('src.github_analyzer.cli.GitHubClient')
    @patch('src.github_analyzer.cli.DatabaseHandler')
    @patch('src.github_analyzer.cli.settings')
    def test_analyze_topics_command(self, mock_settings, mock_db_handler, mock_github_client, runner, sample_repositories, sample_contributors):
        """Test analyze-topics command."""
        # Setup mocks
        mock_settings.github_token = "test_token"
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_repositories_by_topic = AsyncMock(return_value=sample_repositories[:2])
        mock_client_instance.get_contributors = AsyncMock(return_value=sample_contributors)
        mock_client_instance.close = AsyncMock()
        mock_github_client.return_value = mock_client_instance
        
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.save_repository = AsyncMock()
        mock_db_instance.save_contributors = AsyncMock()
        mock_db_instance.update_topic_stats = AsyncMock()
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['analyze-topics', 'python', '--limit', '2', '--save'])
        
        assert result.exit_code == 0
        mock_client_instance.get_repositories_by_topic.assert_called()
        mock_client_instance.get_contributors.assert_called()

    @patch('src.github_analyzer.cli.DatabaseHandler')
    def test_list_repositories_command(self, mock_db_handler, runner):
        """Test list-repositories command."""
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.get_repositories_by_topic = AsyncMock(return_value=[
            {
                'name': 'test-repo',
                'owner': 'testuser',
                'stargazers_count': 100,
                'language': 'Python',
                'topics': ['python', 'testing']
            }
        ])
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['list-repositories', '--topic', 'python'])
        
        assert result.exit_code == 0
        mock_db_instance.get_repositories_by_topic.assert_called_with('python', 20)

    @patch('src.github_analyzer.cli.DatabaseHandler')
    def test_contributors_command(self, mock_db_handler, runner):
        """Test contributors command."""
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.get_top_contributors = AsyncMock(return_value=[
            {
                'login': 'testuser',
                'contributions': 100,
                'html_url': 'https://github.com/testuser'
            }
        ])
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['contributors', 'testuser/test-repo'])
        
        assert result.exit_code == 0
        mock_db_instance.get_top_contributors.assert_called_with('testuser', 'test-repo', 20)

    @patch('src.github_analyzer.cli.DatabaseHandler')
    def test_stats_command(self, mock_db_handler, runner):
        """Test stats command."""
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.get_database_stats = AsyncMock(return_value={
            'repositories': 100,
            'contributors': 500,
            'topics': 20,
            'top_languages': [
                {'_id': 'Python', 'count': 50},
                {'_id': 'JavaScript', 'count': 30}
            ]
        })
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['stats'])
        
        assert result.exit_code == 0
        mock_db_instance.get_database_stats.assert_called_once()

    @patch('src.github_analyzer.cli.GitHubClient')
    @patch('src.github_analyzer.cli.DatabaseHandler')
    @patch('src.github_analyzer.cli.settings')
    def test_trending_command(self, mock_settings, mock_db_handler, mock_github_client, runner, sample_repositories):
        """Test trending command."""
        # Setup mocks
        mock_settings.github_token = "test_token"
        
        mock_client_instance = MagicMock()
        mock_client_instance.get_trending_repositories = AsyncMock(return_value=sample_repositories[:3])
        mock_client_instance.close = AsyncMock()
        mock_github_client.return_value = mock_client_instance
        
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.save_repository = AsyncMock()
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['trending', '--language', 'python', '--limit', '3', '--save'])
        
        assert result.exit_code == 0
        mock_client_instance.get_trending_repositories.assert_called_with(
            language='python', 
            since='daily', 
            limit=3
        )

    def test_contributors_command_invalid_format(self, runner):
        """Test contributors command with invalid repository format."""
        result = runner.invoke(cli, ['contributors', 'invalid-format'])
        
        assert result.exit_code == 0
        assert "Repository format should be 'owner/repo'" in result.output

    @patch('src.github_analyzer.cli.DatabaseHandler')
    @patch('click.confirm')
    def test_clear_data_command(self, mock_confirm, mock_db_handler, runner):
        """Test clear-data command."""
        mock_confirm.return_value = True
        
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.clear_all_data = AsyncMock()
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['clear-data'])
        
        assert result.exit_code == 0
        mock_db_instance.clear_all_data.assert_called_once()

    @patch('src.github_analyzer.cli.DatabaseHandler')
    def test_clear_data_command_with_confirm_flag(self, mock_db_handler, runner):
        """Test clear-data command with --confirm flag."""
        mock_db_instance = MagicMock()
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.clear_all_data = AsyncMock()
        mock_db_handler.return_value = mock_db_instance

        result = runner.invoke(cli, ['clear-data', '--confirm'])
        
        assert result.exit_code == 0
        mock_db_instance.clear_all_data.assert_called_once()

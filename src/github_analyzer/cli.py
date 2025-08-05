"""
Modern CLI interface for GitHub Contributors Analyzer.
"""

import asyncio
from typing import Optional, List
import sys

import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text
from rich import box
import structlog

from .config import settings
from .github_client import GitHubClient
from .database import DatabaseHandler

# Setup rich console
console = Console()
logger = structlog.get_logger(__name__)


def setup_logging(level: str = "INFO"):
    """Setup structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


@click.group()
@click.option('--log-level', default='INFO', help='Set logging level')
@click.pass_context
def cli(ctx, log_level):
    """GitHub Contributors Analyzer - Modern tool for analyzing GitHub repositories."""
    ctx.ensure_object(dict)
    ctx.obj['log_level'] = log_level
    setup_logging(log_level)
    
    # Display welcome message
    console.print(Panel.fit(
        "[bold blue]GitHub Contributors Analyzer[/bold blue]\n"
        "[dim]Analyze repositories and contributors using GitHub's GraphQL API[/dim]",
        border_style="blue"
    ))


@cli.command()
@click.argument('topics', nargs=-1, required=True)
@click.option('--limit', '-l', default=50, help='Number of repositories per topic')
@click.option('--contributors', '-c', default=25, help='Number of contributors per repository')
@click.option('--save', '-s', is_flag=True, help='Save results to database')
@click.pass_context
def analyze_topics(ctx, topics: tuple, limit: int, contributors: int, save: bool):
    """Analyze repositories and contributors for given topics."""
    return asyncio.run(_analyze_topics_async(ctx, topics, limit, contributors, save))


async def _analyze_topics_async(ctx, topics: tuple, limit: int, contributors: int, save: bool):
    """Async implementation of analyze_topics command."""

    if not settings.github_token:
        console.print("[red]Error: GitHub token not found. Please set GITHUB_TOKEN in .env file[/red]")
        sys.exit(1)
    
    github_client = GitHubClient(settings.github_token)
    db_handler = None
    
    if save:
        db_handler = DatabaseHandler()
        try:
            await db_handler.connect()
        except Exception as e:
            console.print(f"[red]Database connection failed: {e}[/red]")
            console.print("[yellow]Continuing without database save...[/yellow]")
            save = False
    
    try:
        for topic in topics:
            console.print(f"\n[bold green]Analyzing topic: {topic}[/bold green]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                
                # Fetch repositories
                task1 = progress.add_task(f"Fetching repositories for '{topic}'...", total=None)
                repositories = await github_client.get_repositories_by_topic(topic, limit)
                progress.update(task1, completed=True)
                
                if not repositories:
                    console.print(f"[yellow]No repositories found for topic '{topic}'[/yellow]")
                    continue
                
                # Display repositories table
                repo_table = Table(title=f"Top Repositories for '{topic}'", box=box.ROUNDED)
                repo_table.add_column("Repository", style="cyan", no_wrap=True)
                repo_table.add_column("Stars", justify="right", style="yellow")
                repo_table.add_column("Language", style="green")
                repo_table.add_column("Description", style="dim")
                
                for repo in repositories[:10]:  # Show top 10 in table
                    repo_table.add_row(
                        f"{repo.owner}/{repo.name}",
                        f"{repo.stargazers_count:,}",
                        repo.language or "N/A",
                        (repo.description or "No description")[:50] + "..." if repo.description and len(repo.description) > 50 else repo.description or "No description"
                    )
                
                console.print(repo_table)
                
                # Analyze contributors for top repositories
                task2 = progress.add_task("Analyzing contributors...", total=len(repositories))
                
                all_contributors = {}
                for i, repo in enumerate(repositories):
                    repo_contributors = await github_client.get_contributors(
                        repo.owner, repo.name, contributors
                    )
                    
                    if save and db_handler:
                        await db_handler.save_repository(repo)
                        await db_handler.save_contributors(repo, repo_contributors)
                    
                    # Aggregate contributors
                    for contrib in repo_contributors:
                        if contrib.login in all_contributors:
                            all_contributors[contrib.login]['total_contributions'] += contrib.contributions
                            all_contributors[contrib.login]['repositories'].append(f"{repo.owner}/{repo.name}")
                        else:
                            all_contributors[contrib.login] = {
                                'login': contrib.login,
                                'total_contributions': contrib.contributions,
                                'repositories': [f"{repo.owner}/{repo.name}"],
                                'avatar_url': contrib.avatar_url,
                                'html_url': contrib.html_url
                            }
                    
                    progress.update(task2, advance=1)
                
                # Display top contributors
                sorted_contributors = sorted(
                    all_contributors.values(),
                    key=lambda x: x['total_contributions'],
                    reverse=True
                )
                
                contrib_table = Table(title=f"Top Contributors for '{topic}'", box=box.ROUNDED)
                contrib_table.add_column("Contributor", style="cyan")
                contrib_table.add_column("Total Contributions", justify="right", style="yellow")
                contrib_table.add_column("Repositories", justify="right", style="green")
                contrib_table.add_column("Profile", style="blue")
                
                for contrib in sorted_contributors[:15]:  # Show top 15
                    contrib_table.add_row(
                        contrib['login'],
                        f"{contrib['total_contributions']:,}",
                        str(len(contrib['repositories'])),
                        contrib['html_url']
                    )
                
                console.print(contrib_table)
                
                if save and db_handler:
                    await db_handler.update_topic_stats(topic)
    
    finally:
        await github_client.close()
        if db_handler:
            await db_handler.disconnect()


@cli.command()
@click.option('--topic', '-t', help='Filter by topic')
@click.option('--limit', '-l', default=20, help='Number of results to show')
@click.pass_context
def list_repositories(ctx, topic: Optional[str], limit: int):
    """List repositories from the database."""
    return asyncio.run(_list_repositories_async(ctx, topic, limit))


async def _list_repositories_async(ctx, topic: Optional[str], limit: int):
    """Async implementation of list_repositories command."""

    db_handler = DatabaseHandler()
    try:
        await db_handler.connect()
        
        if topic:
            repositories = await db_handler.get_repositories_by_topic(topic, limit)
            title = f"Repositories for topic '{topic}'"
        else:
            # Get all repositories sorted by stars
            repositories = await db_handler.repositories.find().sort("stargazers_count", -1).limit(limit).to_list(length=limit)
            title = "Top Repositories"
        
        if not repositories:
            console.print("[yellow]No repositories found[/yellow]")
            return
        
        table = Table(title=title, box=box.ROUNDED)
        table.add_column("Repository", style="cyan")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Language", style="green")
        table.add_column("Topics", style="magenta")
        
        for repo in repositories:
            topics_str = ", ".join(repo.get('topics', [])[:3])  # Show first 3 topics
            if len(repo.get('topics', [])) > 3:
                topics_str += "..."
            
            table.add_row(
                f"{repo['owner']}/{repo['name']}",
                f"{repo['stargazers_count']:,}",
                repo.get('language', 'N/A'),
                topics_str or "None"
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        await db_handler.disconnect()


@cli.command()
@click.argument('repository', required=True)
@click.option('--limit', '-l', default=20, help='Number of contributors to show')
@click.pass_context
def contributors(ctx, repository: str, limit: int):
    """Show contributors for a specific repository (format: owner/repo)."""
    return asyncio.run(_contributors_async(ctx, repository, limit))


async def _contributors_async(ctx, repository: str, limit: int):
    """Async implementation of contributors command."""

    try:
        owner, repo_name = repository.split('/', 1)
    except ValueError:
        console.print("[red]Error: Repository format should be 'owner/repo'[/red]")
        return
    
    db_handler = DatabaseHandler()
    try:
        await db_handler.connect()
        
        contributors_list = await db_handler.get_top_contributors(owner, repo_name, limit)
        
        if not contributors_list:
            console.print(f"[yellow]No contributors found for {repository}[/yellow]")
            return
        
        table = Table(title=f"Top Contributors for {repository}", box=box.ROUNDED)
        table.add_column("Contributor", style="cyan")
        table.add_column("Contributions", justify="right", style="yellow")
        table.add_column("Profile", style="blue")
        
        for contrib in contributors_list:
            table.add_row(
                contrib['login'],
                f"{contrib['contributions']:,}",
                contrib['html_url']
            )
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        await db_handler.disconnect()


@cli.command()
@click.pass_context
def stats(ctx):
    """Show database statistics."""
    return asyncio.run(_stats_async(ctx))


async def _stats_async(ctx):
    """Async implementation of stats command."""

    db_handler = DatabaseHandler()
    try:
        await db_handler.connect()

        stats_data = await db_handler.get_database_stats()

        if not stats_data:
            console.print("[yellow]No statistics available[/yellow]")
            return

        # Create stats panel
        stats_text = f"""
[bold]Database Statistics[/bold]

📊 [cyan]Repositories:[/cyan] {stats_data.get('repositories', 0):,}
👥 [cyan]Contributors:[/cyan] {stats_data.get('contributors', 0):,}
🏷️  [cyan]Topics:[/cyan] {stats_data.get('topics', 0):,}
        """

        console.print(Panel(stats_text.strip(), title="Statistics", border_style="green"))

        # Show top languages
        if stats_data.get('top_languages'):
            lang_table = Table(title="Top Programming Languages", box=box.ROUNDED)
            lang_table.add_column("Language", style="cyan")
            lang_table.add_column("Repositories", justify="right", style="yellow")

            for lang_data in stats_data['top_languages']:
                lang_table.add_row(
                    lang_data['_id'],
                    f"{lang_data['count']:,}"
                )

            console.print(lang_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        await db_handler.disconnect()


@cli.command()
@click.option('--language', '-l', help='Filter by programming language')
@click.option('--since', default='daily', type=click.Choice(['daily', 'weekly', 'monthly']), help='Time period for trending')
@click.option('--limit', default=20, help='Number of repositories to fetch')
@click.option('--save', '-s', is_flag=True, help='Save results to database')
@click.pass_context
def trending(ctx, language: Optional[str], since: str, limit: int, save: bool):
    """Fetch trending repositories from GitHub."""
    return asyncio.run(_trending_async(ctx, language, since, limit, save))


async def _trending_async(ctx, language: Optional[str], since: str, limit: int, save: bool):
    """Async implementation of trending command."""

    if not settings.github_token:
        console.print("[red]Error: GitHub token not found. Please set GITHUB_TOKEN in .env file[/red]")
        sys.exit(1)

    github_client = GitHubClient(settings.github_token)
    db_handler = None

    if save:
        db_handler = DatabaseHandler()
        try:
            await db_handler.connect()
        except Exception as e:
            console.print(f"[red]Database connection failed: {e}[/red]")
            console.print("[yellow]Continuing without database save...[/yellow]")
            save = False

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:

            task = progress.add_task("Fetching trending repositories...", total=None)
            repositories = await github_client.get_trending_repositories(
                language=language,
                since=since,
                limit=limit
            )
            progress.update(task, completed=True)

            if not repositories:
                console.print("[yellow]No trending repositories found[/yellow]")
                return

            # Display trending repositories table
            title = f"Trending Repositories"
            if language:
                title += f" ({language})"

            table = Table(title=title, box=box.ROUNDED)
            table.add_column("Repository", style="cyan", no_wrap=True)
            table.add_column("Stars", justify="right", style="yellow")
            table.add_column("Language", style="green")
            table.add_column("Description", style="dim")

            for repo in repositories:
                table.add_row(
                    f"{repo.owner}/{repo.name}",
                    f"{repo.stargazers_count:,}",
                    repo.language or "N/A",
                    (repo.description or "No description")[:60] + "..." if repo.description and len(repo.description) > 60 else repo.description or "No description"
                )

            console.print(table)

            # Save to database if requested
            if save and db_handler:
                task2 = progress.add_task("Saving to database...", total=len(repositories))
                for repo in repositories:
                    await db_handler.save_repository(repo)
                    progress.update(task2, advance=1)

                console.print(f"[green]Saved {len(repositories)} repositories to database[/green]")

    finally:
        await github_client.close()
        if db_handler:
            await db_handler.disconnect()


@cli.command()
@click.option('--confirm', is_flag=True, help='Confirm deletion without prompt')
@click.pass_context
def clear_data(ctx, confirm: bool):
    """Clear all data from the database (use with caution)."""
    return asyncio.run(_clear_data_async(ctx, confirm))


async def _clear_data_async(ctx, confirm: bool):
    """Async implementation of clear_data command."""

    if not confirm:
        if not click.confirm("This will delete ALL data from the database. Are you sure?"):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    db_handler = DatabaseHandler()
    try:
        await db_handler.connect()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Clearing database...", total=None)
            await db_handler.clear_all_data()
            progress.update(task, completed=True)

        console.print("[green]Database cleared successfully[/green]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        await db_handler.disconnect()


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == '__main__':
    main()

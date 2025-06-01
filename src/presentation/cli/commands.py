from __future__ import annotations
import click
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import Reactor Agent components
try:
    from src.infrastructure.agents.reactor.reactor_agent import react_to_issue
    from src.infrastructure.database.search_logs import search_logs
    from src.infrastructure.agents.reactor.tools import get_all_tools
except ImportError as e:
    click.secho(f"❌ Module import error: {str(e)}", fg='red', err=True)
    sys.exit(1)

# Constants
DEFAULT_DB_PATH = "./chroma_known_problems_db"
DEFAULT_LOGS_DB_PATH = "./chroma_logs_db"


@click.group()
def cli():
    """SIEM LLM Integration CLI - Security Incident Response System"""
    pass


def handle_reactor_response(result: Dict[str, Any], output: str, save: str, verbose: bool) -> None:
    """Format and output Reactor Agent response"""
    if output == 'json':
        click.echo(json.dumps(result, indent=2))
    else:
        click.secho(f"✅ Issue processed successfully!", fg='green')
        click.echo(f"⏱️  Processing time: {result.get('processing_time', 0):.2f} seconds")
        click.echo(f"📅 Timestamp: {result.get('timestamp', 'N/A')}")
        click.echo()

        click.secho("🤖 Reactor Agent Response:", bold=True)
        click.echo("-" * 40)
        click.echo(result.get('response', 'No response generated'))

        if verbose and result.get('context_used'):
            click.echo()
            click.secho("📚 Context from Knowledge Base:", bold=True)
            click.echo("-" * 40)
            context = result['context_used']
            click.echo(context[:500] + "..." if len(context) > 500 else context)

            if result.get('tools_available'):
                click.echo()
                click.secho("🛠️  Available Tools:", bold=True)
                click.echo("-" * 40)
                for tool in result['tools_available']:
                    click.echo(f"  • {tool}")

    if save:
        save_response_to_file(result, save, output)
        click.echo(f"💾 Response saved to: {save}")


@cli.command()
@click.argument('issue')
@click.option('--output', '-o', type=click.Choice(['json', 'text']), default='text',
              help='Output format (json or text)')
@click.option('--save', '-s', type=click.Path(), help='Save response to file')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output with context details')
def handle_security_issue(issue: str, output: str, save: str, verbose: bool) -> None:
    """Process security issue from Detector and generate response"""
    click.secho(f"🔍 Processing security issue: {issue}", bold=True)
    click.echo("=" * 60)

    try:
        start_time = time.time()
        result = react_to_issue(issue)
        result['processing_time'] = time.time() - start_time

        handle_reactor_response(result, output, save, verbose)
    except Exception as e:
        click.secho(f"❌ Error processing security issue: {str(e)}", fg='red', err=True)
        sys.exit(1)


@cli.command()
@click.option('--query', '-q', prompt='Search query', help='Search query for logs')
@click.option('--limit', '-l', default=5, help='Number of results to return')
@click.option('--process', '-p', is_flag=True, help='Process found issues with Reactor Agent')
def search_and_respond(query: str, limit: int, process: bool) -> None:
    """Search indexed logs and optionally process findings with Reactor Agent"""
    try:
        click.secho(f"🔍 Searching logs for: {query}", bold=True)
        search_results = search_logs(query, limit) or []

        if not search_results:
            click.secho("❌ No results found", fg='yellow')
            return

        click.echo(f"📊 Found {len(search_results)} results:")
        click.echo("=" * 50)

        for i, result in enumerate(search_results, 1):
            click.echo(f"{i}. {truncate_text(result)}")

            if process:
                click.echo("   🤖 Processing with Reactor Agent...")
                try:
                    response = react_to_issue(result)
                    click.echo(f"   ✅ Action: {truncate_text(response.get('response', ''))}")
                except Exception as e:
                    click.secho(f"   ❌ Processing failed: {e}", fg='red')
            click.echo()
    except Exception as e:
        click.secho(f"❌ Search failed: {str(e)}", fg='red', err=True)


@cli.command()
@click.option('--file', '-f', type=click.Path(exists=True), required=True,
              help='File containing security issues (one per line)')
@click.option('--batch-size', '-b', default=10, help='Process issues in batches')
@click.option('--delay', '-d', default=1.0, help='Delay between batch processing (seconds)')
def batch_process(file: str, batch_size: int, delay: float) -> None:
    """Process multiple security issues from file in batches"""
    try:
        with open(file, 'r') as f:
            issues = [line.strip() for line in f if line.strip()]

        if not issues:
            click.secho("❌ No issues found in file", fg='yellow')
            return

        click.echo(f"📋 Processing {len(issues)} issues in batches of {batch_size}")
        results = []

        for i in range(0, len(issues), batch_size):
            batch = issues[i:i + batch_size]
            click.echo(f"\n🔄 Processing batch {i // batch_size + 1}/{(len(issues) - 1) // batch_size + 1}")

            for issue in click.progressbar(batch):
                try:
                    result = react_to_issue(issue)
                    results.append({
                        'issue': issue,
                        'success': True,
                        'response': truncate_text(result.get('response', '')),
                        'processing_time': result.get('processing_time', 0)
                    })
                except Exception as e:
                    results.append({
                        'issue': issue,
                        'success': False,
                        'error': str(e),
                        'processing_time': 0
                    })

            if i + batch_size < len(issues):
                click.echo(f"⏳ Waiting {delay:.1f} seconds...")
                time.sleep(delay)

        # Generate processing summary
        successful = sum(1 for r in results if r['success'])
        avg_time = sum(r['processing_time'] for r in results if r['success']) / max(1, successful)

        click.echo("\n📊 Batch Processing Summary:")
        click.echo("=" * 40)
        click.echo(f"Total issues: {len(results)}")
        click.secho(f"Successful: {successful}", fg='green')
        click.secho(f"Failed: {len(results) - successful}", fg='red' if successful < len(results) else 'green')
        click.echo(f"Average processing time: {avg_time:.2f}s")

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"batch_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        click.echo(f"💾 Results saved to: {results_file}")
    except Exception as e:
        click.secho(f"❌ Batch processing failed: {str(e)}", fg='red', err=True)


@cli.command()
@click.option('--source', '-s', type=click.Choice(['detector', 'logs', 'file']),
              default='detector', help='Source of security issues')
@click.option('--input-file', '-i', type=click.Path(exists=True),
              help='Input file when source is file')
@click.option('--output-dir', '-o', type=click.Path(), default='./reports',
              help='Output directory for reports')
@click.option('--format', '-f', type=click.Choice(['json', 'html', 'text']),
              default='json', help='Report format')
def generate_report(source: str, input_file: str, output_dir: str, format: str) -> None:
    """Generate security response report"""
    try:
        issues = fetch_issues(source, input_file)

        if not issues:
            click.secho("❌ No issues found to process", fg='yellow')
            return

        os.makedirs(output_dir, exist_ok=True)
        report_data = generate_report_data(source, issues)
        report_file = create_report_file(report_data, output_dir, format)

        click.secho(f"✅ Report generated: {report_file}", fg='green')
    except Exception as e:
        click.secho(f"❌ Report generation failed: {str(e)}", fg='red', err=True)


@cli.command()
def status() -> None:
    """Check system status and configuration"""
    try:
        click.secho("🔍 SIEM LLM Integration System Status", bold=True)
        click.echo("=" * 50)

        # Database checks
        check_database_status("Known problems database", DEFAULT_DB_PATH)
        check_database_status("Logs database", DEFAULT_LOGS_DB_PATH)

        # Agent status
        try:
            react_to_issue("Test connection")
            click.secho("✅ Reactor Agent: Operational", fg='green')
        except Exception as e:
            click.secho(f"❌ Reactor Agent: Failed ({e})", fg='red')

        # Tools listing
        click.echo("\n🛠️  Available Tools:")
        for tool in get_all_tools():
            click.echo(f"  • {tool.name}: {truncate_text(tool.description, 60)}")
    except Exception as e:
        click.secho(f"❌ Status check failed: {str(e)}", fg='red', err=True)


# Helper functions
def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if needed"""
    return text[:max_length] + "..." if len(text) > max_length else text


def save_response_to_file(result: Dict[str, Any], filepath: str, format_type: str) -> None:
    """Save response to file in specified format"""
    with open(filepath, 'w') as f:
        if format_type == 'json':
            json.dump(result, f, indent=2)
        else:
            f.write(f"Security Issue: {result.get('issue', 'N/A')}\n")
            f.write(f"Timestamp: {result.get('timestamp', 'N/A')}\n")
            f.write(f"Processing Time: {result.get('processing_time', 0):.2f}s\n")
            f.write(f"Success: {result.get('success', False)}\n\n")
            f.write("Response:\n")
            f.write(result.get('response', 'No response generated'))


def fetch_issues(source: str, input_file: str) -> List[str]:
    """Fetch issues based on source type"""
    if source == 'file' and input_file:
        with open(input_file, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    elif source == 'logs':
        return search_logs("error OR warning", 10) or []
    else:
        return [
            "DOS attack detected from IP 192.168.1.100",
            "Malware infection on host server1",
            "Unauthorized access attempt detected"
        ]


def generate_report_data(source: str, issues: List[str]) -> Dict[str, Any]:
    """Generate report data structure"""
    report_data = {
        'timestamp': datetime.now().isoformat(),
        'source': source,
        'total_issues': len(issues),
        'results': []
    }

    for issue in click.progressbar(issues):
        try:
            result = react_to_issue(issue)
            report_data['results'].append({
                'issue': issue,
                'success': result.get('success', False),
                'response': result.get('response', ''),
                'processing_time': result.get('processing_time', 0)
            })
        except Exception as e:
            report_data['results'].append({
                'issue': issue,
                'error': str(e),
                'success': False
            })
    return report_data


def create_report_file(report_data: Dict[str, Any], output_dir: str, format: str) -> str:
    """Create report file in specified format"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"security_report_{timestamp}.{format}"
    filepath = os.path.join(output_dir, filename)

    if format == 'json':
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2)
    elif format == 'html':
        with open(filepath, 'w') as f:
            f.write(generate_html_report(report_data))
    else:  # text format
        with open(filepath, 'w') as f:
            f.write(generate_text_report(report_data))
    return filepath


def check_database_status(name: str, path: str) -> None:
    """Check and report database status"""
    if os.path.exists(path):
        click.secho(f"✅ {name}: Connected", fg='green')
    else:
        click.secho(f"❌ {name}: Not found at {path}", fg='red')


def generate_html_report(report_data):
    """Generate HTML report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Security Response Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #f0f0f0; padding: 20px; }}
            .issue {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
            .success {{ border-left: 5px solid #4CAF50; }}
            .error {{ border-left: 5px solid #f44336; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Security Response Report</h1>
            <p>Generated: {report_data['timestamp']}</p>
            <p>Source: {report_data['source']}</p>
            <p>Total Issues: {report_data['total_issues']}</p>
        </div>
    """

    for result in report_data['results']:
        css_class = "success" if result.get('success', False) else "error"
        html += f"""
        <div class="issue {css_class}">
            <h3>Issue: {result.get('issue', 'Unknown')}</h3>
            <p><strong>Response:</strong> {result.get('response', result.get('error', 'No response'))}</p>
            <p><strong>Processing Time:</strong> {result.get('processing_time', 0):.2f}s</p>
        </div>
        """

    html += "</body></html>"
    return html


def generate_text_report(report_data):
    """Generate text report"""
    text = f"""SECURITY RESPONSE REPORT
{'=' * 50}
Generated: {report_data['timestamp']}
Source: {report_data['source']}
Total Issues: {report_data['total_issues']}

RESULTS:
{'-' * 50}
"""

    for i, result in enumerate(report_data['results'], 1):
        text += f"""
{i}. Issue: {result.get('issue', 'Unknown')}
   Status: {'SUCCESS' if result.get('success', False) else 'ERROR'}
   Response: {result.get('response', result.get('error', 'No response'))}
   Processing Time: {result.get('processing_time', 0):.2f}s
"""

    return text


if __name__ == '__main__':
    cli()
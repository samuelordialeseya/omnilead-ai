"""
OmniLead-AI CLI
================
Rich terminal interface powered by Typer.

Usage:
    python -m omnilead.cli.main_cli process --input sample_leads.csv
    python -m omnilead.cli.main_cli process --input leads.json --output enriched.csv
    python -m omnilead.cli.main_cli status
"""
from __future__ import annotations

import asyncio
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, MofNCompleteColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn, TimeElapsedColumn
from rich.table import Table
from rich.text import Text

from omnilead.config import settings
from omnilead.core.pipeline import run_pipeline
from omnilead.models.schemas import EnrichedLead, LeadStatus, RawLead

# Ensure Windows terminal standard streams handle UTF-8 cleanly
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

app = typer.Typer(
    name="omnilead",
    help="OmniLead-AI: B2B Lead Scraping, Verification & Gemini AI Enrichment Pipeline",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console(safe_box=True)


def _configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s | %(name)s | %(message)s")


def _load_csv(path: Path) -> list[RawLead]:
    leads = []
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            leads.append(RawLead(
                company_name=row.get("company_name", row.get("Company", "")).strip(),
                website=row.get("website", row.get("Website", "")).strip(),
                prospect_name=row.get("prospect_name", row.get("Name", "")).strip(),
                prospect_email=row.get("prospect_email", row.get("Email", "")).strip(),
                prospect_role=row.get("prospect_role", row.get("Role", "")).strip(),
                niche=row.get("niche", row.get("Niche", "")).strip(),
            ))
    return leads


def _load_json(path: Path) -> list[RawLead]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [RawLead(**item) for item in (data if isinstance(data, list) else data.get("leads", []))]


def _build_results_table(leads: list[EnrichedLead]) -> Table:
    table = Table(box=box.ROUNDED, show_lines=True, expand=True)
    table.add_column("Company", style="bold cyan", min_width=18)
    table.add_column("Contact Email", min_width=22)
    table.add_column("Email Risk", min_width=10)
    table.add_column("ICP Score", justify="center", min_width=10)
    table.add_column("Hot Lead", justify="center", min_width=9)
    table.add_column("Status", min_width=11)
    table.add_column("Icebreaker", min_width=35)

    for lead in sorted(leads, key=lambda l: l.icp_score, reverse=True):
        score_color = "bright_green" if lead.icp_score >= 80 else ("yellow" if lead.icp_score >= 50 else "red")
        status_color = {
            LeadStatus.DISPATCHED: "bright_green",
            LeadStatus.ENRICHED: "green",
            LeadStatus.VERIFIED: "yellow",
            LeadStatus.FAILED: "red",
        }.get(lead.status, "white")

        table.add_row(
            lead.company_name,
            lead.prospect_email or "[dim]—[/dim]",
            lead.email_risk.value,
            Text(str(lead.icp_score), style=score_color),
            "HOT" if lead.is_hot_lead else "—",
            Text(lead.status.value, style=status_color),
            (lead.icebreaker[:70] + "…") if len(lead.icebreaker) > 70 else lead.icebreaker,
        )

    return table


@app.command()
def process(
    input_file: Path = typer.Option(..., "--input", "-i", help="CSV or JSON file of raw leads."),
    output_file: Optional[Path] = typer.Option(None, "--output", "-o", help="Output CSV path. Defaults to output/enriched_<timestamp>.csv"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable debug logging."),
):
    """
    [bold]Process[/bold] a CSV/JSON file of raw leads through the full OmniLead-AI pipeline.

    Runs web crawling → email verification → Gemini AI enrichment → dispatch.
    """
    _configure_logging(verbose)

    if not input_file.exists():
        console.print(f"[red]Error:[/red] Input file not found: {input_file}")
        raise typer.Exit(1)

    # Load input
    suffix = input_file.suffix.lower()
    if suffix == ".csv":
        raw_leads = _load_csv(input_file)
    elif suffix == ".json":
        raw_leads = _load_json(input_file)
    else:
        console.print(f"[red]Error:[/red] Unsupported file format '{suffix}'. Use .csv or .json")
        raise typer.Exit(1)

    if not raw_leads:
        console.print("[yellow]Warning:[/yellow] Input file is empty. Nothing to process.")
        raise typer.Exit(0)

    # Resolve output path
    if output_file is None:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = Path(settings.output_dir) / f"enriched_{ts}.csv"

    # Print banner
    mode_badge = "[bold green]MOCK MODE[/bold green]" if settings.mock_mode else "[bold blue]LIVE MODE[/bold blue]"
    console.print(Panel.fit(
        f"[bold white]OmniLead-AI[/bold white]  •  B2B Lead Enrichment Pipeline\n"
        f"Mode: {mode_badge}  |  Leads: [bold]{len(raw_leads)}[/bold]  |  Concurrency: {settings.concurrency_limit}  |  RPS: {settings.rate_limit_rps}",
        border_style="bright_blue",
    ))

    processed_leads: list[EnrichedLead] = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    )
    task_id = progress.add_task("Processing leads…", total=len(raw_leads))

    async def on_progress(lead: EnrichedLead, idx: int, total: int) -> None:
        processed_leads.append(lead)
        label = f"[cyan]{lead.company_name[:25]}[/cyan] — ICP [bold]{lead.icp_score}[/bold]"
        progress.update(task_id, advance=1, description=f"[{idx}/{total}] {label}")

    with progress:
        asyncio.run(run_pipeline(raw_leads, output_path=str(output_file), progress_callback=on_progress))

    # Summary table
    console.print("\n")
    console.print(Panel(
        _build_results_table(processed_leads),
        title="[bold white]Enrichment Results[/bold white]",
        border_style="bright_blue",
    ))

    hot_count = sum(1 for l in processed_leads if l.is_hot_lead)
    enriched_count = sum(1 for l in processed_leads if l.status in (LeadStatus.ENRICHED, LeadStatus.DISPATCHED))

    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green][+][/green] Enriched:  [green]{enriched_count}[/green] / {len(processed_leads)}")
    console.print(f"  [bright_green][*][/bright_green] Hot Leads: [bright_green]{hot_count}[/bright_green]")
    console.print(f"  [cyan][>][/cyan] Output:    [cyan]{output_file.resolve()}[/cyan]\n")


@app.command()
def status():
    """Show current OmniLead-AI configuration and system status."""
    table = Table(box=box.SIMPLE_HEAD, show_header=True)
    table.add_column("Setting", style="bold cyan")
    table.add_column("Value")

    table.add_row("Mock Mode", "[green]ENABLED[/green]" if settings.mock_mode else "[red]DISABLED[/red]")
    table.add_row("Gemini API Key", "[green]✓ Configured[/green]" if settings.gemini_api_key else "[yellow]Not set[/yellow]")
    table.add_row("Gemini Model", settings.gemini_model)
    table.add_row("Concurrency Limit", str(settings.concurrency_limit))
    table.add_row("Rate Limit (RPS)", str(settings.rate_limit_rps))
    table.add_row("CRM Webhook", "[green]✓ Configured[/green]" if settings.crm_webhook_url else "[dim]Not set[/dim]")
    table.add_row("Slack Webhook", "[green]✓ Configured[/green]" if settings.slack_webhook_url else "[dim]Not set[/dim]")
    table.add_row("Discord Webhook", "[green]✓ Configured[/green]" if settings.discord_webhook_url else "[dim]Not set[/dim]")
    table.add_row("Output Directory", settings.output_dir)

    console.print(Panel(table, title="[bold white]OmniLead-AI Configuration[/bold white]", border_style="bright_blue"))


if __name__ == "__main__":
    app()

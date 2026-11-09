"""
CSV Exporter
============
Writes enriched leads to a UTF-8 CSV file with all metadata columns.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path

from omnilead.models.schemas import EnrichedLead

logger = logging.getLogger(__name__)

_CSV_FIELDNAMES = [
    "company_name", "website", "prospect_name", "prospect_email", "prospect_role",
    "niche", "meta_title", "detected_stack", "social_linkedin", "social_twitter",
    "email_valid", "email_risk", "email_deliverability_score",
    "icp_score", "is_hot_lead", "icebreaker", "value_proposition",
    "suggested_cta", "company_summary", "pain_points", "status",
]


def export_to_csv(leads: list[EnrichedLead], output_path: str | Path) -> Path:
    """
    Write enriched leads to a CSV file.

    Args:
        leads: List of fully processed EnrichedLead objects.
        output_path: Destination file path (created if not exists).

    Returns:
        Resolved Path to the written CSV file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [lead.to_csv_row() for lead in leads]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"Exported {len(rows)} leads → {path}")
    return path

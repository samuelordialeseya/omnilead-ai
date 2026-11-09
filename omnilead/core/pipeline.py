"""
Pipeline Orchestrator
======================
Coordinates all pipeline stages for a list of raw leads:
  1. Rate-limited async web crawling
  2. Email deliverability verification
  3. Gemini AI enrichment
  4. CRM/Slack/Discord dispatch
  5. CSV export

Provides a simple `run_pipeline()` coroutine as the primary entry point.
"""
from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from omnilead.ai.enricher import enrich_lead
from omnilead.config import settings
from omnilead.core.crawler import crawl_website
from omnilead.core.csv_exporter import export_to_csv
from omnilead.core.rate_limiter import get_rate_limiter
from omnilead.core.verifier import verify_email
from omnilead.dispatchers.webhook_dispatcher import dispatch_lead
from omnilead.models.schemas import EnrichedLead, LeadStatus, RawLead

logger = logging.getLogger(__name__)


async def process_single_lead(raw: RawLead) -> EnrichedLead:
    """Process one lead through the full pipeline (crawl → verify → enrich → dispatch)."""
    lead = EnrichedLead(
        company_name=raw.company_name,
        website=raw.website,
        prospect_name=raw.prospect_name,
        prospect_email=raw.prospect_email,
        prospect_role=raw.prospect_role,
        niche=raw.niche,
        status=LeadStatus.PENDING,
    )

    limiter = get_rate_limiter()

    # ── Stage 1: Web Crawl ───────────────────────────────────────────────────
    try:
        async with limiter.acquire():
            scraped = await crawl_website(raw.website)
        lead.meta_title = scraped.meta_title
        lead.meta_description = scraped.meta_description
        lead.page_summary = scraped.page_summary
        lead.detected_stack = scraped.detected_stack
        lead.social_linkedin = scraped.social_links.get("linkedin", "")
        lead.social_twitter = scraped.social_links.get("twitter", "")
        lead.status = LeadStatus.SCRAPED
    except Exception as exc:
        lead.status = LeadStatus.FAILED
        lead.error_message = f"Crawl failed: {exc}"
        logger.warning(f"Crawl failed for {raw.website}: {exc}")
        return lead

    # ── Stage 2: Email Verification ──────────────────────────────────────────
    try:
        if raw.prospect_email:
            async with limiter.acquire():
                email_result = await verify_email(raw.prospect_email)
            lead.email_valid = email_result.risk.value in ("SAFE", "CATCH_ALL")
            lead.email_risk = email_result.risk
            lead.email_deliverability_score = email_result.deliverability_score
        lead.status = LeadStatus.VERIFIED
    except Exception as exc:
        logger.warning(f"Email verification failed for {raw.prospect_email}: {exc}")

    # ── Stage 3: AI Enrichment ───────────────────────────────────────────────
    try:
        async with limiter.acquire():
            enrichment = await enrich_lead(raw.company_name, scraped, raw.niche)
        lead.company_summary = enrichment.company_summary
        lead.pain_points = enrichment.inferred_pain_points
        lead.icebreaker = enrichment.personalized_icebreaker
        lead.value_proposition = enrichment.value_proposition
        lead.icp_score = enrichment.icp_score
        lead.suggested_cta = enrichment.suggested_cta
        lead.status = LeadStatus.ENRICHED
    except Exception as exc:
        lead.status = LeadStatus.FAILED
        lead.error_message = f"AI enrichment failed: {exc}"
        logger.warning(f"AI enrichment failed for {raw.company_name}: {exc}")
        return lead

    # ── Stage 4: Dispatch ────────────────────────────────────────────────────
    try:
        async with limiter.acquire():
            lead.dispatch_success = await dispatch_lead(lead)
        if lead.dispatch_success:
            lead.status = LeadStatus.DISPATCHED
    except Exception as exc:
        logger.warning(f"Dispatch failed for {raw.company_name}: {exc}")

    return lead


async def run_pipeline(
    raw_leads: list[RawLead],
    output_path: str | None = None,
    progress_callback=None,
) -> list[EnrichedLead]:
    """
    Run the full OmniLead-AI pipeline on a list of raw leads.

    Args:
        raw_leads: Input lead records.
        output_path: Optional CSV file path for export.
        progress_callback: Async callable(lead, index, total) for live UI updates.

    Returns:
        List of fully enriched lead records.
    """
    total = len(raw_leads)
    logger.info(f"Starting OmniLead-AI pipeline: {total} leads | mock_mode={settings.mock_mode}")

    tasks = [process_single_lead(lead) for lead in raw_leads]
    results: list[EnrichedLead] = []

    for idx, coro in enumerate(asyncio.as_completed(tasks)):
        lead = await coro
        results.append(lead)
        if progress_callback:
            await progress_callback(lead, idx + 1, total)

    # ── Export ───────────────────────────────────────────────────────────────
    if output_path:
        export_to_csv(results, output_path)

    hot = sum(1 for r in results if r.is_hot_lead)
    enriched = sum(1 for r in results if r.status == LeadStatus.ENRICHED or r.status == LeadStatus.DISPATCHED)
    logger.info(f"Pipeline complete: {enriched}/{total} enriched, {hot} hot leads")

    return results

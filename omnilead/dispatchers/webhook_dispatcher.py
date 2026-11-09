"""
Webhook Dispatcher with Exponential Backoff
============================================
Sends enriched leads to external CRM systems (GoHighLevel, HubSpot, Zapier, Make)
and fires Slack/Discord alerts for hot leads (ICP score >= 80).

Features:
- 3-attempt exponential backoff with jitter (tenacity)
- Configurable per-platform payload serialization
- Graceful degradation: on failure, logs error but does NOT crash the pipeline
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx
from tenacity import AsyncRetrying, RetryError, stop_after_attempt, wait_exponential

from omnilead.config import settings
from omnilead.models.schemas import EnrichedLead

logger = logging.getLogger(__name__)

_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "OmniLead-AI/1.0 (Automation Pipeline)",
}


async def dispatch_lead(lead: EnrichedLead) -> bool:
    """
    Dispatch a fully enriched lead to configured endpoints.

    Returns True if at least one dispatch succeeded.
    """
    if settings.mock_mode:
        await asyncio.sleep(0.1)
        logger.info(f"[MOCK] Dispatched lead for {lead.company_name} (ICP={lead.icp_score})")
        return True

    tasks = []

    if settings.crm_webhook_url:
        tasks.append(_send_to_crm(lead))

    if lead.is_hot_lead:
        if settings.slack_webhook_url:
            tasks.append(_send_slack_alert(lead))
        if settings.discord_webhook_url:
            tasks.append(_send_discord_alert(lead))

    if not tasks:
        logger.debug(f"No dispatch endpoints configured for {lead.company_name}")
        return False

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return any(r is True for r in results)


async def _post_with_retry(url: str, payload: dict) -> bool:
    """POST with 3-attempt exponential backoff (1s → 2s → 4s + jitter)."""
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=False,
        ):
            with attempt:
                async with httpx.AsyncClient(timeout=10, headers=_HEADERS) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    return True
    except RetryError:
        logger.error(f"All retry attempts failed for POST to {url[:50]}...")
        return False
    except Exception as exc:
        logger.error(f"Unexpected dispatch error: {exc}")
        return False
    return False


async def _send_to_crm(lead: EnrichedLead) -> bool:
    """Send lead to GoHighLevel / HubSpot / Zapier / Make webhook."""
    payload = {
        "source": "omnilead-ai",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "company": {
            "name": lead.company_name,
            "website": lead.website,
            "niche": lead.niche,
            "detected_stack": lead.detected_stack,
        },
        "contact": {
            "name": lead.prospect_name,
            "email": lead.prospect_email,
            "role": lead.prospect_role,
        },
        "ai_enrichment": {
            "icp_score": lead.icp_score,
            "is_hot_lead": lead.is_hot_lead,
            "summary": lead.company_summary,
            "pain_points": lead.pain_points,
            "icebreaker": lead.icebreaker,
            "value_proposition": lead.value_proposition,
            "suggested_cta": lead.suggested_cta,
        },
        "deliverability": {
            "email_valid": lead.email_valid,
            "email_risk": lead.email_risk.value,
            "deliverability_score": lead.email_deliverability_score,
        },
    }
    return await _post_with_retry(settings.crm_webhook_url, payload)


async def _send_slack_alert(lead: EnrichedLead) -> bool:
    """Send a formatted Slack message for hot leads."""
    score_emoji = "🔥" if lead.icp_score >= 90 else "⭐"
    payload = {
        "text": f"{score_emoji} *Hot Lead Detected!* — {lead.company_name}",
        "attachments": [
            {
                "color": "#36a64f",
                "fields": [
                    {"title": "Company", "value": lead.company_name, "short": True},
                    {"title": "ICP Score", "value": f"{lead.icp_score}/100", "short": True},
                    {"title": "Contact", "value": f"{lead.prospect_name} <{lead.prospect_email}>", "short": False},
                    {"title": "Icebreaker", "value": lead.icebreaker, "short": False},
                    {"title": "Website", "value": f"<{lead.website}|{lead.company_name}>", "short": True},
                ],
                "footer": "OmniLead-AI Pipeline",
                "ts": int(datetime.now(timezone.utc).timestamp()),
            }
        ],
    }
    return await _post_with_retry(settings.slack_webhook_url, payload)


async def _send_discord_alert(lead: EnrichedLead) -> bool:
    """Send a Discord embed for hot leads."""
    score_color = 0x2ECC71 if lead.icp_score >= 90 else 0xF39C12
    payload = {
        "embeds": [
            {
                "title": f"🔥 Hot Lead: {lead.company_name}",
                "url": lead.website,
                "color": score_color,
                "fields": [
                    {"name": "ICP Score", "value": f"`{lead.icp_score}/100`", "inline": True},
                    {"name": "Contact", "value": f"{lead.prospect_name} — {lead.prospect_email}", "inline": True},
                    {"name": "Icebreaker", "value": lead.icebreaker, "inline": False},
                    {"name": "Pain Points", "value": "\n".join(f"• {p}" for p in lead.pain_points[:2]), "inline": False},
                ],
                "footer": {"text": "OmniLead-AI Automation Pipeline"},
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }
    return await _post_with_retry(settings.discord_webhook_url, payload)

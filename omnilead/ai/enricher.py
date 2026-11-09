"""
Gemini AI Enrichment Engine
=============================
Uses gemini-3.8-flash to analyze scraped company data and generate:
  - Company summary
  - Inferred operational pain points
  - Hyper-personalized cold email icebreaker
  - Value proposition tailored to automation services
  - ICP (Ideal Customer Profile) match score 0-100
  - Suggested CTA for first outreach

Supports full MOCK_MODE for zero-credential demonstrations.
"""
from __future__ import annotations

import asyncio
import json
import random

from omnilead.config import settings
from omnilead.models.schemas import AIEnrichment, ScrapedData

# ── Mock Enrichment Dataset ───────────────────────────────────────────────────
_MOCK_ENRICHMENTS = [
    AIEnrichment(
        company_summary=(
            "GrowthStack is a B2B revenue operations platform that automates lead scoring, "
            "pipeline hygiene, and CRM enrichment for high-velocity sales teams."
        ),
        inferred_pain_points=[
            "Sales reps are manually updating CRM fields, costing 8–12 hours per rep per week",
            "Lead handoff from marketing to sales has significant data gaps causing slow follow-up",
            "No automated deduplication means duplicate records inflate their pipeline metrics",
        ],
        personalized_icebreaker=(
            "Noticed GrowthStack's RevOps platform integrates with both HubSpot and Salesforce — "
            "most teams using dual CRMs tell us that keeping them in sync is their #1 silent time-drain."
        ),
        value_proposition=(
            "We build automated sync and enrichment pipelines that eliminate the CRM data gaps "
            "your reps complain about — no more manual updates, no more duplicate records."
        ),
        icp_score=92,
        suggested_cta="Would it be worth a 15-min call to show you what that looks like in practice?",
    ),
    AIEnrichment(
        company_summary=(
            "EcomElite is a full-service Shopify Plus agency helping D2C brands scale "
            "through conversion optimization, email flows, and paid media creative."
        ),
        inferred_pain_points=[
            "Client reporting is likely manual and time-consuming across multiple Shopify stores",
            "Klaviyo flow performance review and optimization is probably done ad-hoc",
            "Scaling to new client accounts requires duplicating setup work that could be templated",
        ],
        personalized_icebreaker=(
            "Saw that EcomElite runs Klaviyo and Shopify across your client base — "
            "agencies at your scale usually spend 20+ hours a month just on reporting that could run on its own."
        ),
        value_proposition=(
            "We automate the repeatable parts of agency operations — client dashboards, "
            "flow audit alerts, and onboarding workflows — so your team can focus on strategy."
        ),
        icp_score=85,
        suggested_cta="Happy to map out exactly which parts of your workflow we could automate first — interested?",
    ),
    AIEnrichment(
        company_summary=(
            "OutreachPro provides cold email infrastructure including domain warming, "
            "DKIM/SPF/DMARC configuration, and deliverability monitoring for agencies."
        ),
        inferred_pain_points=[
            "Manually onboarding new client domains for warmup is a bottleneck at scale",
            "Deliverability alerts are likely reactive rather than proactive",
            "No automated escalation path when inboxes start hitting spam folders",
        ],
        personalized_icebreaker=(
            "OutreachPro's deliverability monitoring is impressive — "
            "curious if your team has automated alerts when a client's reputation drops below threshold or if that's still manual triage."
        ),
        value_proposition=(
            "We build proactive monitoring pipelines that alert and auto-pause campaigns "
            "before inbox placement drops, protecting your clients' sender reputations without manual oversight."
        ),
        icp_score=88,
        suggested_cta="Would love to show you a 5-min demo of how we monitor 200+ mailboxes in real time — worth a quick look?",
    ),
]


async def enrich_lead(company_name: str, scraped: ScrapedData, niche: str = "") -> AIEnrichment:
    """
    Generate AI-powered lead enrichment for a company.

    Args:
        company_name: Display name of the target company.
        scraped: Crawled website data to contextualize the prompt.
        niche: Optional ICP tag (e.g. "B2B SaaS", "E-commerce Agency").

    Returns:
        AIEnrichment with structured fields for outreach personalization.
    """
    if settings.mock_mode or not settings.ai_enabled:
        await asyncio.sleep(random.uniform(0.2, 0.6))
        return random.choice(_MOCK_ENRICHMENTS)

    return await _live_enrich(company_name, scraped, niche)


async def _live_enrich(company_name: str, scraped: ScrapedData, niche: str) -> AIEnrichment:
    """Call Gemini 3.8 Flash with strict JSON schema output."""
    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)

    stack_str = ", ".join(scraped.detected_stack) if scraped.detected_stack else "unknown"
    social_str = ", ".join(f"{k}: {v}" for k, v in scraped.social_links.items()) if scraped.social_links else "none found"

    prompt = f"""You are an expert B2B cold outreach strategist specializing in automation and digital services.

Analyze the following company and produce a JSON object matching the exact schema below.

COMPANY DETAILS:
- Name: {company_name}
- Niche/Industry: {niche or "Unknown"}
- Website: {scraped.website}
- Meta Title: {scraped.meta_title or "N/A"}
- Meta Description: {scraped.meta_description or "N/A"}
- Page Content Summary: {scraped.page_summary[:800] if scraped.page_summary else "N/A"}
- Detected Tech Stack: {stack_str}
- Social Profiles: {social_str}

OUTPUT JSON SCHEMA (respond ONLY with valid JSON, no markdown):
{{
  "company_summary": "2-sentence executive summary of what the company does and who they serve",
  "inferred_pain_points": ["Pain point 1", "Pain point 2", "Pain point 3"],
  "personalized_icebreaker": "Single hyper-specific cold email opening sentence referencing something unique about their business",
  "value_proposition": "Concise pitch sentence connecting their pain points to automation/AI solutions",
  "icp_score": 0-100,
  "suggested_cta": "Suggested call-to-action for first outreach email"
}}

Rules:
- icebreaker must reference a SPECIFIC, OBSERVABLE detail from the company data (not generic praise)
- pain_points must be ACUTE business problems, not vague observations
- icp_score reflects how strong a prospect they are for automation/AI services (80+ = hot lead)
- Keep all text concise and direct — no filler phrases like "It seems like" or "I noticed that"
"""

    interaction = client.interactions.create(
        model=settings.gemini_model,
        input=prompt,
        config={
            "generation_config": {
                "response_mime_type": "application/json",
                "temperature": 0.4,
                "max_output_tokens": 1024,
            }
        }
    )

    raw = interaction.output_text or "{}"
    # Strip markdown fences if model wrapped it
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    data = json.loads(raw)

    return AIEnrichment(**data)

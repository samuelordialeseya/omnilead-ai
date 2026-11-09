"""
Tests: AI Enricher (mock mode)
"""
import pytest
from omnilead.ai.enricher import enrich_lead
from omnilead.core.crawler import crawl_website


@pytest.mark.asyncio
async def test_enrichment_returns_valid_schema():
    scraped = await crawl_website("https://example.com")
    result = await enrich_lead("Example Corp", scraped, "B2B SaaS")
    assert isinstance(result.company_summary, str)
    assert len(result.company_summary) > 10


@pytest.mark.asyncio
async def test_enrichment_icp_score_in_range():
    scraped = await crawl_website("https://example.com")
    result = await enrich_lead("Example Corp", scraped)
    assert 0 <= result.icp_score <= 100


@pytest.mark.asyncio
async def test_enrichment_pain_points_is_list():
    scraped = await crawl_website("https://example.com")
    result = await enrich_lead("Example Corp", scraped)
    assert isinstance(result.inferred_pain_points, list)
    assert len(result.inferred_pain_points) >= 1


@pytest.mark.asyncio
async def test_enrichment_icebreaker_is_string():
    scraped = await crawl_website("https://example.com")
    result = await enrich_lead("Example Corp", scraped)
    assert isinstance(result.personalized_icebreaker, str)
    assert len(result.personalized_icebreaker) > 20


@pytest.mark.asyncio
async def test_enrichment_suggested_cta_present():
    scraped = await crawl_website("https://example.com")
    result = await enrich_lead("Example Corp", scraped)
    assert isinstance(result.suggested_cta, str)
    assert len(result.suggested_cta) > 5

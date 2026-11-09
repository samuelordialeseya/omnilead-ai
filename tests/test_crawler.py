"""
Tests: Web Crawler (mock mode)
"""
import pytest
from omnilead.core.crawler import crawl_website


@pytest.mark.asyncio
async def test_crawl_returns_scraped_data():
    result = await crawl_website("https://example-agency.com")
    assert result.website == "https://example-agency.com"
    assert result.crawl_success is True


@pytest.mark.asyncio
async def test_crawl_has_meta_title():
    result = await crawl_website("https://example.com")
    assert isinstance(result.meta_title, str)
    assert len(result.meta_title) > 0


@pytest.mark.asyncio
async def test_crawl_detected_stack_is_list():
    result = await crawl_website("https://any-site.com")
    assert isinstance(result.detected_stack, list)


@pytest.mark.asyncio
async def test_crawl_social_links_is_dict():
    result = await crawl_website("https://any-site.com")
    assert isinstance(result.social_links, dict)


@pytest.mark.asyncio
async def test_crawl_page_summary_is_string():
    result = await crawl_website("https://any-site.com")
    assert isinstance(result.page_summary, str)

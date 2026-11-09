"""
Tests: Email Verifier
"""
import pytest
from omnilead.core.verifier import verify_email
from omnilead.models.schemas import EmailRisk


@pytest.mark.asyncio
async def test_valid_email_returns_safe():
    result = await verify_email("contact@growthstack.io")
    assert result.is_valid_format is True
    assert result.risk == EmailRisk.SAFE
    assert result.deliverability_score >= 80


@pytest.mark.asyncio
async def test_disposable_email_detected():
    result = await verify_email("throwaway@mailinator.com")
    assert result.is_disposable is True
    assert result.risk == EmailRisk.DISPOSABLE
    assert result.deliverability_score < 30


@pytest.mark.asyncio
async def test_invalid_format_email():
    result = await verify_email("not-an-email")
    assert result.is_valid_format is False
    assert result.risk == EmailRisk.INVALID


@pytest.mark.asyncio
async def test_empty_email():
    result = await verify_email("")
    assert result.is_valid_format is False


@pytest.mark.asyncio
async def test_email_with_plus_addressing():
    result = await verify_email("user+filter@acme.com")
    assert result.is_valid_format is True


@pytest.mark.asyncio
async def test_domain_extracted_correctly():
    result = await verify_email("ceo@bigagency.com")
    assert result.domain == "bigagency.com"

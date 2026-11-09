"""
Email Deliverability Verifier
==============================
Three-layer verification:
  1. RFC 5322 format regex
  2. Disposable email domain blacklist (50+ domains)
  3. Async DNS MX record lookup
"""
from __future__ import annotations

import asyncio
import re
from functools import lru_cache

import dns.asyncresolver
import dns.exception

from omnilead.config import settings
from omnilead.models.schemas import EmailRisk, EmailValidationResult

# ── RFC 5322 simplified regex ─────────────────────────────────────────────────
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+"
    r"(?:\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~\-]+)*"
    r"@"
    r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)+"
    r"[a-zA-Z]{2,}$"
)

# ── Disposable email domain blacklist ─────────────────────────────────────────
_DISPOSABLE_DOMAINS: frozenset[str] = frozenset({
    "mailinator.com", "guerrillamail.com", "tempmail.com", "10minutemail.com",
    "throwaway.email", "yopmail.com", "fakeinbox.com", "getairmail.com",
    "sharklasers.com", "guerrillamailblock.com", "grr.la", "guerrillamail.info",
    "guerrillamail.biz", "guerrillamail.de", "guerrillamail.net", "guerrillamail.org",
    "spam4.me", "trashmail.com", "trashmail.me", "trashmail.net", "trashmail.at",
    "dispostable.com", "mailnull.com", "tempr.email", "discard.email",
    "spamgourmet.com", "spamgourmet.net", "mytrashmail.com", "mailexpire.com",
    "maildrop.cc", "spamfree24.org", "deadaddress.com", "spamherelots.com",
    "binkmail.com", "mailzilla.com", "einrot.com", "discardmail.com",
    "mailscrap.com", "mailbreak.com", "junk1.de", "dispostable.com",
    "classicalaudio.com", "jetable.fr.nf", "nospam.ze.tc", "notsharingmy.info",
    "anonbox.net", "anonymbox.com", "maileater.com", "trash-mail.at",
    "spammotel.com", "e4ward.com", "mailbidon.com", "spamgob.com",
})


@lru_cache(maxsize=512)
def _is_disposable(domain: str) -> bool:
    return domain.lower() in _DISPOSABLE_DOMAINS


async def verify_email(email: str) -> EmailValidationResult:
    """
    Run three-layer verification on a prospect email.

    Mock mode returns a plausible result instantly.
    Live mode performs real DNS lookups.
    """
    email = email.strip().lower()

    if settings.mock_mode:
        await asyncio.sleep(0.05)
        return _mock_result(email)

    return await _live_verify(email)


def _mock_result(email: str) -> EmailValidationResult:
    """Generate a realistic mock verification result."""
    if not email:
        return EmailValidationResult(email=email, is_valid_format=False, risk=EmailRisk.INVALID)

    if not _EMAIL_RE.match(email):
        return EmailValidationResult(email=email, is_valid_format=False, risk=EmailRisk.INVALID, deliverability_score=0)

    domain = email.split("@", 1)[1]

    if _is_disposable(domain):
        return EmailValidationResult(
            email=email, is_valid_format=True, domain=domain,
            mx_records_found=False, is_disposable=True,
            risk=EmailRisk.DISPOSABLE, deliverability_score=10,
        )

    return EmailValidationResult(
        email=email, is_valid_format=True, domain=domain,
        mx_records_found=True, is_disposable=False,
        risk=EmailRisk.SAFE, deliverability_score=90,
    )


async def _live_verify(email: str) -> EmailValidationResult:
    """Perform real DNS MX record lookup."""
    if not email:
        return EmailValidationResult(email=email, is_valid_format=False, risk=EmailRisk.INVALID)

    if not _EMAIL_RE.match(email):
        return EmailValidationResult(email=email, is_valid_format=False, risk=EmailRisk.INVALID, deliverability_score=0)

    domain = email.split("@", 1)[1]

    if _is_disposable(domain):
        return EmailValidationResult(
            email=email, is_valid_format=True, domain=domain,
            mx_records_found=False, is_disposable=True,
            risk=EmailRisk.DISPOSABLE, deliverability_score=10,
        )

    # DNS MX lookup
    mx_found = False
    try:
        answers = await dns.asyncresolver.resolve(domain, "MX", lifetime=5.0)
        mx_found = len(answers) > 0
    except (dns.exception.DNSException, Exception):
        mx_found = False

    if not mx_found:
        return EmailValidationResult(
            email=email, is_valid_format=True, domain=domain,
            mx_records_found=False, is_disposable=False,
            risk=EmailRisk.NO_MX, deliverability_score=20,
        )

    return EmailValidationResult(
        email=email, is_valid_format=True, domain=domain,
        mx_records_found=True, is_disposable=False,
        risk=EmailRisk.SAFE, deliverability_score=92,
    )

"""
Async Web Crawler
=================
Fetches company websites and extracts meaningful signals:
  - Meta title + description
  - Cleaned body text excerpt
  - Detected technology stack keywords
  - Social media profile links
  - Email addresses found in page content
"""
from __future__ import annotations

import asyncio
import random
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from omnilead.config import settings
from omnilead.models.schemas import ScrapedData

# ── User-Agent Rotation ───────────────────────────────────────────────────────
_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
]

# ── Tech Stack Keyword Signals ────────────────────────────────────────────────
_STACK_SIGNALS: dict[str, list[str]] = {
    "Shopify": ["shopify", "myshopify"],
    "WordPress": ["wp-content", "wp-json", "wordpress"],
    "HubSpot": ["hubspot", "hs-scripts"],
    "Intercom": ["intercom", "intercomcdn"],
    "Salesforce": ["salesforce", "pardot", "force.com"],
    "React": ["react-dom", "__next", "nextjs"],
    "Vue.js": ["vue.js", "vue.min.js"],
    "Webflow": ["webflow.com", "wf-form"],
    "MailChimp": ["mailchimp", "mc-embedded-subscribe"],
    "Google Analytics": ["gtag(", "google-analytics", "UA-"],
    "Hotjar": ["hotjar"],
    "Stripe": ["stripe.js", "js.stripe.com"],
    "Klaviyo": ["klaviyo"],
    "Zapier": ["zapier"],
    "Drift": ["drift.com"],
    "ActiveCampaign": ["activecampaign"],
}

# ── Social URL Patterns ───────────────────────────────────────────────────────
_SOCIAL_PATTERNS: dict[str, re.Pattern] = {
    "linkedin": re.compile(r"linkedin\.com/(company|in)/[\w\-]+", re.I),
    "twitter": re.compile(r"(?:twitter|x)\.com/[\w]+", re.I),
    "facebook": re.compile(r"facebook\.com/[\w.\-]+", re.I),
    "instagram": re.compile(r"instagram\.com/[\w.]+", re.I),
    "youtube": re.compile(r"youtube\.com/(?:c|channel|@)[\w\-]+", re.I),
}

_EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.I)

# ── Mock Data ─────────────────────────────────────────────────────────────────
_MOCK_PAGES = [
    {
        "meta_title": "GrowthStack | B2B Revenue Operations Software",
        "meta_description": "GrowthStack automates sales pipelines, lead scoring, and CRM enrichment for high-velocity B2B teams.",
        "page_summary": "We help B2B SaaS companies scale outbound by automating repetitive RevOps workflows. Our platform integrates with HubSpot, Salesforce, and Outreach to automate lead qualification, meeting scheduling, and pipeline hygiene.",
        "detected_stack": ["HubSpot", "React", "Stripe", "Google Analytics"],
        "social_links": {"linkedin": "linkedin.com/company/growthstack", "twitter": "twitter.com/growthstack"},
        "emails_found": [],
    },
    {
        "meta_title": "EcomElite Agency | Shopify Growth Partners",
        "meta_description": "Full-service Shopify Plus agency specializing in D2C growth, conversion optimization, and email automation.",
        "page_summary": "EcomElite partners with 7-figure Shopify brands to build profitable growth systems. We specialize in email flows, paid media creative, and post-purchase retention using Klaviyo, Shopify, and Gorgias.",
        "detected_stack": ["Shopify", "Klaviyo", "Google Analytics", "Hotjar"],
        "social_links": {"linkedin": "linkedin.com/company/ecomelite-agency", "instagram": "instagram.com/ecomelite"},
        "emails_found": ["hello@ecomelite.com"],
    },
    {
        "meta_title": "OutreachPro | Cold Email Infrastructure for Agencies",
        "meta_description": "Warm mailboxes, deliverability monitoring, and automated sequence management for cold email agencies.",
        "page_summary": "OutreachPro provides the infrastructure cold email agencies need to run at scale. We handle domain warming, DKIM/DMARC/SPF setup, inbox rotation, and deliverability monitoring so your team can focus on copy and strategy.",
        "detected_stack": ["React", "Stripe", "Intercom", "Zapier"],
        "social_links": {"linkedin": "linkedin.com/company/outreachpro", "twitter": "twitter.com/outreachpro_io"},
        "emails_found": ["team@outreachpro.io"],
    },
]


async def crawl_website(website: str) -> ScrapedData:
    """
    Fetch and parse a company's website.

    In MOCK_MODE, returns a randomized realistic dataset without hitting
    any external URL. In production mode, performs an async HTTP GET.
    """
    if settings.mock_mode:
        await asyncio.sleep(random.uniform(0.1, 0.4))  # simulate network latency
        mock = random.choice(_MOCK_PAGES)
        return ScrapedData(website=website, crawl_success=True, **mock)

    return await _live_crawl(website)


async def _live_crawl(url: str) -> ScrapedData:
    """Perform real async HTTP scrape."""
    headers = {
        "User-Agent": random.choice(_USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=settings.request_timeout,
            headers=headers,
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text
    except (httpx.RequestError, httpx.HTTPStatusError) as exc:
        return ScrapedData(website=url, crawl_success=False, error=str(exc))

    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in soup(["script", "style", "noscript", "svg", "nav", "footer", "iframe"]):
        tag.decompose()

    meta_title = (soup.find("title") or {}).get_text(strip=True) if soup.find("title") else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "") if meta_desc_tag else ""

    raw_text = soup.get_text(separator=" ", strip=True)
    page_summary = " ".join(raw_text.split())[:1500]  # first 1500 chars of clean text

    # Detect tech stack
    raw_html_lower = html.lower()
    detected_stack = [name for name, signals in _STACK_SIGNALS.items() if any(s in raw_html_lower for s in signals)]

    # Extract social links
    social_links: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        href: str = anchor["href"]
        for platform, pattern in _SOCIAL_PATTERNS.items():
            if pattern.search(href) and platform not in social_links:
                social_links[platform] = href.strip()

    # Extract emails
    emails_found = list(set(_EMAIL_PATTERN.findall(raw_text)))[:10]

    return ScrapedData(
        website=url,
        meta_title=meta_title,
        meta_description=meta_description,
        page_summary=page_summary,
        detected_stack=detected_stack,
        social_links=social_links,
        emails_found=emails_found,
        crawl_success=True,
    )

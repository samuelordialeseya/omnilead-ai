"""
Tests: FastAPI Server
"""
import pytest
from fastapi.testclient import TestClient
from omnilead.api.server import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "mock_mode" in data


def test_health_contains_model_info():
    response = client.get("/api/v1/health")
    data = response.json()
    assert "gemini_model" in data
    assert data["gemini_model"] == "gemini-3.8-flash"


def test_enrich_single_lead():
    response = client.post("/api/v1/enrich", json={
        "company_name": "TestCorp",
        "website": "https://testcorp.com",
        "prospect_name": "Jane Smith",
        "prospect_email": "jane@testcorp.com",
        "prospect_role": "Head of Growth",
        "niche": "B2B SaaS",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["company_name"] == "TestCorp"
    assert "icp_score" in data
    assert isinstance(data["icp_score"], int)
    assert 0 <= data["icp_score"] <= 100


def test_enrich_missing_required_fields():
    response = client.post("/api/v1/enrich", json={"company_name": "Only Name"})
    assert response.status_code == 422  # Validation error (missing website)


def test_dashboard_returns_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_batch_rejects_non_csv():
    response = client.post("/api/v1/batch", files={"file": ("leads.txt", b"hello", "text/plain")})
    assert response.status_code == 400

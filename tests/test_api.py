import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_chat_endpoint_basic() -> None:
    response = client.post("/chat", json={"message": "I want to visit a beach destination on a budget."})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "extracted_preferences" in data
    assert "recommendations_preview" in data
    assert isinstance(data["recommendations_preview"], list)


def test_chat_endpoint_extracts_travel_style() -> None:
    response = client.post("/chat", json={"message": "I love hiking and mountain adventures."})
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_preferences"].get("travel_style") == "adventure"


def test_chat_endpoint_extracts_budget() -> None:
    response = client.post("/chat", json={"message": "I want something luxury and premium."})
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_preferences"].get("budget") == "luxury"


def test_recommend_trip_returns_results() -> None:
    response = client.post("/recommend-trip", json={})
    assert response.status_code == 200
    data = response.json()
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


def test_recommend_trip_filter_by_style() -> None:
    response = client.post("/recommend-trip", json={"travel_style": "beach"})
    assert response.status_code == 200
    data = response.json()
    for rec in data["recommendations"]:
        assert rec["travel_style"] == "beach"


def test_get_user_profile_default() -> None:
    response = client.get("/user-profile")
    assert response.status_code == 200
    data = response.json()
    assert "preferred_destinations" in data
    assert "travel_style" in data
    assert "budget" in data


def test_update_user_profile() -> None:
    payload = {
        "preferred_destinations": ["Japan", "Thailand"],
        "travel_style": "cultural",
        "budget": "moderate",
        "dietary_restrictions": ["vegetarian"],
        "interests": ["history", "food"],
    }
    response = client.post("/user-profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["travel_style"] == "cultural"
    assert data["budget"] == "moderate"
    assert "Japan" in data["preferred_destinations"]

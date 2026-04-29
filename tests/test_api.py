import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

FULL_ITEM = {
    "user_id": {"S": "user-123"},
    "preferred_destinations": {"L": [{"S": "Japan"}, {"S": "Thailand"}]},
    "travel_style": {"S": "cultural"},
    "budget": {"S": "moderate"},
    "dietary_restrictions": {"L": [{"S": "vegetarian"}]},
    "interests": {"L": [{"S": "history"}, {"S": "food"}]},
}


@pytest.fixture
def mock_dynamodb():
    with patch("app.services.user_service.get_dynamodb_client") as mock_factory:
        client_mock = MagicMock()
        client_mock.get_item.return_value = {}
        client_mock.put_item.return_value = {}
        mock_factory.return_value = client_mock
        yield client_mock


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


def test_get_user_profile_default(mock_dynamodb) -> None:
    mock_dynamodb.get_item.return_value = {"Item": FULL_ITEM}
    response = client.get("/user-profile/user-123")
    assert response.status_code == 200
    data = response.json()
    assert "preferred_destinations" in data
    assert "travel_style" in data
    assert "budget" in data
    assert "dietary_restrictions" in data
    assert "interests" in data


def test_update_user_profile(mock_dynamodb) -> None:
    updated_item = {
        "user_id": {"S": "user-123"},
        "preferred_destinations": {"L": [{"S": "Japan"}, {"S": "Thailand"}]},
        "travel_style": {"S": "cultural"},
        "budget": {"S": "moderate"},
        "dietary_restrictions": {"L": [{"S": "vegetarian"}]},
        "interests": {"L": [{"S": "history"}, {"S": "food"}]},
    }
    mock_dynamodb.get_item.side_effect = [
        {},                        # _fetch inside update_or_create_profile
        {"Item": updated_item},    # _fetch inside get_profile after save
    ]
    payload = {
        "preferred_destinations": ["Japan", "Thailand"],
        "travel_style": "cultural",
        "budget": "moderate",
        "dietary_restrictions": ["vegetarian"],
        "interests": ["history", "food"],
    }
    response = client.post("/user-profile/user-123", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["travel_style"] == "cultural"
    assert data["budget"] == "moderate"
    assert "Japan" in data["preferred_destinations"]

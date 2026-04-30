import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_chat_service
from app.models.schemas import ChatResponse, RecommendationPreview, UserPreferencesSchema

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


def _make_chat_response(travel_style: str | None = None, budget: str | None = None) -> ChatResponse:
    return ChatResponse(
        reply="Here are some travel recommendations!",
        session_id="test-session-id",
        extracted_preferences=UserPreferencesSchema(travel_style=travel_style, budget=budget),
        recommendations_preview=[RecommendationPreview(destination="Bali", description="Beautiful island")],
    )


@pytest.fixture
def mock_chat_service():
    mock_service = MagicMock()
    app.dependency_overrides[get_chat_service] = lambda: mock_service
    yield mock_service
    app.dependency_overrides.pop(get_chat_service, None)


def test_chat_endpoint_basic(mock_chat_service) -> None:
    mock_chat_service.handle_message.return_value = _make_chat_response()
    response = client.post("/chat", json={"message": "I want to visit a beach destination on a budget."})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "extracted_preferences" in data
    assert "recommendations_preview" in data
    assert isinstance(data["recommendations_preview"], list)


def test_chat_endpoint_extracts_travel_style(mock_chat_service) -> None:
    mock_chat_service.handle_message.return_value = _make_chat_response(travel_style="adventure")
    response = client.post("/chat", json={"message": "I love hiking and mountain adventures."})
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_preferences"].get("travel_style") == "adventure"


def test_chat_endpoint_extracts_budget(mock_chat_service) -> None:
    mock_chat_service.handle_message.return_value = _make_chat_response(budget="luxury")
    response = client.post("/chat", json={"message": "I want something luxury and premium."})
    assert response.status_code == 200
    data = response.json()
    assert data["extracted_preferences"].get("budget") == "luxury"



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

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.domain import UserProfile
from app.models.schemas import UserProfileRequest
from app.services.user_service import UserService, _item_to_profile, _profile_to_item


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FULL_ITEM = {
    "user_id": {"S": "user-1"},
    "preferred_destinations": {"L": [{"S": "Italy"}, {"S": "Japan"}]},
    "travel_style": {"S": "cultural"},
    "budget": {"S": "medium"},
    "dietary_restrictions": {"L": [{"S": "vegetarian"}]},
    "interests": {"L": [{"S": "history"}, {"S": "food"}]},
}

FULL_PROFILE = UserProfile(
    user_id="user-1",
    preferred_destinations=["Italy", "Japan"],
    travel_style="cultural",
    budget="medium",
    dietary_restrictions=["vegetarian"],
    interests=["history", "food"],
)


# ---------------------------------------------------------------------------
# _item_to_profile
# ---------------------------------------------------------------------------


def test_item_to_profile_full():
    profile = _item_to_profile(FULL_ITEM)
    assert profile.user_id == "user-1"
    assert profile.preferred_destinations == ["Italy", "Japan"]
    assert profile.travel_style == "cultural"
    assert profile.budget == "medium"
    assert profile.dietary_restrictions == ["vegetarian"]
    assert profile.interests == ["history", "food"]


def test_item_to_profile_missing_optional_fields():
    item = {
        "user_id": {"S": "user-2"},
    }
    profile = _item_to_profile(item)
    assert profile.user_id == "user-2"
    assert profile.preferred_destinations == []
    assert profile.travel_style is None
    assert profile.budget is None
    assert profile.dietary_restrictions == []
    assert profile.interests == []


# ---------------------------------------------------------------------------
# _profile_to_item
# ---------------------------------------------------------------------------


def test_profile_to_item_full():
    item = _profile_to_item(FULL_PROFILE)
    assert item["user_id"] == {"S": "user-1"}
    assert item["preferred_destinations"] == {"L": [{"S": "Italy"}, {"S": "Japan"}]}
    assert item["travel_style"] == {"S": "cultural"}
    assert item["budget"] == {"S": "medium"}
    assert item["dietary_restrictions"] == {"L": [{"S": "vegetarian"}]}
    assert item["interests"] == {"L": [{"S": "history"}, {"S": "food"}]}


def test_profile_to_item_omits_none_fields():
    profile = UserProfile(user_id="user-3")
    item = _profile_to_item(profile)
    assert "travel_style" not in item
    assert "budget" not in item


# ---------------------------------------------------------------------------
# UserService
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_client():
    with patch("app.services.user_service.get_dynamodb_client") as mock_factory:
        client = MagicMock()
        mock_factory.return_value = client
        yield client


class TestGetProfile:
    def test_returns_profile_when_found(self, mock_client):
        mock_client.get_item.return_value = {"Item": FULL_ITEM}
        response = UserService().get_profile("user-1")
        assert response.user_id == "user-1"
        assert response.travel_style == "cultural"
        assert response.preferred_destinations == ["Italy", "Japan"]

    def test_raises_404_when_not_found(self, mock_client):
        mock_client.get_item.return_value = {}
        with pytest.raises(HTTPException) as exc_info:
            UserService().get_profile("unknown")
        assert exc_info.value.status_code == 404


class TestUpdateOrCreateProfile:
    def test_creates_new_profile_when_not_found(self, mock_client):
        mock_client.get_item.side_effect = [
            {},               # _fetch inside update_or_create_profile
            {"Item": {        # _fetch inside get_profile after save
                "user_id": {"S": "new-user"},
                "preferred_destinations": {"L": [{"S": "Portugal"}]},
                "travel_style": {"S": "beach"},
                "budget": {"S": "low"},
                "dietary_restrictions": {"L": []},
                "interests": {"L": []},
            }},
        ]
        request = UserProfileRequest(
            preferred_destinations=["Portugal"],
            travel_style="beach",
            budget="low",
        )
        response = UserService().update_or_create_profile("new-user", request)
        assert mock_client.put_item.called
        assert response.user_id == "new-user"
        assert response.travel_style == "beach"

    def test_updates_existing_profile(self, mock_client):
        updated_item = {**FULL_ITEM, "budget": {"S": "luxury"}}
        mock_client.get_item.side_effect = [
            {"Item": FULL_ITEM},      # _fetch inside update_or_create_profile
            {"Item": updated_item},   # _fetch inside get_profile after save
        ]
        request = UserProfileRequest(budget="luxury")
        response = UserService().update_or_create_profile("user-1", request)
        assert mock_client.put_item.called
        assert response.budget == "luxury"

    def test_partial_update_preserves_existing_fields(self, mock_client):
        mock_client.get_item.side_effect = [
            {"Item": FULL_ITEM},
            {"Item": FULL_ITEM},
        ]
        request = UserProfileRequest(travel_style="adventure")
        UserService().update_or_create_profile("user-1", request)

        saved_item = mock_client.put_item.call_args[1]["Item"]
        assert saved_item["preferred_destinations"] == {"L": [{"S": "Italy"}, {"S": "Japan"}]}
        assert saved_item["travel_style"] == {"S": "adventure"}


class TestUpdateFromPreferences:
    def test_merges_destinations_with_existing(self, mock_client):
        mock_client.get_item.return_value = {"Item": FULL_ITEM}
        UserService().update_from_preferences("user-1", {"preferred_destinations": ["Portugal"]})

        saved_item = mock_client.put_item.call_args[1]["Item"]
        saved_destinations = {v["S"] for v in saved_item["preferred_destinations"]["L"]}
        assert "Italy" in saved_destinations
        assert "Japan" in saved_destinations
        assert "Portugal" in saved_destinations

    def test_creates_profile_when_not_found(self, mock_client):
        mock_client.get_item.return_value = {}
        UserService().update_from_preferences("new-user", {"travel_style": "beach", "budget": "low"})

        assert mock_client.put_item.called
        saved_item = mock_client.put_item.call_args[1]["Item"]
        assert saved_item["user_id"] == {"S": "new-user"}
        assert saved_item["travel_style"] == {"S": "beach"}
        assert saved_item["budget"] == {"S": "low"}

    def test_updates_travel_style_and_budget(self, mock_client):
        mock_client.get_item.return_value = {"Item": FULL_ITEM}
        UserService().update_from_preferences("user-1", {"travel_style": "adventure", "budget": "luxury"})

        saved_item = mock_client.put_item.call_args[1]["Item"]
        assert saved_item["travel_style"] == {"S": "adventure"}
        assert saved_item["budget"] == {"S": "luxury"}

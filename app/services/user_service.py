from fastapi import HTTPException
from app.models.domain import UserProfile, UserPreferences
from app.models.schemas import UserProfileRequest, UserProfileResponse
from app.db.dynamodb import get_dynamodb_client
from app.core.config import settings


def _item_to_profile(item: dict) -> UserProfile:
    return UserProfile(
        user_id=item["user_id"]["S"],
        preferred_destinations=[v["S"] for v in item.get("preferred_destinations", {}).get("L", [])],
        travel_style=item.get("travel_style", {}).get("S"),
        budget=item.get("budget", {}).get("S"),
        dietary_restrictions=[v["S"] for v in item.get("dietary_restrictions", {}).get("L", [])],
        interests=[v["S"] for v in item.get("interests", {}).get("L", [])],
    )


def _profile_to_item(profile: UserProfile) -> dict:
    item: dict = {
        "user_id": {"S": profile.user_id},
        "preferred_destinations": {"L": [{"S": d} for d in profile.preferred_destinations]},
        "dietary_restrictions": {"L": [{"S": r} for r in profile.dietary_restrictions]},
        "interests": {"L": [{"S": i} for i in profile.interests]},
    }
    if profile.travel_style is not None:
        item["travel_style"] = {"S": profile.travel_style}
    if profile.budget is not None:
        item["budget"] = {"S": profile.budget}
    return item


class UserService:
    def _fetch(self, user_id: str) -> UserProfile | None:
        client = get_dynamodb_client()
        response = client.get_item(
            TableName=settings.DYNAMODB_TABLE_USER_PROFILES,
            Key={"user_id": {"S": user_id}},
        )
        item = response.get("Item")
        return _item_to_profile(item) if item else None

    def _save(self, profile: UserProfile) -> None:
        client = get_dynamodb_client()
        client.put_item(
            TableName=settings.DYNAMODB_TABLE_USER_PROFILES,
            Item=_profile_to_item(profile),
        )

    def get_profile(self, user_id: str) -> UserProfileResponse:
        profile = self._fetch(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"User profile '{user_id}' not found")
        return UserProfileResponse(
            user_id=profile.user_id,
            preferred_destinations=profile.preferred_destinations,
            travel_style=profile.travel_style,
            budget=profile.budget,
            dietary_restrictions=profile.dietary_restrictions,
            interests=profile.interests,
        )

    def update_or_create_profile(self, user_id: str, data: UserProfileRequest) -> UserProfileResponse:
        profile = self._fetch(user_id) or UserProfile(user_id=user_id)
        if data.preferred_destinations is not None:
            profile.preferred_destinations = data.preferred_destinations
        if data.travel_style is not None:
            profile.travel_style = data.travel_style
        if data.budget is not None:
            profile.budget = data.budget
        if data.dietary_restrictions is not None:
            profile.dietary_restrictions = data.dietary_restrictions
        if data.interests is not None:
            profile.interests = data.interests
        self._save(profile)
        return self.get_profile(user_id)

    def get_preferences(self, user_id: str) -> UserPreferences:
        profile = self._fetch(user_id)
        if profile is None:
            return UserPreferences()
        return UserPreferences(
            travel_style=profile.travel_style,
            budget=profile.budget,
            preferred_destinations=profile.preferred_destinations,
            dietary_restrictions=profile.dietary_restrictions,
            interests=profile.interests,
        )

    def update_from_preferences(self, user_id: str, preferences: UserPreferences) -> None:
        profile = self._fetch(user_id) or UserProfile(user_id=user_id)
        if preferences.travel_style is not None:
            profile.travel_style = preferences.travel_style
        if preferences.budget is not None:
            profile.budget = preferences.budget
        if preferences.preferred_destinations:
            existing = set(profile.preferred_destinations)
            existing.update(preferences.preferred_destinations)
            profile.preferred_destinations = list(existing)
        if preferences.dietary_restrictions:
            existing_dr = set(profile.dietary_restrictions)
            existing_dr.update(preferences.dietary_restrictions)
            profile.dietary_restrictions = list(existing_dr)
        if preferences.interests:
            existing_int = set(profile.interests)
            existing_int.update(preferences.interests)
            profile.interests = list(existing_int)
        self._save(profile)

from app.models.domain import UserProfile
from app.models.schemas import UserProfileRequest, UserProfileResponse


class UserService:
    def __init__(self) -> None:
        self._profile: UserProfile = UserProfile()

    def get_profile(self) -> UserProfileResponse:
        return UserProfileResponse(
            preferred_destinations=self._profile.preferred_destinations,
            travel_style=self._profile.travel_style,
            budget=self._profile.budget,
            dietary_restrictions=self._profile.dietary_restrictions,
            interests=self._profile.interests,
        )

    def update_profile(self, data: UserProfileRequest) -> UserProfileResponse:
        if data.preferred_destinations:
            self._profile.preferred_destinations = data.preferred_destinations
        if data.travel_style is not None:
            self._profile.travel_style = data.travel_style
        if data.budget is not None:
            self._profile.budget = data.budget
        if data.dietary_restrictions:
            self._profile.dietary_restrictions = data.dietary_restrictions
        if data.interests:
            self._profile.interests = data.interests
        return self.get_profile()

    def update_from_preferences(self, preferences: dict) -> None:
        if "travel_style" in preferences:
            self._profile.travel_style = preferences["travel_style"]
        if "budget" in preferences:
            self._profile.budget = preferences["budget"]
        if "preferred_destinations" in preferences:
            existing = set(self._profile.preferred_destinations)
            for dest in preferences["preferred_destinations"]:
                existing.add(dest)
            self._profile.preferred_destinations = list(existing)

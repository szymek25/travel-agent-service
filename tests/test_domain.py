"""Tests for UserPreferences domain model methods: merge(), to_dict(), from_dict()."""

from app.models.domain import UserPreferences


# ---------------------------------------------------------------------------
# UserPreferences.merge
# ---------------------------------------------------------------------------


class TestUserPreferencesMerge:
    # --- travel_style ---

    def test_other_travel_style_overrides_self(self) -> None:
        merged = UserPreferences(travel_style="beach").merge(
            UserPreferences(travel_style="adventure")
        )
        assert merged.travel_style == "adventure"

    def test_self_travel_style_preserved_when_other_is_none(self) -> None:
        merged = UserPreferences(travel_style="beach").merge(UserPreferences())
        assert merged.travel_style == "beach"

    def test_none_when_both_travel_styles_absent(self) -> None:
        merged = UserPreferences().merge(UserPreferences())
        assert merged.travel_style is None

    # --- budget ---

    def test_other_string_budget_overrides_self(self) -> None:
        merged = UserPreferences(budget="moderate").merge(UserPreferences(budget="luxury"))
        assert merged.budget == "luxury"

    def test_other_integer_budget_overrides_self(self) -> None:
        merged = UserPreferences(budget="moderate").merge(UserPreferences(budget=3000))
        assert merged.budget == 3000
        assert isinstance(merged.budget, int)

    def test_self_budget_preserved_when_other_is_none(self) -> None:
        merged = UserPreferences(budget=2000).merge(UserPreferences())
        assert merged.budget == 2000

    def test_none_when_both_budgets_absent(self) -> None:
        merged = UserPreferences().merge(UserPreferences())
        assert merged.budget is None

    # --- list fields ---

    def test_preferred_destinations_unioned(self) -> None:
        merged = UserPreferences(preferred_destinations=["Paris"]).merge(
            UserPreferences(preferred_destinations=["Tokyo"])
        )
        assert "Paris" in merged.preferred_destinations
        assert "Tokyo" in merged.preferred_destinations

    def test_dietary_restrictions_unioned(self) -> None:
        merged = UserPreferences(dietary_restrictions=["vegan"]).merge(
            UserPreferences(dietary_restrictions=["halal"])
        )
        assert "vegan" in merged.dietary_restrictions
        assert "halal" in merged.dietary_restrictions

    def test_interests_unioned(self) -> None:
        merged = UserPreferences(interests=["hiking"]).merge(
            UserPreferences(interests=["diving"])
        )
        assert "hiking" in merged.interests
        assert "diving" in merged.interests

    def test_all_list_fields_unioned_together(self) -> None:
        base = UserPreferences(
            preferred_destinations=["Paris"],
            dietary_restrictions=["vegetarian"],
            interests=["museums"],
        )
        other = UserPreferences(
            preferred_destinations=["Tokyo"],
            dietary_restrictions=["vegan"],
            interests=["hiking"],
        )
        merged = base.merge(other)
        assert set(merged.preferred_destinations) == {"Paris", "Tokyo"}
        assert set(merged.dietary_restrictions) == {"vegetarian", "vegan"}
        assert set(merged.interests) == {"museums", "hiking"}

    def test_duplicate_list_entries_deduplicated(self) -> None:
        merged = UserPreferences(interests=["hiking"]).merge(
            UserPreferences(interests=["hiking", "diving"])
        )
        assert merged.interests.count("hiking") == 1
        assert "diving" in merged.interests

    def test_empty_other_preserves_all_self_fields(self) -> None:
        base = UserPreferences(
            travel_style="beach",
            budget="luxury",
            preferred_destinations=["Bali"],
            dietary_restrictions=["vegan"],
            interests=["diving"],
        )
        merged = base.merge(UserPreferences())
        assert merged.travel_style == "beach"
        assert merged.budget == "luxury"
        assert "Bali" in merged.preferred_destinations
        assert "vegan" in merged.dietary_restrictions
        assert "diving" in merged.interests

    def test_empty_base_merged_with_full_other(self) -> None:
        other = UserPreferences(
            travel_style="cultural",
            budget=1500,
            preferred_destinations=["Kyoto"],
            dietary_restrictions=["halal"],
            interests=["art"],
        )
        merged = UserPreferences().merge(other)
        assert merged.travel_style == "cultural"
        assert merged.budget == 1500
        assert "Kyoto" in merged.preferred_destinations

    # --- immutability ---

    def test_returns_new_instance(self) -> None:
        base = UserPreferences(travel_style="beach")
        other = UserPreferences(travel_style="adventure")
        merged = base.merge(other)
        assert merged is not base
        assert merged is not other

    def test_original_instances_unchanged_after_merge(self) -> None:
        base = UserPreferences(travel_style="beach", preferred_destinations=["Paris"])
        other = UserPreferences(travel_style="adventure", preferred_destinations=["Tokyo"])
        base.merge(other)
        assert base.travel_style == "beach"
        assert base.preferred_destinations == ["Paris"]
        assert other.travel_style == "adventure"
        assert other.preferred_destinations == ["Tokyo"]


# ---------------------------------------------------------------------------
# UserPreferences.to_dict
# ---------------------------------------------------------------------------


class TestUserPreferencesToDict:
    def test_contains_all_five_keys(self) -> None:
        d = UserPreferences().to_dict()
        assert set(d.keys()) == {
            "travel_style",
            "budget",
            "preferred_destinations",
            "dietary_restrictions",
            "interests",
        }

    def test_none_scalars_present_as_none(self) -> None:
        d = UserPreferences().to_dict()
        assert d["travel_style"] is None
        assert d["budget"] is None

    def test_empty_lists_present_as_empty_lists(self) -> None:
        d = UserPreferences().to_dict()
        assert d["preferred_destinations"] == []
        assert d["dietary_restrictions"] == []
        assert d["interests"] == []

    def test_string_values_preserved(self) -> None:
        d = UserPreferences(travel_style="adventure", budget="moderate").to_dict()
        assert d["travel_style"] == "adventure"
        assert d["budget"] == "moderate"

    def test_integer_budget_preserved_with_type(self) -> None:
        d = UserPreferences(budget=2500).to_dict()
        assert d["budget"] == 2500
        assert isinstance(d["budget"], int)

    def test_list_values_preserved(self) -> None:
        d = UserPreferences(
            preferred_destinations=["Nepal", "Patagonia"],
            dietary_restrictions=["vegetarian"],
            interests=["trekking", "photography"],
        ).to_dict()
        assert d["preferred_destinations"] == ["Nepal", "Patagonia"]
        assert d["dietary_restrictions"] == ["vegetarian"]
        assert d["interests"] == ["trekking", "photography"]

    def test_full_preferences_roundtrip_type(self) -> None:
        prefs = UserPreferences(
            travel_style="ski",
            budget=4000,
            preferred_destinations=["Swiss Alps"],
            dietary_restrictions=[],
            interests=["après-ski", "snowboarding"],
        )
        d = prefs.to_dict()
        assert isinstance(d, dict)
        assert d["travel_style"] == "ski"
        assert d["budget"] == 4000


# ---------------------------------------------------------------------------
# UserPreferences.from_dict
# ---------------------------------------------------------------------------


class TestUserPreferencesFromDict:
    def test_full_dict_maps_all_fields(self) -> None:
        data = {
            "travel_style": "cultural",
            "budget": "mid-range",
            "preferred_destinations": ["Japan", "Italy"],
            "dietary_restrictions": ["halal"],
            "interests": ["art", "food"],
        }
        prefs = UserPreferences.from_dict(data)
        assert prefs.travel_style == "cultural"
        assert prefs.budget == "mid-range"
        assert prefs.preferred_destinations == ["Japan", "Italy"]
        assert prefs.dietary_restrictions == ["halal"]
        assert prefs.interests == ["art", "food"]

    def test_empty_dict_defaults_all_to_none_or_empty(self) -> None:
        prefs = UserPreferences.from_dict({})
        assert prefs.travel_style is None
        assert prefs.budget is None
        assert prefs.preferred_destinations == []
        assert prefs.dietary_restrictions == []
        assert prefs.interests == []

    def test_missing_scalar_keys_default_to_none(self) -> None:
        prefs = UserPreferences.from_dict({"budget": "luxury"})
        assert prefs.travel_style is None

    def test_missing_list_keys_default_to_empty(self) -> None:
        prefs = UserPreferences.from_dict({"travel_style": "beach"})
        assert prefs.preferred_destinations == []
        assert prefs.dietary_restrictions == []
        assert prefs.interests == []

    def test_explicit_none_list_value_defaults_to_empty(self) -> None:
        prefs = UserPreferences.from_dict({"preferred_destinations": None})
        assert prefs.preferred_destinations == []

    def test_explicit_none_scalar_preserved_as_none(self) -> None:
        prefs = UserPreferences.from_dict({"travel_style": None})
        assert prefs.travel_style is None

    def test_integer_budget_preserved(self) -> None:
        prefs = UserPreferences.from_dict({"budget": 3000})
        assert prefs.budget == 3000
        assert isinstance(prefs.budget, int)

    def test_extra_keys_ignored(self) -> None:
        prefs = UserPreferences.from_dict({"travel_style": "beach", "unknown_field": "ignored"})
        assert prefs.travel_style == "beach"

    def test_roundtrip_to_dict_and_back(self) -> None:
        original = UserPreferences(
            travel_style="adventure",
            budget=1500,
            preferred_destinations=["Nepal", "Patagonia"],
            dietary_restrictions=["vegetarian"],
            interests=["trekking"],
        )
        restored = UserPreferences.from_dict(original.to_dict())
        assert restored.travel_style == original.travel_style
        assert restored.budget == original.budget
        assert set(restored.preferred_destinations) == set(original.preferred_destinations)
        assert restored.dietary_restrictions == original.dietary_restrictions
        assert restored.interests == original.interests

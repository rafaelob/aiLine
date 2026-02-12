"""Tests for PydanticAIModelSelector (SmartRouter tier -> Model bridge)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from pydantic_ai.models import Model

from ailine_agents.model_selection.bridge import PydanticAIModelSelector


def _make_mock_model(name: str = "mock") -> Model:
    """Create a mock that passes isinstance checks for Model."""
    m = MagicMock(spec=Model)
    m.__str__ = lambda self: name
    return m


class TestPydanticAIModelSelector:
    """PydanticAIModelSelector maps tier names to Pydantic AI Model instances."""

    def test_construction_with_all_tiers(self) -> None:
        cheap = _make_mock_model("cheap")
        middle = _make_mock_model("middle")
        primary = _make_mock_model("primary")
        selector = PydanticAIModelSelector(cheap=cheap, middle=middle, primary=primary)
        assert selector.select_model(tier="cheap") is cheap
        assert selector.select_model(tier="middle") is middle
        assert selector.select_model(tier="primary") is primary

    def test_construction_primary_only(self) -> None:
        primary = _make_mock_model("primary")
        selector = PydanticAIModelSelector(primary=primary)
        assert selector.select_model(tier="primary") is primary

    def test_construction_cheap_only(self) -> None:
        cheap = _make_mock_model("cheap")
        selector = PydanticAIModelSelector(cheap=cheap)
        assert selector.select_model(tier="cheap") is cheap

    def test_no_tiers_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="At least one"):
            PydanticAIModelSelector()

    def test_fallback_to_primary(self) -> None:
        primary = _make_mock_model("primary")
        selector = PydanticAIModelSelector(primary=primary)
        # cheap/middle not set -> fallback to primary
        assert selector.select_model(tier="cheap") is primary
        assert selector.select_model(tier="middle") is primary

    def test_fallback_to_middle_when_no_primary(self) -> None:
        middle = _make_mock_model("middle")
        selector = PydanticAIModelSelector(middle=middle)
        assert selector.select_model(tier="primary") is middle
        assert selector.select_model(tier="cheap") is middle

    def test_fallback_to_cheap_when_no_others(self) -> None:
        cheap = _make_mock_model("cheap")
        selector = PydanticAIModelSelector(cheap=cheap)
        assert selector.select_model(tier="primary") is cheap
        assert selector.select_model(tier="middle") is cheap

    def test_unknown_tier_falls_back(self) -> None:
        primary = _make_mock_model("primary")
        selector = PydanticAIModelSelector(primary=primary)
        # Unknown tier key -> falls back
        assert selector.select_model(tier="nonexistent") is primary

    def test_select_model_default_tier_is_primary(self) -> None:
        primary = _make_mock_model("primary")
        cheap = _make_mock_model("cheap")
        selector = PydanticAIModelSelector(cheap=cheap, primary=primary)
        assert selector.select_model() is primary

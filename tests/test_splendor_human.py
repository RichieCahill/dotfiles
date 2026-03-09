"""Tests for python/splendor/human.py - non-TUI parts."""

from __future__ import annotations

from python.splendor.human import (
    COST_ABBR,
    COLOR_ABBR_TO_FULL,
    COLOR_STYLE,
    color_token,
    fmt_gem,
    fmt_number,
    format_card,
    format_cost,
    format_discounts,
    format_noble,
    format_tokens,
    parse_color_token,
)
from python.splendor.base import Card, GEM_COLORS, Noble

import pytest


# --- parse_color_token ---


def test_parse_color_token_full_names() -> None:
    """Test parsing full color names."""
    assert parse_color_token("white") == "white"
    assert parse_color_token("blue") == "blue"
    assert parse_color_token("green") == "green"
    assert parse_color_token("red") == "red"
    assert parse_color_token("black") == "black"


def test_parse_color_token_abbreviations() -> None:
    """Test parsing abbreviated color names."""
    assert parse_color_token("w") == "white"
    assert parse_color_token("b") == "blue"
    assert parse_color_token("g") == "green"
    assert parse_color_token("r") == "red"
    assert parse_color_token("k") == "black"
    assert parse_color_token("o") == "gold"


def test_parse_color_token_case_insensitive() -> None:
    """Test parsing is case insensitive."""
    assert parse_color_token("WHITE") == "white"
    assert parse_color_token("B") == "blue"


def test_parse_color_token_unknown() -> None:
    """Test parsing unknown color raises."""
    with pytest.raises(ValueError, match="Unknown color"):
        parse_color_token("purple")


# --- format functions ---


def test_format_cost() -> None:
    """Test format_cost formats correctly."""
    cost = {"white": 2, "blue": 1, "green": 0, "red": 0, "black": 0, "gold": 0}
    result = format_cost(cost)
    assert "W:" in result
    assert "B:" in result


def test_format_cost_empty() -> None:
    """Test format_cost with all zeros."""
    cost = dict.fromkeys(GEM_COLORS, 0)
    result = format_cost(cost)
    assert result == "-"


def test_format_card() -> None:
    """Test format_card."""
    card = Card(tier=1, points=2, color="white", cost={"white": 0, "blue": 1, "green": 0, "red": 0, "black": 0, "gold": 0})
    result = format_card(card)
    assert "T1" in result
    assert "P2" in result


def test_format_noble() -> None:
    """Test format_noble."""
    noble = Noble(name="Noble 1", points=3, requirements={"white": 3, "blue": 3, "green": 3})
    result = format_noble(noble)
    assert "Noble 1" in result
    assert "+3" in result


def test_format_tokens() -> None:
    """Test format_tokens."""
    tokens = {"white": 2, "blue": 1, "green": 0, "red": 0, "black": 0, "gold": 0}
    result = format_tokens(tokens)
    assert "white:" in result


def test_format_discounts() -> None:
    """Test format_discounts."""
    discounts = {"white": 2, "blue": 1, "green": 0, "red": 0, "black": 0, "gold": 0}
    result = format_discounts(discounts)
    assert "W:" in result


def test_format_discounts_empty() -> None:
    """Test format_discounts with all zeros."""
    discounts = dict.fromkeys(GEM_COLORS, 0)
    result = format_discounts(discounts)
    assert result == "-"


# --- formatting helpers ---


def test_color_token() -> None:
    """Test color_token."""
    result = color_token("white", 3)
    assert "white" in result
    assert "3" in result


def test_fmt_gem() -> None:
    """Test fmt_gem."""
    result = fmt_gem("blue")
    assert "blue" in result


def test_fmt_number() -> None:
    """Test fmt_number."""
    result = fmt_number(42)
    assert "42" in result


# --- constants ---


def test_cost_abbr_all_colors() -> None:
    """Test COST_ABBR has all gem colors."""
    for color in GEM_COLORS:
        assert color in COST_ABBR


def test_color_abbr_to_full() -> None:
    """Test COLOR_ABBR_TO_FULL mappings."""
    assert COLOR_ABBR_TO_FULL["w"] == "white"
    assert COLOR_ABBR_TO_FULL["o"] == "gold"


def test_color_style_all_colors() -> None:
    """Test COLOR_STYLE has all gem colors."""
    for color in GEM_COLORS:
        assert color in COLOR_STYLE
        fg, bg = COLOR_STYLE[color]
        assert isinstance(fg, str)
        assert isinstance(bg, str)

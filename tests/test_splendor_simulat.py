"""Tests for python/splendor/simulat.py."""

from __future__ import annotations

import json
import random
from pathlib import Path
from unittest.mock import patch

from python.splendor.base import load_cards, load_nobles
from python.splendor.simulat import main


def test_simulat_main(tmp_path: Path) -> None:
    """Test simulat main function with mock game data."""
    random.seed(42)

    # Create temporary game data
    cards_dir = tmp_path / "game_data" / "cards"
    nobles_dir = tmp_path / "game_data" / "nobles"
    cards_dir.mkdir(parents=True)
    nobles_dir.mkdir(parents=True)

    cards = []
    for tier in (1, 2, 3):
        for color in ("white", "blue", "green", "red", "black"):
            cards.append({
                "tier": tier,
                "points": tier,
                "color": color,
                "cost": {"white": tier, "blue": 0, "green": 0, "red": 0, "black": 0, "gold": 0},
            })
    (cards_dir / "default.json").write_text(json.dumps(cards))

    nobles = [
        {"name": f"Noble {i}", "points": 3, "requirements": {"white": 3, "blue": 3, "green": 3}}
        for i in range(5)
    ]
    (nobles_dir / "default.json").write_text(json.dumps(nobles))

    # Patch Path(__file__).parent to point to tmp_path
    fake_parent = tmp_path
    with patch("python.splendor.simulat.Path") as mock_path_cls:
        mock_path_cls.return_value.__truediv__ = Path.__truediv__
        mock_file = mock_path_cls().__truediv__("simulat.py")
        # Make Path(__file__).parent return tmp_path
        mock_path_cls.reset_mock()
        mock_path_instance = mock_path_cls.return_value
        mock_path_instance.parent = fake_parent

        # Actually just patch load_cards and load_nobles
    cards_data = load_cards(cards_dir / "default.json")
    nobles_data = load_nobles(nobles_dir / "default.json")

    with (
        patch("python.splendor.simulat.load_cards", return_value=cards_data),
        patch("python.splendor.simulat.load_nobles", return_value=nobles_data),
    ):
        main()


def test_load_cards_and_nobles(tmp_path: Path) -> None:
    """Test that load_cards and load_nobles work correctly."""
    cards_dir = tmp_path / "cards"
    cards_dir.mkdir()

    cards = [
        {
            "tier": 1,
            "points": 0,
            "color": "white",
            "cost": {"white": 1, "blue": 0, "green": 0, "red": 0, "black": 0, "gold": 0},
        }
    ]
    cards_file = cards_dir / "default.json"
    cards_file.write_text(json.dumps(cards))
    loaded = load_cards(cards_file)
    assert len(loaded) == 1
    assert loaded[0].color == "white"

    nobles_dir = tmp_path / "nobles"
    nobles_dir.mkdir()
    nobles = [{"name": "Noble A", "points": 3, "requirements": {"white": 3}}]
    nobles_file = nobles_dir / "default.json"
    nobles_file.write_text(json.dumps(nobles))
    loaded_nobles = load_nobles(nobles_file)
    assert len(loaded_nobles) == 1
    assert loaded_nobles[0].name == "Noble A"

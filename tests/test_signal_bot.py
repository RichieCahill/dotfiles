"""Tests for the Signal command and control bot."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from python.signal_bot.commands.inventory import (
    _format_summary,
    _merge_items,
    load_inventory,
    parse_llm_response,
    save_inventory,
)
from python.signal_bot.device_registry import DeviceRegistry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.main import dispatch
from python.signal_bot.models import (
    InventoryItem,
    LLMConfig,
    SignalMessage,
    TrustLevel,
)
from python.signal_bot.signal_client import SignalClient


class TestModels:
    def test_llm_config_base_url(self):
        config = LLMConfig(model="test:7b", host="bob.local", port=11434)
        assert config.base_url == "http://bob.local:11434"

    def test_trust_level_values(self):
        assert TrustLevel.VERIFIED == "verified"
        assert TrustLevel.UNVERIFIED == "unverified"
        assert TrustLevel.BLOCKED == "blocked"

    def test_signal_message_defaults(self):
        msg = SignalMessage(source="+1234", timestamp=0)
        assert msg.message == ""
        assert msg.attachments == []
        assert msg.group_id is None

    def test_inventory_item_defaults(self):
        item = InventoryItem(name="wrench")
        assert item.quantity == 1
        assert item.category == ""


class TestInventoryParsing:
    def test_parse_llm_response_basic(self):
        raw = '[{"name": "water", "quantity": 6, "category": "supplies", "notes": ""}]'
        items = parse_llm_response(raw)
        assert len(items) == 1
        assert items[0].name == "water"
        assert items[0].quantity == 6

    def test_parse_llm_response_with_code_fence(self):
        raw = '```json\n[{"name": "tape", "quantity": 1, "category": "tools", "notes": ""}]\n```'
        items = parse_llm_response(raw)
        assert len(items) == 1
        assert items[0].name == "tape"

    def test_parse_llm_response_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_response("not json at all")

    def test_merge_items_new(self):
        existing = [InventoryItem(name="tape", quantity=2, category="tools")]
        new = [InventoryItem(name="rope", quantity=1, category="supplies")]
        merged = _merge_items(existing, new)
        assert len(merged) == 2

    def test_merge_items_duplicate_sums_quantity(self):
        existing = [InventoryItem(name="tape", quantity=2, category="tools")]
        new = [InventoryItem(name="tape", quantity=3, category="tools")]
        merged = _merge_items(existing, new)
        assert len(merged) == 1
        assert merged[0].quantity == 5

    def test_merge_items_case_insensitive(self):
        existing = [InventoryItem(name="Tape", quantity=1)]
        new = [InventoryItem(name="tape", quantity=2)]
        merged = _merge_items(existing, new)
        assert len(merged) == 1
        assert merged[0].quantity == 3

    def test_format_summary(self):
        items = [InventoryItem(name="water", quantity=6, category="supplies")]
        summary = _format_summary(items)
        assert "water" in summary
        assert "x6" in summary

    def test_save_and_load_inventory(self, tmp_path):
        path = tmp_path / "inventory.json"
        items = [InventoryItem(name="wrench", quantity=1, category="tools")]
        save_inventory(path, items)
        loaded = load_inventory(path)
        assert len(loaded) == 1
        assert loaded[0].name == "wrench"

    def test_load_inventory_missing_file(self, tmp_path):
        path = tmp_path / "does_not_exist.json"
        assert load_inventory(path) == []


class TestDeviceRegistry:
    @pytest.fixture
    def signal_mock(self):
        return MagicMock(spec=SignalClient)

    @pytest.fixture
    def registry(self, tmp_path, signal_mock):
        return DeviceRegistry(signal_mock, tmp_path / "devices.json")

    def test_new_device_is_unverified(self, registry):
        registry.record_contact("+1234", "abc123")
        assert not registry.is_verified("+1234")

    def test_verify_device(self, registry):
        registry.record_contact("+1234", "abc123")
        assert registry.verify("+1234")
        assert registry.is_verified("+1234")

    def test_verify_unknown_device(self, registry):
        assert not registry.verify("+9999")

    def test_block_device(self, registry):
        registry.record_contact("+1234", "abc123")
        registry.block("+1234")
        assert registry.is_blocked("+1234")

    def test_safety_number_change_resets_trust(self, registry):
        registry.record_contact("+1234", "abc123")
        registry.verify("+1234")
        assert registry.is_verified("+1234")
        registry.record_contact("+1234", "different_safety_number")
        assert not registry.is_verified("+1234")

    def test_persistence(self, tmp_path, signal_mock):
        path = tmp_path / "devices.json"
        reg1 = DeviceRegistry(signal_mock, path)
        reg1.record_contact("+1234", "abc123")
        reg1.verify("+1234")

        reg2 = DeviceRegistry(signal_mock, path)
        assert reg2.is_verified("+1234")

    def test_list_devices(self, registry):
        registry.record_contact("+1234", "abc")
        registry.record_contact("+5678", "def")
        assert len(registry.list_devices()) == 2


class TestDispatch:
    @pytest.fixture
    def signal_mock(self):
        return MagicMock(spec=SignalClient)

    @pytest.fixture
    def llm_mock(self):
        return MagicMock(spec=LLMClient)

    @pytest.fixture
    def registry_mock(self):
        mock = MagicMock(spec=DeviceRegistry)
        mock.is_blocked.return_value = False
        mock.is_verified.return_value = True
        return mock

    def test_blocked_device_ignored(self, signal_mock, llm_mock, registry_mock, tmp_path):
        registry_mock.is_blocked.return_value = True
        msg = SignalMessage(source="+1234", timestamp=0, message="!help")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_not_called()

    def test_unverified_device_gets_warning(self, signal_mock, llm_mock, registry_mock, tmp_path):
        registry_mock.is_verified.return_value = False
        msg = SignalMessage(source="+1234", timestamp=0, message="!help")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_called_once()
        assert "not verified" in signal_mock.reply.call_args[0][1]

    def test_help_command(self, signal_mock, llm_mock, registry_mock, tmp_path):
        msg = SignalMessage(source="+1234", timestamp=0, message="!help")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_called_once()
        assert "Available commands" in signal_mock.reply.call_args[0][1]

    def test_unknown_command(self, signal_mock, llm_mock, registry_mock, tmp_path):
        msg = SignalMessage(source="+1234", timestamp=0, message="!foobar")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_called_once()
        assert "Unknown command" in signal_mock.reply.call_args[0][1]

    def test_non_command_message_ignored(self, signal_mock, llm_mock, registry_mock, tmp_path):
        msg = SignalMessage(source="+1234", timestamp=0, message="hello there")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_not_called()

    def test_status_command(self, signal_mock, llm_mock, registry_mock, tmp_path):
        llm_mock.list_models.return_value = ["model1", "model2"]
        llm_mock.config = LLMConfig(model="test:7b", host="bob")
        registry_mock.list_devices.return_value = []
        msg = SignalMessage(source="+1234", timestamp=0, message="!status")
        dispatch(msg, signal_mock, llm_mock, registry_mock, tmp_path / "inv.json")
        signal_mock.reply.assert_called_once()
        assert "Bot online" in signal_mock.reply.call_args[0][1]

"""Tests for the Signal command and control bot."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine

from python.orm.richie.base import RichieBase
from python.signal_bot.commands.inventory import (
    _format_summary,
    parse_llm_response,
)
from python.signal_bot.device_registry import DeviceRegistry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.main import dispatch
from python.signal_bot.models import (
    BotConfig,
    InventoryItem,
    SignalMessage,
    TrustLevel,
)
from python.signal_bot.signal_client import SignalClient


class TestModels:
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
        assert item.unit == "each"
        assert item.category == ""


class TestInventoryParsing:
    def test_parse_llm_response_basic(self):
        raw = '[{"name": "water", "quantity": 6, "unit": "gallon", "category": "supplies", "notes": ""}]'
        items = parse_llm_response(raw)
        assert len(items) == 1
        assert items[0].name == "water"
        assert items[0].quantity == 6
        assert items[0].unit == "gallon"

    def test_parse_llm_response_with_code_fence(self):
        raw = '```json\n[{"name": "tape", "quantity": 1, "unit": "each", "category": "tools", "notes": ""}]\n```'
        items = parse_llm_response(raw)
        assert len(items) == 1
        assert items[0].name == "tape"

    def test_parse_llm_response_invalid_json(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_response("not json at all")

    def test_format_summary(self):
        items = [InventoryItem(name="water", quantity=6, unit="gallon", category="supplies")]
        summary = _format_summary(items)
        assert "water" in summary
        assert "x6" in summary
        assert "gallon" in summary


class TestDeviceRegistry:
    @pytest.fixture
    def signal_mock(self):
        return MagicMock(spec=SignalClient)

    @pytest.fixture
    def engine(self):
        engine = create_engine("sqlite://")
        RichieBase.metadata.create_all(engine)
        return engine

    @pytest.fixture
    def registry(self, signal_mock, engine):
        return DeviceRegistry(signal_mock, engine)

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
        assert registry.block("+1234")
        assert not registry.is_verified("+1234")

    def test_safety_number_change_resets_trust(self, registry):
        registry.record_contact("+1234", "abc123")
        registry.verify("+1234")
        assert registry.is_verified("+1234")
        registry.record_contact("+1234", "different_safety_number")
        assert not registry.is_verified("+1234")

    def test_persistence(self, signal_mock, engine):
        reg1 = DeviceRegistry(signal_mock, engine)
        reg1.record_contact("+1234", "abc123")
        reg1.verify("+1234")

        reg2 = DeviceRegistry(signal_mock, engine)
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
        mock.is_verified.return_value = True
        mock.has_safety_number.return_value = True
        return mock

    @pytest.fixture
    def config(self):
        return BotConfig(
            signal_api_url="http://localhost:8080",
            phone_number="+1234567890",
            inventory_api_url="http://localhost:9090",
        )

    def test_unverified_device_ignored(self, signal_mock, llm_mock, registry_mock, config):
        registry_mock.is_verified.return_value = False
        msg = SignalMessage(source="+1234", timestamp=0, message="!help")
        dispatch(msg, signal_mock, llm_mock, registry_mock, config)
        signal_mock.reply.assert_not_called()

    def test_help_command(self, signal_mock, llm_mock, registry_mock, config):
        msg = SignalMessage(source="+1234", timestamp=0, message="!help")
        dispatch(msg, signal_mock, llm_mock, registry_mock, config)
        signal_mock.reply.assert_called_once()
        assert "Available commands" in signal_mock.reply.call_args[0][1]

    def test_unknown_command(self, signal_mock, llm_mock, registry_mock, config):
        msg = SignalMessage(source="+1234", timestamp=0, message="!foobar")
        dispatch(msg, signal_mock, llm_mock, registry_mock, config)
        signal_mock.reply.assert_called_once()
        assert "Unknown command" in signal_mock.reply.call_args[0][1]

    def test_non_command_message_ignored(self, signal_mock, llm_mock, registry_mock, config):
        msg = SignalMessage(source="+1234", timestamp=0, message="hello there")
        dispatch(msg, signal_mock, llm_mock, registry_mock, config)
        signal_mock.reply.assert_not_called()

    def test_status_command(self, signal_mock, llm_mock, registry_mock, config):
        llm_mock.list_models.return_value = ["model1", "model2"]
        llm_mock.model = "test:7b"
        registry_mock.list_devices.return_value = []
        msg = SignalMessage(source="+1234", timestamp=0, message="!status")
        dispatch(msg, signal_mock, llm_mock, registry_mock, config)
        signal_mock.reply.assert_called_once()
        assert "Bot online" in signal_mock.reply.call_args[0][1]

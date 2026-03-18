"""Tests for the Signal command and control bot."""

from __future__ import annotations

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from python.signal_bot.commands.inventory import (
    _format_summary,
    parse_llm_response,
)
from python.signal_bot.commands.location import _format_location, handle_location_request
from python.signal_bot.device_registry import _BLOCKED_TTL, _DEFAULT_TTL, DeviceRegistry, _CacheEntry
from python.signal_bot.llm_client import LLMClient
from python.signal_bot.main import Bot
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


class TestContactCache:
    @pytest.fixture
    def signal_mock(self):
        return MagicMock(spec=SignalClient)

    @pytest.fixture
    def registry(self, signal_mock, engine):
        return DeviceRegistry(signal_mock, engine)

    def test_second_call_uses_cache(self, registry):
        registry.record_contact("+1234", "abc")
        assert "+1234" in registry._contact_cache

        with patch.object(registry, "engine") as mock_engine:
            registry.record_contact("+1234", "abc")
            mock_engine.assert_not_called()

    def test_unverified_gets_default_ttl(self, registry):
        registry.record_contact("+1234", "abc")
        from python.common import utcnow

        entry = registry._contact_cache["+1234"]
        expected = utcnow() + _DEFAULT_TTL
        assert abs((entry.expires - expected).total_seconds()) < 2
        assert entry.trust_level == TrustLevel.UNVERIFIED
        assert entry.has_safety_number is True

    def test_blocked_gets_blocked_ttl(self, registry):
        registry.record_contact("+1234", "abc")
        registry.block("+1234")
        from python.common import utcnow

        entry = registry._contact_cache["+1234"]
        expected = utcnow() + _BLOCKED_TTL
        assert abs((entry.expires - expected).total_seconds()) < 2
        assert entry.trust_level == TrustLevel.BLOCKED

    def test_verify_updates_cache(self, registry):
        registry.record_contact("+1234", "abc")
        registry.verify("+1234")
        entry = registry._contact_cache["+1234"]
        assert entry.trust_level == TrustLevel.VERIFIED

    def test_block_updates_cache(self, registry):
        registry.record_contact("+1234", "abc")
        registry.block("+1234")
        entry = registry._contact_cache["+1234"]
        assert entry.trust_level == TrustLevel.BLOCKED

    def test_unverify_updates_cache(self, registry):
        registry.record_contact("+1234", "abc")
        registry.verify("+1234")
        registry.unverify("+1234")
        entry = registry._contact_cache["+1234"]
        assert entry.trust_level == TrustLevel.UNVERIFIED

    def test_is_verified_uses_cache(self, registry):
        registry.record_contact("+1234", "abc")
        registry.verify("+1234")
        with patch.object(registry, "engine") as mock_engine:
            assert registry.is_verified("+1234") is True
            mock_engine.assert_not_called()

    def test_has_safety_number_uses_cache(self, registry):
        registry.record_contact("+1234", "abc")
        with patch.object(registry, "engine") as mock_engine:
            assert registry.has_safety_number("+1234") is True
            mock_engine.assert_not_called()

    def test_no_safety_number_cached(self, registry):
        registry.record_contact("+1234", None)
        with patch.object(registry, "engine") as mock_engine:
            assert registry.has_safety_number("+1234") is False
            mock_engine.assert_not_called()

    def test_expired_cache_hits_db(self, registry):
        registry.record_contact("+1234", "abc")
        old = registry._contact_cache["+1234"]
        registry._contact_cache["+1234"] = _CacheEntry(
            expires=old.expires - timedelta(minutes=10),
            trust_level=old.trust_level,
            has_safety_number=old.has_safety_number,
            safety_number=old.safety_number,
            roles=old.roles,
        )

        with patch("python.signal_bot.device_registry.Session") as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value.__enter__ = MagicMock(return_value=mock_session)
            mock_session_cls.return_value.__exit__ = MagicMock(return_value=False)
            mock_device = MagicMock()
            mock_device.trust_level = TrustLevel.UNVERIFIED
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_device
            registry.record_contact("+1234", "abc")
            mock_session.execute.assert_called_once()


class TestLocationCommand:
    def test_format_location(self):
        response = _format_location("12.34", "56.78")
        assert "12.34, 56.78" in response
        assert "maps.google.com" in response

    def test_handle_location_request_without_config(self):
        signal = MagicMock(spec=SignalClient)
        message = SignalMessage(source="+1234", timestamp=0, message="location")
        handle_location_request(message, signal, None, None)
        signal.reply.assert_called_once()
        assert "not configured" in signal.reply.call_args[0][1]


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
        mock.has_role.return_value = False
        mock.get_roles.return_value = []
        return mock

    @pytest.fixture
    def config(self, engine):
        return BotConfig(
            signal_api_url="http://localhost:8080",
            phone_number="+1234567890",
            inventory_api_url="http://localhost:9090",
            engine=engine,
        )

    @pytest.fixture
    def bot(self, signal_mock, llm_mock, registry_mock, config):
        return Bot(signal_mock, llm_mock, registry_mock, config)

    def test_unverified_device_ignored(self, bot, signal_mock, registry_mock):
        registry_mock.is_verified.return_value = False
        msg = SignalMessage(source="+1234", timestamp=0, message="help")
        bot.dispatch(msg)
        signal_mock.reply.assert_not_called()

    def test_admin_without_safety_number_ignored(self, bot, signal_mock, registry_mock):
        registry_mock.has_safety_number.return_value = False
        registry_mock.has_role.return_value = True
        msg = SignalMessage(source="+1234", timestamp=0, message="help")
        bot.dispatch(msg)
        signal_mock.reply.assert_not_called()

    def test_non_admin_without_safety_number_allowed(self, bot, signal_mock, registry_mock):
        registry_mock.has_safety_number.return_value = False
        registry_mock.has_role.return_value = False
        registry_mock.get_roles.return_value = []
        msg = SignalMessage(source="+1234", timestamp=0, message="help")
        bot.dispatch(msg)
        signal_mock.reply.assert_called_once()

    def test_help_command(self, bot, signal_mock, registry_mock):
        msg = SignalMessage(source="+1234", timestamp=0, message="help")
        bot.dispatch(msg)
        signal_mock.reply.assert_called_once()
        assert "Available commands" in signal_mock.reply.call_args[0][1]

    def test_unknown_command_ignored(self, bot, signal_mock):
        msg = SignalMessage(source="+1234", timestamp=0, message="foobar")
        bot.dispatch(msg)
        signal_mock.reply.assert_not_called()

    def test_non_command_message_ignored(self, bot, signal_mock):
        msg = SignalMessage(source="+1234", timestamp=0, message="hello there")
        bot.dispatch(msg)
        signal_mock.reply.assert_not_called()

    def test_status_command(self, bot, signal_mock, llm_mock, registry_mock):
        llm_mock.list_models.return_value = ["model1", "model2"]
        llm_mock.model = "test:7b"
        registry_mock.list_devices.return_value = []
        registry_mock.has_role.return_value = True
        msg = SignalMessage(source="+1234", timestamp=0, message="status")
        bot.dispatch(msg)
        signal_mock.reply.assert_called_once()
        assert "Bot online" in signal_mock.reply.call_args[0][1]

    def test_location_command(self, bot, signal_mock, registry_mock, config):
        registry_mock.has_role.return_value = True
        msg = SignalMessage(source="+1234", timestamp=0, message="location")
        with patch("python.signal_bot.main.handle_location_request") as mock_location:
            bot.dispatch(msg)

        mock_location.assert_called_once_with(
            msg,
            signal_mock,
            config.ha_url,
            config.ha_token,
        )

"""Tests for python/orm modules."""

from __future__ import annotations

from os import environ
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from python.orm.base import RichieBase, TableBase, get_connection_info, get_postgres_engine
from python.orm.contact import ContactNeed, ContactRelationship, RelationshipType

if TYPE_CHECKING:
    pass


def test_richie_base_schema_name() -> None:
    """Test RichieBase has correct schema name."""
    assert RichieBase.schema_name == "main"


def test_richie_base_metadata_naming() -> None:
    """Test RichieBase metadata has naming conventions."""
    assert RichieBase.metadata.schema == "main"
    naming = RichieBase.metadata.naming_convention
    assert naming is not None
    assert "ix" in naming
    assert "uq" in naming
    assert "ck" in naming
    assert "fk" in naming
    assert "pk" in naming


def test_table_base_abstract() -> None:
    """Test TableBase is abstract."""
    assert TableBase.__abstract__ is True


def test_get_connection_info_success() -> None:
    """Test get_connection_info with all env vars set."""
    env = {
        "POSTGRES_DB": "testdb",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
    }
    with patch.dict(environ, env, clear=False):
        result = get_connection_info()
        assert result == ("testdb", "localhost", "5432", "testuser", "testpass")


def test_get_connection_info_no_password() -> None:
    """Test get_connection_info with no password."""
    env = {
        "POSTGRES_DB": "testdb",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "testuser",
    }
    # Clear password if set
    cleaned = {k: v for k, v in environ.items() if k != "POSTGRES_PASSWORD"}
    cleaned.update(env)
    with patch.dict(environ, cleaned, clear=True):
        result = get_connection_info()
        assert result == ("testdb", "localhost", "5432", "testuser", None)


def test_get_connection_info_missing_vars() -> None:
    """Test get_connection_info raises with missing env vars."""
    with patch.dict(environ, {}, clear=True), pytest.raises(ValueError, match="Missing environment variables"):
        get_connection_info()


def test_get_postgres_engine() -> None:
    """Test get_postgres_engine creates an engine."""
    env = {
        "POSTGRES_DB": "testdb",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432",
        "POSTGRES_USER": "testuser",
        "POSTGRES_PASSWORD": "testpass",
    }
    mock_engine = MagicMock()
    with patch.dict(environ, env, clear=False), patch("python.orm.base.create_engine", return_value=mock_engine):
        engine = get_postgres_engine()
        assert engine is mock_engine


# --- Contact ORM tests ---


def test_relationship_type_values() -> None:
    """Test RelationshipType enum values."""
    assert RelationshipType.SPOUSE.value == "spouse"
    assert RelationshipType.OTHER.value == "other"


def test_relationship_type_default_weight() -> None:
    """Test RelationshipType default weights."""
    assert RelationshipType.SPOUSE.default_weight == 10
    assert RelationshipType.ACQUAINTANCE.default_weight == 3
    assert RelationshipType.OTHER.default_weight == 2
    assert RelationshipType.PARENT.default_weight == 9


def test_relationship_type_display_name() -> None:
    """Test RelationshipType display_name."""
    assert RelationshipType.BEST_FRIEND.display_name == "Best Friend"
    assert RelationshipType.AUNT_UNCLE.display_name == "Aunt Uncle"
    assert RelationshipType.SPOUSE.display_name == "Spouse"


def test_all_relationship_types_have_weights() -> None:
    """Test all relationship types have valid weights."""
    for rt in RelationshipType:
        weight = rt.default_weight
        assert 1 <= weight <= 10


def test_contact_need_table_name() -> None:
    """Test ContactNeed table name."""
    assert ContactNeed.__tablename__ == "contact_need"


def test_contact_relationship_table_name() -> None:
    """Test ContactRelationship table name."""
    assert ContactRelationship.__tablename__ == "contact_relationship"

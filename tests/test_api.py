"""Tests for python/api modules."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from python.api.routers.contact import (
    ContactBase,
    ContactCreate,
    ContactListResponse,
    ContactRelationshipCreate,
    ContactRelationshipResponse,
    ContactRelationshipUpdate,
    ContactUpdate,
    GraphData,
    GraphEdge,
    GraphNode,
    NeedBase,
    NeedCreate,
    NeedResponse,
    RelationshipTypeInfo,
    router,
)
from python.api.routers.frontend import create_frontend_router
from python.orm.contact import RelationshipType


# --- Pydantic schema tests ---


def test_need_base() -> None:
    """Test NeedBase schema."""
    need = NeedBase(name="ADHD", description="Attention deficit")
    assert need.name == "ADHD"


def test_need_create() -> None:
    """Test NeedCreate schema."""
    need = NeedCreate(name="Light Sensitive")
    assert need.name == "Light Sensitive"
    assert need.description is None


def test_need_response() -> None:
    """Test NeedResponse schema."""
    need = NeedResponse(id=1, name="ADHD", description="test")
    assert need.id == 1


def test_contact_base() -> None:
    """Test ContactBase schema."""
    contact = ContactBase(name="John")
    assert contact.name == "John"
    assert contact.age is None
    assert contact.bio is None


def test_contact_create() -> None:
    """Test ContactCreate schema."""
    contact = ContactCreate(name="John", need_ids=[1, 2])
    assert contact.need_ids == [1, 2]


def test_contact_create_no_needs() -> None:
    """Test ContactCreate with no needs."""
    contact = ContactCreate(name="John")
    assert contact.need_ids == []


def test_contact_update() -> None:
    """Test ContactUpdate schema."""
    update = ContactUpdate(name="Jane", age=30)
    assert update.name == "Jane"
    assert update.age == 30


def test_contact_update_partial() -> None:
    """Test ContactUpdate with partial data."""
    update = ContactUpdate(age=25)
    assert update.name is None
    assert update.age == 25


def test_contact_list_response() -> None:
    """Test ContactListResponse schema."""
    contact = ContactListResponse(id=1, name="John")
    assert contact.id == 1


def test_contact_relationship_create() -> None:
    """Test ContactRelationshipCreate schema."""
    rel = ContactRelationshipCreate(
        related_contact_id=2,
        relationship_type=RelationshipType.FRIEND,
    )
    assert rel.related_contact_id == 2
    assert rel.closeness_weight is None


def test_contact_relationship_create_with_weight() -> None:
    """Test ContactRelationshipCreate with custom weight."""
    rel = ContactRelationshipCreate(
        related_contact_id=2,
        relationship_type=RelationshipType.SPOUSE,
        closeness_weight=10,
    )
    assert rel.closeness_weight == 10


def test_contact_relationship_update() -> None:
    """Test ContactRelationshipUpdate schema."""
    update = ContactRelationshipUpdate(closeness_weight=8)
    assert update.relationship_type is None
    assert update.closeness_weight == 8


def test_contact_relationship_response() -> None:
    """Test ContactRelationshipResponse schema."""
    resp = ContactRelationshipResponse(
        contact_id=1,
        related_contact_id=2,
        relationship_type="friend",
        closeness_weight=6,
    )
    assert resp.contact_id == 1


def test_relationship_type_info() -> None:
    """Test RelationshipTypeInfo schema."""
    info = RelationshipTypeInfo(value="spouse", display_name="Spouse", default_weight=10)
    assert info.value == "spouse"


def test_graph_node() -> None:
    """Test GraphNode schema."""
    node = GraphNode(id=1, name="John", current_job="Dev")
    assert node.id == 1


def test_graph_edge() -> None:
    """Test GraphEdge schema."""
    edge = GraphEdge(source=1, target=2, relationship_type="friend", closeness_weight=6)
    assert edge.source == 1


def test_graph_data() -> None:
    """Test GraphData schema."""
    data = GraphData(
        nodes=[GraphNode(id=1, name="John")],
        edges=[GraphEdge(source=1, target=2, relationship_type="friend", closeness_weight=6)],
    )
    assert len(data.nodes) == 1
    assert len(data.edges) == 1


# --- frontend router test ---


def test_create_frontend_router(tmp_path: Path) -> None:
    """Test create_frontend_router creates router."""
    # Create required assets dir and index.html
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    index = tmp_path / "index.html"
    index.write_text("<html></html>")

    router = create_frontend_router(tmp_path)
    assert router is not None


# --- API main tests ---


def test_create_app() -> None:
    """Test create_app creates FastAPI app."""
    with patch("python.api.main.get_postgres_engine"):
        from python.api.main import create_app

        app = create_app()
        assert app is not None
        assert app.title == "Contact Database API"


def test_create_app_with_frontend(tmp_path: Path) -> None:
    """Test create_app with frontend directory."""
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    index = tmp_path / "index.html"
    index.write_text("<html></html>")

    with patch("python.api.main.get_postgres_engine"):
        from python.api.main import create_app

        app = create_app(frontend_dir=tmp_path)
        assert app is not None


def test_build_frontend_none() -> None:
    """Test build_frontend with None returns None."""
    from python.api.main import build_frontend

    result = build_frontend(None)
    assert result is None


def test_build_frontend_missing_dir() -> None:
    """Test build_frontend with missing directory raises."""
    from python.api.main import build_frontend

    with pytest.raises(FileExistsError):
        build_frontend(Path("/nonexistent/path"))


# --- dependencies test ---


def test_db_session_dependency() -> None:
    """Test get_db dependency."""
    from python.api.dependencies import get_db

    mock_engine = create_engine("sqlite:///:memory:")
    mock_request = MagicMock()
    mock_request.app.state.engine = mock_engine

    gen = get_db(mock_request)
    session = next(gen)
    assert isinstance(session, Session)
    try:
        next(gen)
    except StopIteration:
        pass

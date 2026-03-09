"""Integration tests for API router using SQLite in-memory database."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from python.api.routers.contact import (
    ContactCreate,
    ContactRelationshipCreate,
    ContactRelationshipUpdate,
    ContactUpdate,
    NeedCreate,
    add_contact_relationship,
    add_need_to_contact,
    create_contact,
    create_need,
    delete_contact,
    delete_need,
    get_contact,
    get_contact_relationships,
    get_need,
    get_relationship_graph,
    list_contacts,
    list_needs,
    list_relationship_types,
    RelationshipTypeInfo,
    remove_contact_relationship,
    remove_need_from_contact,
    update_contact,
    update_contact_relationship,
)
from python.orm.base import RichieBase
from python.orm.contact import Contact, ContactNeed, ContactRelationship, Need, RelationshipType

import pytest


def _create_db() -> Session:
    """Create in-memory SQLite database with schema."""
    engine = create_engine("sqlite:///:memory:")
    # Create tables without schema prefix for SQLite
    RichieBase.metadata.create_all(engine, checkfirst=True)
    return Session(engine)


@pytest.fixture
def db() -> Session:
    """Database session fixture."""
    engine = create_engine("sqlite:///:memory:")
    # SQLite doesn't support schemas, so we need to drop the schema reference
    from sqlalchemy import MetaData

    meta = MetaData()
    for table in RichieBase.metadata.sorted_tables:
        # Create table without schema
        table.to_metadata(meta)
    meta.create_all(engine)
    session = Session(engine)
    yield session
    session.close()


# --- Need CRUD tests ---


def test_create_need(db: Session) -> None:
    """Test creating a need."""
    need = create_need(NeedCreate(name="ADHD", description="Attention deficit"), db)
    assert need.name == "ADHD"
    assert need.id is not None


def test_list_needs(db: Session) -> None:
    """Test listing needs."""
    create_need(NeedCreate(name="ADHD"), db)
    create_need(NeedCreate(name="Light Sensitive"), db)
    needs = list_needs(db)
    assert len(needs) == 2


def test_get_need(db: Session) -> None:
    """Test getting a need by ID."""
    created = create_need(NeedCreate(name="ADHD"), db)
    need = get_need(created.id, db)
    assert need.name == "ADHD"


def test_get_need_not_found(db: Session) -> None:
    """Test getting a need that doesn't exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_need(999, db)
    assert exc_info.value.status_code == 404


def test_delete_need(db: Session) -> None:
    """Test deleting a need."""
    created = create_need(NeedCreate(name="ADHD"), db)
    result = delete_need(created.id, db)
    assert result == {"deleted": True}


def test_delete_need_not_found(db: Session) -> None:
    """Test deleting a need that doesn't exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_need(999, db)
    assert exc_info.value.status_code == 404


# --- Contact CRUD tests ---


def test_create_contact(db: Session) -> None:
    """Test creating a contact."""
    contact = create_contact(ContactCreate(name="John"), db)
    assert contact.name == "John"
    assert contact.id is not None


def test_create_contact_with_needs(db: Session) -> None:
    """Test creating a contact with needs."""
    need = create_need(NeedCreate(name="ADHD"), db)
    contact = create_contact(ContactCreate(name="John", need_ids=[need.id]), db)
    assert len(contact.needs) == 1


def test_list_contacts(db: Session) -> None:
    """Test listing contacts."""
    create_contact(ContactCreate(name="John"), db)
    create_contact(ContactCreate(name="Jane"), db)
    contacts = list_contacts(db)
    assert len(contacts) == 2


def test_list_contacts_pagination(db: Session) -> None:
    """Test listing contacts with pagination."""
    for i in range(5):
        create_contact(ContactCreate(name=f"Contact {i}"), db)
    contacts = list_contacts(db, skip=2, limit=2)
    assert len(contacts) == 2


def test_get_contact(db: Session) -> None:
    """Test getting a contact by ID."""
    created = create_contact(ContactCreate(name="John"), db)
    contact = get_contact(created.id, db)
    assert contact.name == "John"


def test_get_contact_not_found(db: Session) -> None:
    """Test getting a contact that doesn't exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_contact(999, db)
    assert exc_info.value.status_code == 404


def test_update_contact(db: Session) -> None:
    """Test updating a contact."""
    created = create_contact(ContactCreate(name="John"), db)
    updated = update_contact(created.id, ContactUpdate(name="Jane", age=30), db)
    assert updated.name == "Jane"
    assert updated.age == 30


def test_update_contact_with_needs(db: Session) -> None:
    """Test updating a contact's needs."""
    need = create_need(NeedCreate(name="ADHD"), db)
    created = create_contact(ContactCreate(name="John"), db)
    updated = update_contact(created.id, ContactUpdate(need_ids=[need.id]), db)
    assert len(updated.needs) == 1


def test_update_contact_not_found(db: Session) -> None:
    """Test updating a contact that doesn't exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        update_contact(999, ContactUpdate(name="Jane"), db)
    assert exc_info.value.status_code == 404


def test_delete_contact(db: Session) -> None:
    """Test deleting a contact."""
    created = create_contact(ContactCreate(name="John"), db)
    result = delete_contact(created.id, db)
    assert result == {"deleted": True}


def test_delete_contact_not_found(db: Session) -> None:
    """Test deleting a contact that doesn't exist."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        delete_contact(999, db)
    assert exc_info.value.status_code == 404


# --- Need-Contact association tests ---


def test_add_need_to_contact(db: Session) -> None:
    """Test adding a need to a contact."""
    need = create_need(NeedCreate(name="ADHD"), db)
    contact = create_contact(ContactCreate(name="John"), db)
    result = add_need_to_contact(contact.id, need.id, db)
    assert result == {"added": True}


def test_add_need_to_contact_contact_not_found(db: Session) -> None:
    """Test adding need to nonexistent contact."""
    from fastapi import HTTPException

    need = create_need(NeedCreate(name="ADHD"), db)
    with pytest.raises(HTTPException) as exc_info:
        add_need_to_contact(999, need.id, db)
    assert exc_info.value.status_code == 404


def test_add_need_to_contact_need_not_found(db: Session) -> None:
    """Test adding nonexistent need to contact."""
    from fastapi import HTTPException

    contact = create_contact(ContactCreate(name="John"), db)
    with pytest.raises(HTTPException) as exc_info:
        add_need_to_contact(contact.id, 999, db)
    assert exc_info.value.status_code == 404


def test_remove_need_from_contact(db: Session) -> None:
    """Test removing a need from a contact."""
    need = create_need(NeedCreate(name="ADHD"), db)
    contact = create_contact(ContactCreate(name="John", need_ids=[need.id]), db)
    result = remove_need_from_contact(contact.id, need.id, db)
    assert result == {"removed": True}


def test_remove_need_from_contact_contact_not_found(db: Session) -> None:
    """Test removing need from nonexistent contact."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        remove_need_from_contact(999, 1, db)
    assert exc_info.value.status_code == 404


def test_remove_need_from_contact_need_not_found(db: Session) -> None:
    """Test removing nonexistent need from contact."""
    from fastapi import HTTPException

    contact = create_contact(ContactCreate(name="John"), db)
    with pytest.raises(HTTPException) as exc_info:
        remove_need_from_contact(contact.id, 999, db)
    assert exc_info.value.status_code == 404


# --- Relationship tests ---


def test_add_contact_relationship(db: Session) -> None:
    """Test adding a relationship between contacts."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    rel = add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    assert rel.contact_id == c1.id
    assert rel.related_contact_id == c2.id


def test_add_contact_relationship_default_weight(db: Session) -> None:
    """Test relationship uses default weight from type."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    rel = add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.SPOUSE),
        db,
    )
    assert rel.closeness_weight == RelationshipType.SPOUSE.default_weight


def test_add_contact_relationship_custom_weight(db: Session) -> None:
    """Test relationship with custom weight."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    rel = add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND, closeness_weight=8),
        db,
    )
    assert rel.closeness_weight == 8


def test_add_contact_relationship_contact_not_found(db: Session) -> None:
    """Test adding relationship with nonexistent contact."""
    from fastapi import HTTPException

    c2 = create_contact(ContactCreate(name="Jane"), db)
    with pytest.raises(HTTPException) as exc_info:
        add_contact_relationship(
            999,
            ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
            db,
        )
    assert exc_info.value.status_code == 404


def test_add_contact_relationship_related_not_found(db: Session) -> None:
    """Test adding relationship with nonexistent related contact."""
    from fastapi import HTTPException

    c1 = create_contact(ContactCreate(name="John"), db)
    with pytest.raises(HTTPException) as exc_info:
        add_contact_relationship(
            c1.id,
            ContactRelationshipCreate(related_contact_id=999, relationship_type=RelationshipType.FRIEND),
            db,
        )
    assert exc_info.value.status_code == 404


def test_add_contact_relationship_self(db: Session) -> None:
    """Test cannot relate contact to itself."""
    from fastapi import HTTPException

    c1 = create_contact(ContactCreate(name="John"), db)
    with pytest.raises(HTTPException) as exc_info:
        add_contact_relationship(
            c1.id,
            ContactRelationshipCreate(related_contact_id=c1.id, relationship_type=RelationshipType.FRIEND),
            db,
        )
    assert exc_info.value.status_code == 400


def test_get_contact_relationships(db: Session) -> None:
    """Test getting relationships for a contact."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    rels = get_contact_relationships(c1.id, db)
    assert len(rels) == 1


def test_get_contact_relationships_not_found(db: Session) -> None:
    """Test getting relationships for nonexistent contact."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        get_contact_relationships(999, db)
    assert exc_info.value.status_code == 404


def test_update_contact_relationship(db: Session) -> None:
    """Test updating a relationship."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    updated = update_contact_relationship(
        c1.id,
        c2.id,
        ContactRelationshipUpdate(closeness_weight=9),
        db,
    )
    assert updated.closeness_weight == 9


def test_update_contact_relationship_type(db: Session) -> None:
    """Test updating relationship type."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    updated = update_contact_relationship(
        c1.id,
        c2.id,
        ContactRelationshipUpdate(relationship_type=RelationshipType.BEST_FRIEND),
        db,
    )
    assert updated.relationship_type == "best_friend"


def test_update_contact_relationship_not_found(db: Session) -> None:
    """Test updating nonexistent relationship."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        update_contact_relationship(
            999,
            998,
            ContactRelationshipUpdate(closeness_weight=5),
            db,
        )
    assert exc_info.value.status_code == 404


def test_remove_contact_relationship(db: Session) -> None:
    """Test removing a relationship."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    result = remove_contact_relationship(c1.id, c2.id, db)
    assert result == {"deleted": True}


def test_remove_contact_relationship_not_found(db: Session) -> None:
    """Test removing nonexistent relationship."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        remove_contact_relationship(999, 998, db)
    assert exc_info.value.status_code == 404


# --- list_relationship_types ---


def test_list_relationship_types() -> None:
    """Test listing relationship types."""
    types = list_relationship_types()
    assert len(types) == len(RelationshipType)
    assert all(isinstance(t, RelationshipTypeInfo) for t in types)


# --- graph tests ---


def test_get_relationship_graph(db: Session) -> None:
    """Test getting relationship graph."""
    c1 = create_contact(ContactCreate(name="John"), db)
    c2 = create_contact(ContactCreate(name="Jane"), db)
    add_contact_relationship(
        c1.id,
        ContactRelationshipCreate(related_contact_id=c2.id, relationship_type=RelationshipType.FRIEND),
        db,
    )
    graph = get_relationship_graph(db)
    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1


def test_get_relationship_graph_empty(db: Session) -> None:
    """Test getting empty relationship graph."""
    graph = get_relationship_graph(db)
    assert len(graph.nodes) == 0
    assert len(graph.edges) == 0

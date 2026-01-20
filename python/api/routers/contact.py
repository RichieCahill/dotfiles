"""Contact API router."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from python.api.dependencies import DbSession
from python.orm.contact import Contact, ContactRelationship, Need, RelationshipType


class NeedBase(BaseModel):
    """Base schema for Need."""

    name: str
    description: str | None = None


class NeedCreate(NeedBase):
    """Schema for creating a Need."""


class NeedResponse(NeedBase):
    """Schema for Need response."""

    id: int

    model_config = {"from_attributes": True}


class ContactRelationshipCreate(BaseModel):
    """Schema for creating a contact relationship."""

    related_contact_id: int
    relationship_type: RelationshipType
    closeness_weight: int | None = None


class ContactRelationshipUpdate(BaseModel):
    """Schema for updating a contact relationship."""

    relationship_type: RelationshipType | None = None
    closeness_weight: int | None = None


class ContactRelationshipResponse(BaseModel):
    """Schema for contact relationship response."""

    contact_id: int
    related_contact_id: int
    relationship_type: str
    closeness_weight: int

    model_config = {"from_attributes": True}


class RelationshipTypeInfo(BaseModel):
    """Information about a relationship type."""

    value: str
    display_name: str
    default_weight: int


class GraphNode(BaseModel):
    """Node in the relationship graph."""

    id: int
    name: str
    current_job: str | None = None


class GraphEdge(BaseModel):
    """Edge in the relationship graph."""

    source: int
    target: int
    relationship_type: str
    closeness_weight: int


class GraphData(BaseModel):
    """Complete graph data for visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ContactBase(BaseModel):
    """Base schema for Contact."""

    name: str
    age: int | None = None
    bio: str | None = None
    current_job: str | None = None
    gender: str | None = None
    goals: str | None = None
    legal_name: str | None = None
    profile_pic: str | None = None
    safe_conversation_starters: str | None = None
    self_sufficiency_score: int | None = None
    social_structure_style: str | None = None
    ssn: str | None = None
    suffix: str | None = None
    timezone: str | None = None
    topics_to_avoid: str | None = None


class ContactCreate(ContactBase):
    """Schema for creating a Contact."""

    need_ids: list[int] = []


class ContactUpdate(BaseModel):
    """Schema for updating a Contact."""

    name: str | None = None
    age: int | None = None
    bio: str | None = None
    current_job: str | None = None
    gender: str | None = None
    goals: str | None = None
    legal_name: str | None = None
    profile_pic: str | None = None
    safe_conversation_starters: str | None = None
    self_sufficiency_score: int | None = None
    social_structure_style: str | None = None
    ssn: str | None = None
    suffix: str | None = None
    timezone: str | None = None
    topics_to_avoid: str | None = None
    need_ids: list[int] | None = None


class ContactResponse(ContactBase):
    """Schema for Contact response with relationships."""

    id: int
    needs: list[NeedResponse] = []
    related_to: list[ContactRelationshipResponse] = []
    related_from: list[ContactRelationshipResponse] = []

    model_config = {"from_attributes": True}


class ContactListResponse(ContactBase):
    """Schema for Contact list response."""

    id: int

    model_config = {"from_attributes": True}


router = APIRouter(prefix="/api", tags=["contacts"])


@router.post("/needs", response_model=NeedResponse)
def create_need(need: NeedCreate, db: DbSession) -> Need:
    """Create a new need."""
    db_need = Need(name=need.name, description=need.description)
    db.add(db_need)
    db.commit()
    db.refresh(db_need)
    return db_need


@router.get("/needs", response_model=list[NeedResponse])
def list_needs(db: DbSession) -> list[Need]:
    """List all needs."""
    return list(db.scalars(select(Need)).all())


@router.get("/needs/{need_id}", response_model=NeedResponse)
def get_need(need_id: int, db: DbSession) -> Need:
    """Get a need by ID."""
    need = db.get(Need, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    return need


@router.delete("/needs/{need_id}")
def delete_need(need_id: int, db: DbSession) -> dict[str, bool]:
    """Delete a need by ID."""
    need = db.get(Need, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")
    db.delete(need)
    db.commit()
    return {"deleted": True}


@router.post("/contacts", response_model=ContactResponse)
def create_contact(contact: ContactCreate, db: DbSession) -> Contact:
    """Create a new contact."""
    need_ids = contact.need_ids
    contact_data = contact.model_dump(exclude={"need_ids"})
    db_contact = Contact(**contact_data)

    if need_ids:
        needs = list(db.scalars(select(Need).where(Need.id.in_(need_ids))).all())
        db_contact.needs = needs

    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.get("/contacts", response_model=list[ContactListResponse])
def list_contacts(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
) -> list[Contact]:
    """List all contacts with pagination."""
    return list(db.scalars(select(Contact).offset(skip).limit(limit)).all())


@router.get("/contacts/{contact_id}", response_model=ContactResponse)
def get_contact(contact_id: int, db: DbSession) -> Contact:
    """Get a contact by ID with all relationships."""
    contact = db.scalar(
        select(Contact)
        .where(Contact.id == contact_id)
        .options(
            selectinload(Contact.needs),
            selectinload(Contact.related_to),
            selectinload(Contact.related_from),
        )
    )
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: DbSession,
) -> Contact:
    """Update a contact by ID."""
    db_contact = db.get(Contact, contact_id)
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    update_data = contact.model_dump(exclude_unset=True)
    need_ids = update_data.pop("need_ids", None)

    for key, value in update_data.items():
        setattr(db_contact, key, value)

    if need_ids is not None:
        needs = list(db.scalars(select(Need).where(Need.id.in_(need_ids))).all())
        db_contact.needs = needs

    db.commit()
    db.refresh(db_contact)
    return db_contact


@router.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: DbSession) -> dict[str, bool]:
    """Delete a contact by ID."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return {"deleted": True}


@router.post("/contacts/{contact_id}/needs/{need_id}")
def add_need_to_contact(
    contact_id: int,
    need_id: int,
    db: DbSession,
) -> dict[str, bool]:
    """Add a need to a contact."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    need = db.get(Need, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    if need not in contact.needs:
        contact.needs.append(need)
        db.commit()

    return {"added": True}


@router.delete("/contacts/{contact_id}/needs/{need_id}")
def remove_need_from_contact(
    contact_id: int,
    need_id: int,
    db: DbSession,
) -> dict[str, bool]:
    """Remove a need from a contact."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    need = db.get(Need, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    if need in contact.needs:
        contact.needs.remove(need)
        db.commit()

    return {"removed": True}


@router.post(
    "/contacts/{contact_id}/relationships",
    response_model=ContactRelationshipResponse,
)
def add_contact_relationship(
    contact_id: int,
    relationship: ContactRelationshipCreate,
    db: DbSession,
) -> ContactRelationship:
    """Add a relationship between two contacts."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    related_contact = db.get(Contact, relationship.related_contact_id)
    if not related_contact:
        raise HTTPException(status_code=404, detail="Related contact not found")

    if contact_id == relationship.related_contact_id:
        raise HTTPException(status_code=400, detail="Cannot relate contact to itself")

    # Use provided weight or default from relationship type
    weight = relationship.closeness_weight
    if weight is None:
        weight = relationship.relationship_type.default_weight

    db_relationship = ContactRelationship(
        contact_id=contact_id,
        related_contact_id=relationship.related_contact_id,
        relationship_type=relationship.relationship_type.value,
        closeness_weight=weight,
    )
    db.add(db_relationship)
    db.commit()
    db.refresh(db_relationship)
    return db_relationship


@router.get(
    "/contacts/{contact_id}/relationships",
    response_model=list[ContactRelationshipResponse],
)
def get_contact_relationships(
    contact_id: int,
    db: DbSession,
) -> list[ContactRelationship]:
    """Get all relationships for a contact."""
    contact = db.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    outgoing = list(db.scalars(select(ContactRelationship).where(ContactRelationship.contact_id == contact_id)).all())
    incoming = list(
        db.scalars(select(ContactRelationship).where(ContactRelationship.related_contact_id == contact_id)).all()
    )
    return outgoing + incoming


@router.patch(
    "/contacts/{contact_id}/relationships/{related_contact_id}",
    response_model=ContactRelationshipResponse,
)
def update_contact_relationship(
    contact_id: int,
    related_contact_id: int,
    update: ContactRelationshipUpdate,
    db: DbSession,
) -> ContactRelationship:
    """Update a relationship between two contacts."""
    relationship = db.scalar(
        select(ContactRelationship).where(
            ContactRelationship.contact_id == contact_id,
            ContactRelationship.related_contact_id == related_contact_id,
        )
    )
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    if update.relationship_type is not None:
        relationship.relationship_type = update.relationship_type.value
    if update.closeness_weight is not None:
        relationship.closeness_weight = update.closeness_weight

    db.commit()
    db.refresh(relationship)
    return relationship


@router.delete("/contacts/{contact_id}/relationships/{related_contact_id}")
def remove_contact_relationship(
    contact_id: int,
    related_contact_id: int,
    db: DbSession,
) -> dict[str, bool]:
    """Remove a relationship between two contacts."""
    relationship = db.scalar(
        select(ContactRelationship).where(
            ContactRelationship.contact_id == contact_id,
            ContactRelationship.related_contact_id == related_contact_id,
        )
    )
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    db.delete(relationship)
    db.commit()
    return {"deleted": True}


@router.get("/relationship-types")
def list_relationship_types() -> list[RelationshipTypeInfo]:
    """List all available relationship types with their default weights."""
    return [
        RelationshipTypeInfo(
            value=rt.value,
            display_name=rt.display_name,
            default_weight=rt.default_weight,
        )
        for rt in RelationshipType
    ]


@router.get("/graph")
def get_relationship_graph(db: DbSession) -> GraphData:
    """Get all contacts and relationships as graph data for visualization."""
    contacts = list(db.scalars(select(Contact)).all())
    relationships = list(db.scalars(select(ContactRelationship)).all())

    nodes = [GraphNode(id=c.id, name=c.name, current_job=c.current_job) for c in contacts]

    edges = [
        GraphEdge(
            source=rel.contact_id,
            target=rel.related_contact_id,
            relationship_type=rel.relationship_type,
            closeness_weight=rel.closeness_weight,
        )
        for rel in relationships
    ]

    return GraphData(nodes=nodes, edges=edges)

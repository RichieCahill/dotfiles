"""HTMX server-rendered view router."""

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from python.api.dependencies import DbSession
from python.orm.richie.contact import Contact, ContactRelationship, Need, RelationshipType

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(tags=["views"])

FAMILIAL_TYPES = {
    "parent",
    "child",
    "sibling",
    "grandparent",
    "grandchild",
    "aunt_uncle",
    "niece_nephew",
    "cousin",
    "in_law",
}
FRIEND_TYPES = {"best_friend", "close_friend", "friend", "acquaintance", "neighbor"}
PARTNER_TYPES = {"spouse", "partner"}
PROFESSIONAL_TYPES = {"mentor", "mentee", "business_partner", "colleague", "manager", "direct_report", "client"}

CONTACT_STRING_FIELDS = (
    "name",
    "legal_name",
    "suffix",
    "gender",
    "current_job",
    "timezone",
    "profile_pic",
    "bio",
    "goals",
    "social_structure_style",
    "safe_conversation_starters",
    "topics_to_avoid",
    "ssn",
)

CONTACT_INT_FIELDS = ("age", "self_sufficiency_score")


def _group_relationships(relationships: list[ContactRelationship]) -> dict[str, list[ContactRelationship]]:
    """Group relationships by category."""
    groups: dict[str, list[ContactRelationship]] = {
        "familial": [],
        "partners": [],
        "friends": [],
        "professional": [],
        "other": [],
    }
    for rel in relationships:
        if rel.relationship_type in FAMILIAL_TYPES:
            groups["familial"].append(rel)
        elif rel.relationship_type in PARTNER_TYPES:
            groups["partners"].append(rel)
        elif rel.relationship_type in FRIEND_TYPES:
            groups["friends"].append(rel)
        elif rel.relationship_type in PROFESSIONAL_TYPES:
            groups["professional"].append(rel)
        else:
            groups["other"].append(rel)
    return groups


def _build_contact_name_map(database: Session, contact: Contact) -> dict[int, str]:
    """Build a mapping of contact IDs to names for relationship display."""
    related_ids = {rel.related_contact_id for rel in contact.related_to}
    related_ids |= {rel.contact_id for rel in contact.related_from}
    related_ids.discard(contact.id)

    if not related_ids:
        return {}

    related_contacts = list(database.scalars(select(Contact).where(Contact.id.in_(related_ids))).all())
    return {related.id: related.name for related in related_contacts}


def _get_relationship_type_display() -> dict[str, str]:
    """Build a mapping of relationship type values to display names."""
    return {rel_type.value: rel_type.display_name for rel_type in RelationshipType}


async def _parse_contact_form(request: Request) -> dict[str, Any]:
    """Parse contact form data from a multipart/form request."""
    form_data = await request.form()
    result: dict[str, Any] = {}

    for field in CONTACT_STRING_FIELDS:
        value = form_data.get(field, "")
        result[field] = str(value) if value else None

    for field in CONTACT_INT_FIELDS:
        value = form_data.get(field, "")
        result[field] = int(value) if value else None

    result["need_ids"] = [int(value) for value in form_data.getlist("need_ids")]
    return result


def _save_contact_from_form(database: Session, contact: Contact, form_result: dict[str, Any]) -> None:
    """Apply parsed form data to a Contact and save associated needs."""
    need_ids = form_result.pop("need_ids")

    for key, value in form_result.items():
        setattr(contact, key, value)

    if need_ids:
        contact.needs = list(database.scalars(select(Need).where(Need.id.in_(need_ids))).all())
    else:
        contact.needs = []


@router.get("/", response_class=HTMLResponse)
@router.get("/contacts", response_class=HTMLResponse)
def contact_list_page(request: Request, database: DbSession) -> HTMLResponse:
    """Render the contacts list page."""
    contacts = list(database.scalars(select(Contact)).all())
    return templates.TemplateResponse(request, "contact_list.html", {"contacts": contacts})


@router.get("/contacts/new", response_class=HTMLResponse)
def new_contact_page(request: Request, database: DbSession) -> HTMLResponse:
    """Render the new contact form page."""
    all_needs = list(database.scalars(select(Need)).all())
    return templates.TemplateResponse(request, "contact_form.html", {"contact": None, "all_needs": all_needs})


@router.post("/htmx/contacts/new")
async def create_contact_form(request: Request, database: DbSession) -> RedirectResponse:
    """Handle the create contact form submission."""
    form_result = await _parse_contact_form(request)
    contact = Contact()
    _save_contact_from_form(database, contact, form_result)

    database.add(contact)
    database.commit()
    database.refresh(contact)
    return RedirectResponse(url=f"/contacts/{contact.id}", status_code=303)


@router.get("/contacts/{contact_id}", response_class=HTMLResponse)
def contact_detail_page(contact_id: int, request: Request, database: DbSession) -> HTMLResponse:
    """Render the contact detail page."""
    contact = database.scalar(
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

    contact_names = _build_contact_name_map(database, contact)
    grouped_relationships = _group_relationships(contact.related_to)
    all_contacts = list(database.scalars(select(Contact)).all())
    all_needs = list(database.scalars(select(Need)).all())
    available_needs = [need for need in all_needs if need not in contact.needs]

    return templates.TemplateResponse(
        request,
        "contact_detail.html",
        {
            "contact": contact,
            "contact_names": contact_names,
            "grouped_relationships": grouped_relationships,
            "all_contacts": all_contacts,
            "available_needs": available_needs,
            "relationship_types": list(RelationshipType),
        },
    )


@router.get("/contacts/{contact_id}/edit", response_class=HTMLResponse)
def edit_contact_page(contact_id: int, request: Request, database: DbSession) -> HTMLResponse:
    """Render the edit contact form page."""
    contact = database.scalar(select(Contact).where(Contact.id == contact_id).options(selectinload(Contact.needs)))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    all_needs = list(database.scalars(select(Need)).all())
    return templates.TemplateResponse(request, "contact_form.html", {"contact": contact, "all_needs": all_needs})


@router.post("/htmx/contacts/{contact_id}/edit")
async def update_contact_form(contact_id: int, request: Request, database: DbSession) -> RedirectResponse:
    """Handle the edit contact form submission."""
    contact = database.get(Contact, contact_id)
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    form_result = await _parse_contact_form(request)
    _save_contact_from_form(database, contact, form_result)

    database.commit()
    return RedirectResponse(url=f"/contacts/{contact_id}", status_code=303)


@router.post("/htmx/contacts/{contact_id}/add-need", response_class=HTMLResponse)
def add_need_to_contact_htmx(
    contact_id: int,
    request: Request,
    database: DbSession,
    need_id: Annotated[int, Form()],
) -> HTMLResponse:
    """Add a need to a contact and return updated manage-needs partial."""
    contact = database.scalar(select(Contact).where(Contact.id == contact_id).options(selectinload(Contact.needs)))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    need = database.get(Need, need_id)
    if not need:
        raise HTTPException(status_code=404, detail="Need not found")

    if need not in contact.needs:
        contact.needs.append(need)
        database.commit()
        database.refresh(contact)

    return templates.TemplateResponse(request, "partials/manage_needs.html", {"contact": contact})


@router.post("/htmx/contacts/{contact_id}/add-relationship", response_class=HTMLResponse)
def add_relationship_htmx(
    contact_id: int,
    request: Request,
    database: DbSession,
    related_contact_id: Annotated[int, Form()],
    relationship_type: Annotated[str, Form()],
) -> HTMLResponse:
    """Add a relationship and return updated manage-relationships partial."""
    contact = database.scalar(select(Contact).where(Contact.id == contact_id).options(selectinload(Contact.related_to)))
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    related_contact = database.get(Contact, related_contact_id)
    if not related_contact:
        raise HTTPException(status_code=404, detail="Related contact not found")

    rel_type = RelationshipType(relationship_type)
    weight = rel_type.default_weight

    relationship = ContactRelationship(
        contact_id=contact_id,
        related_contact_id=related_contact_id,
        relationship_type=relationship_type,
        closeness_weight=weight,
    )
    database.add(relationship)
    database.commit()
    database.refresh(contact)

    contact_names = _build_contact_name_map(database, contact)
    return templates.TemplateResponse(
        request,
        "partials/manage_relationships.html",
        {"contact": contact, "contact_names": contact_names},
    )


@router.post("/htmx/contacts/{contact_id}/relationships/{related_contact_id}/weight")
def update_relationship_weight_htmx(
    contact_id: int,
    related_contact_id: int,
    database: DbSession,
    closeness_weight: Annotated[int, Form()],
) -> HTMLResponse:
    """Update a relationship's closeness weight from HTMX range input."""
    relationship = database.scalar(
        select(ContactRelationship).where(
            ContactRelationship.contact_id == contact_id,
            ContactRelationship.related_contact_id == related_contact_id,
        )
    )
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    relationship.closeness_weight = closeness_weight
    database.commit()
    return HTMLResponse("")


@router.post("/htmx/needs", response_class=HTMLResponse)
def create_need_htmx(
    request: Request,
    database: DbSession,
    name: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
) -> HTMLResponse:
    """Create a need via form data and return updated needs list."""
    need = Need(name=name, description=description or None)
    database.add(need)
    database.commit()
    needs = list(database.scalars(select(Need)).all())
    return templates.TemplateResponse(request, "partials/need_items.html", {"needs": needs})


@router.get("/needs", response_class=HTMLResponse)
def needs_page(request: Request, database: DbSession) -> HTMLResponse:
    """Render the needs list page."""
    needs = list(database.scalars(select(Need)).all())
    return templates.TemplateResponse(request, "need_list.html", {"needs": needs})


@router.get("/graph", response_class=HTMLResponse)
def graph_page(request: Request, database: DbSession) -> HTMLResponse:
    """Render the relationship graph page."""
    contacts = list(database.scalars(select(Contact)).all())
    relationships = list(database.scalars(select(ContactRelationship)).all())

    graph_data = {
        "nodes": [{"id": contact.id, "name": contact.name, "current_job": contact.current_job} for contact in contacts],
        "edges": [
            {
                "source": rel.contact_id,
                "target": rel.related_contact_id,
                "relationship_type": rel.relationship_type,
                "closeness_weight": rel.closeness_weight,
            }
            for rel in relationships
        ],
    }

    return templates.TemplateResponse(
        request,
        "graph.html",
        {
            "graph_data": graph_data,
            "relationship_type_display": _get_relationship_type_display(),
        },
    )

"""Contact database models."""

from __future__ import annotations

from enum import Enum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.base import RichieBase, TableBase


class RelationshipType(str, Enum):
    """Relationship types with default closeness weights.

    Default weight is an integer 1-10 where 10 = closest relationship.
    Users can override this per-relationship in the UI.
    """

    SPOUSE = "spouse"
    PARTNER = "partner"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    BEST_FRIEND = "best_friend"
    GRANDPARENT = "grandparent"
    GRANDCHILD = "grandchild"
    AUNT_UNCLE = "aunt_uncle"
    NIECE_NEPHEW = "niece_nephew"
    COUSIN = "cousin"
    IN_LAW = "in_law"
    CLOSE_FRIEND = "close_friend"
    FRIEND = "friend"
    MENTOR = "mentor"
    MENTEE = "mentee"
    BUSINESS_PARTNER = "business_partner"
    COLLEAGUE = "colleague"
    MANAGER = "manager"
    DIRECT_REPORT = "direct_report"
    CLIENT = "client"
    ACQUAINTANCE = "acquaintance"
    NEIGHBOR = "neighbor"
    EX = "ex"
    OTHER = "other"

    @property
    def default_weight(self) -> int:
        """Return the default closeness weight (1-10) for this relationship type."""
        weights = {
            RelationshipType.SPOUSE: 10,
            RelationshipType.PARTNER: 10,
            RelationshipType.PARENT: 9,
            RelationshipType.CHILD: 9,
            RelationshipType.SIBLING: 9,
            RelationshipType.BEST_FRIEND: 8,
            RelationshipType.GRANDPARENT: 7,
            RelationshipType.GRANDCHILD: 7,
            RelationshipType.AUNT_UNCLE: 7,
            RelationshipType.NIECE_NEPHEW: 7,
            RelationshipType.COUSIN: 7,
            RelationshipType.IN_LAW: 7,
            RelationshipType.CLOSE_FRIEND: 6,
            RelationshipType.FRIEND: 6,
            RelationshipType.MENTOR: 5,
            RelationshipType.MENTEE: 5,
            RelationshipType.BUSINESS_PARTNER: 5,
            RelationshipType.COLLEAGUE: 4,
            RelationshipType.MANAGER: 4,
            RelationshipType.DIRECT_REPORT: 4,
            RelationshipType.CLIENT: 4,
            RelationshipType.ACQUAINTANCE: 3,
            RelationshipType.NEIGHBOR: 3,
            RelationshipType.EX: 2,
            RelationshipType.OTHER: 2,
        }
        return weights.get(self, 5)

    @property
    def display_name(self) -> str:
        """Return a human-readable display name."""
        return self.value.replace("_", " ").title()


class ContactNeed(RichieBase):
    """Association table: Contact <-> Need."""

    __tablename__ = "contact_need"

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("main.contact.id", ondelete="CASCADE"),
        primary_key=True,
    )
    need_id: Mapped[int] = mapped_column(
        ForeignKey("main.need.id", ondelete="CASCADE"),
        primary_key=True,
    )


class ContactRelationship(RichieBase):
    """Association table: Contact <-> Contact with relationship type and weight."""

    __tablename__ = "contact_relationship"

    contact_id: Mapped[int] = mapped_column(
        ForeignKey("main.contact.id", ondelete="CASCADE"),
        primary_key=True,
    )
    related_contact_id: Mapped[int] = mapped_column(
        ForeignKey("main.contact.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relationship_type: Mapped[str] = mapped_column(String(100))
    closeness_weight: Mapped[int] = mapped_column(default=5)


class Contact(TableBase):
    """Contact model."""

    __tablename__ = "contact"

    name: Mapped[str]

    age: Mapped[int | None]
    bio: Mapped[str | None]
    current_job: Mapped[str | None]
    gender: Mapped[str | None]
    goals: Mapped[str | None]
    legal_name: Mapped[str | None]
    profile_pic: Mapped[str | None]
    safe_conversation_starters: Mapped[str | None]
    self_sufficiency_score: Mapped[int | None]
    social_structure_style: Mapped[str | None]
    ssn: Mapped[str | None]
    suffix: Mapped[str | None]
    timezone: Mapped[str | None]
    topics_to_avoid: Mapped[str | None]

    needs: Mapped[list[Need]] = relationship(
        "Need",
        secondary=ContactNeed.__table__,
        back_populates="contacts",
    )

    related_to: Mapped[list[ContactRelationship]] = relationship(
        "ContactRelationship",
        foreign_keys=[ContactRelationship.contact_id],
        cascade="all, delete-orphan",
    )
    related_from: Mapped[list[ContactRelationship]] = relationship(
        "ContactRelationship",
        foreign_keys=[ContactRelationship.related_contact_id],
        cascade="all, delete-orphan",
    )


class Need(TableBase):
    """Need/accommodation model (e.g., light sensitive, ADHD)."""

    __tablename__ = "need"

    name: Mapped[str]
    description: Mapped[str | None]

    contacts: Mapped[list[Contact]] = relationship(
        "Contact",
        secondary=ContactNeed.__table__,
        back_populates="needs",
    )

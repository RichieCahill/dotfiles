"""Van inventory ORM models."""

from __future__ import annotations

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from python.orm.van_inventory.base import VanTableBase


class Item(VanTableBase):
    """A food item in the van."""

    __tablename__ = "items"

    name: Mapped[str] = mapped_column(unique=True)
    quantity: Mapped[float] = mapped_column(default=0)
    unit: Mapped[str]
    category: Mapped[str | None]

    meal_ingredients: Mapped[list[MealIngredient]] = relationship(back_populates="item")


class Meal(VanTableBase):
    """A meal that can be made from items in the van."""

    __tablename__ = "meals"

    name: Mapped[str] = mapped_column(unique=True)
    instructions: Mapped[str | None]

    ingredients: Mapped[list[MealIngredient]] = relationship(back_populates="meal")


class MealIngredient(VanTableBase):
    """Links a meal to the items it requires, with quantities."""

    __tablename__ = "meal_ingredients"
    __table_args__ = (UniqueConstraint("meal_id", "item_id"),)

    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id"))
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    quantity_needed: Mapped[float]

    meal: Mapped[Meal] = relationship(back_populates="ingredients")
    item: Mapped[Item] = relationship(back_populates="meal_ingredients")

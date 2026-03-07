"""Van inventory API router."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from python.orm.van_inventory.models import Item, Meal, MealIngredient

if TYPE_CHECKING:
    from python.van_inventory.dependencies import DbSession


# --- Schemas ---


class ItemCreate(BaseModel):
    """Schema for creating an item."""

    name: str
    quantity: float = 0
    unit: str
    category: str | None = None


class ItemUpdate(BaseModel):
    """Schema for updating an item."""

    name: str | None = None
    quantity: float | None = None
    unit: str | None = None
    category: str | None = None


class ItemResponse(BaseModel):
    """Schema for item response."""

    id: int
    name: str
    quantity: float
    unit: str
    category: str | None

    model_config = {"from_attributes": True}


class IngredientCreate(BaseModel):
    """Schema for adding an ingredient to a meal."""

    item_id: int
    quantity_needed: float


class MealCreate(BaseModel):
    """Schema for creating a meal."""

    name: str
    instructions: str | None = None
    ingredients: list[IngredientCreate] = []


class MealUpdate(BaseModel):
    """Schema for updating a meal."""

    name: str | None = None
    instructions: str | None = None


class IngredientResponse(BaseModel):
    """Schema for ingredient response."""

    item_id: int
    item_name: str
    quantity_needed: float
    unit: str

    model_config = {"from_attributes": True}


class MealResponse(BaseModel):
    """Schema for meal response."""

    id: int
    name: str
    instructions: str | None
    ingredients: list[IngredientResponse] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_meal(cls, meal: Meal) -> MealResponse:
        """Build a MealResponse from an ORM Meal with loaded ingredients."""
        return cls(
            id=meal.id,
            name=meal.name,
            instructions=meal.instructions,
            ingredients=[
                IngredientResponse(
                    item_id=mi.item_id,
                    item_name=mi.item.name,
                    quantity_needed=mi.quantity_needed,
                    unit=mi.item.unit,
                )
                for mi in meal.ingredients
            ],
        )


class ShoppingItem(BaseModel):
    """An item needed for a meal that is short on stock."""

    item_name: str
    unit: str
    needed: float
    have: float
    short: float


class MealAvailability(BaseModel):
    """Availability status for a meal."""

    meal_id: int
    meal_name: str
    can_make: bool
    missing: list[ShoppingItem] = []


# --- Routes ---

router = APIRouter(prefix="/api", tags=["van_inventory"])


# Items


@router.post("/items", response_model=ItemResponse)
def create_item(item: ItemCreate, db: DbSession) -> Item:
    """Create a new inventory item."""
    db_item = Item(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/items", response_model=list[ItemResponse])
def list_items(db: DbSession) -> list[Item]:
    """List all inventory items."""
    return list(db.scalars(select(Item).order_by(Item.name)).all())


@router.get("/items/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: DbSession) -> Item:
    """Get an item by ID."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.patch("/items/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, item: ItemUpdate, db: DbSession) -> Item:
    """Update an item by ID."""
    db_item = db.get(Item, item_id)
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/items/{item_id}")
def delete_item(item_id: int, db: DbSession) -> dict[str, bool]:
    """Delete an item by ID."""
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return {"deleted": True}


# Meals


@router.post("/meals", response_model=MealResponse)
def create_meal(meal: MealCreate, db: DbSession) -> MealResponse:
    """Create a new meal with optional ingredients."""
    db_meal = Meal(name=meal.name, instructions=meal.instructions)
    db.add(db_meal)
    db.flush()
    for ing in meal.ingredients:
        db.add(MealIngredient(meal_id=db_meal.id, item_id=ing.item_id, quantity_needed=ing.quantity_needed))
    db.commit()
    db_meal = db.scalar(
        select(Meal)
        .where(Meal.id == db_meal.id)
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
    )
    return MealResponse.from_meal(db_meal)


@router.get("/meals", response_model=list[MealResponse])
def list_meals(db: DbSession) -> list[MealResponse]:
    """List all meals with ingredients."""
    meals = list(
        db.scalars(
            select(Meal)
            .options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
            .order_by(Meal.name)
        ).all()
    )
    return [MealResponse.from_meal(m) for m in meals]


@router.get("/meals/{meal_id}", response_model=MealResponse)
def get_meal(meal_id: int, db: DbSession) -> MealResponse:
    """Get a meal by ID with ingredients."""
    meal = db.scalar(
        select(Meal)
        .where(Meal.id == meal_id)
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return MealResponse.from_meal(meal)


@router.delete("/meals/{meal_id}")
def delete_meal(meal_id: int, db: DbSession) -> dict[str, bool]:
    """Delete a meal by ID."""
    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    db.delete(meal)
    db.commit()
    return {"deleted": True}


@router.post("/meals/{meal_id}/ingredients", response_model=MealResponse)
def add_ingredient(meal_id: int, ingredient: IngredientCreate, db: DbSession) -> MealResponse:
    """Add an ingredient to a meal."""
    meal = db.get(Meal, meal_id)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    db.add(MealIngredient(meal_id=meal_id, item_id=ingredient.item_id, quantity_needed=ingredient.quantity_needed))
    db.commit()
    meal = db.scalar(
        select(Meal)
        .where(Meal.id == meal_id)
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
    )
    return MealResponse.from_meal(meal)


@router.delete("/meals/{meal_id}/ingredients/{item_id}")
def remove_ingredient(meal_id: int, item_id: int, db: DbSession) -> dict[str, bool]:
    """Remove an ingredient from a meal."""
    mi = db.scalar(
        select(MealIngredient).where(MealIngredient.meal_id == meal_id, MealIngredient.item_id == item_id)
    )
    if not mi:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(mi)
    db.commit()
    return {"deleted": True}


# What can I make / what do I need


@router.get("/meals/availability", response_model=list[MealAvailability])
def check_all_meals(db: DbSession) -> list[MealAvailability]:
    """Check which meals can be made with current inventory."""
    meals = list(
        db.scalars(
            select(Meal).options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
        ).all()
    )
    return [_check_meal(m) for m in meals]


@router.get("/meals/{meal_id}/availability", response_model=MealAvailability)
def check_meal(meal_id: int, db: DbSession) -> MealAvailability:
    """Check if a specific meal can be made and what's missing."""
    meal = db.scalar(
        select(Meal)
        .where(Meal.id == meal_id)
        .options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
    )
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    return _check_meal(meal)


def _check_meal(meal: Meal) -> MealAvailability:
    missing = [
        ShoppingItem(
            item_name=mi.item.name,
            unit=mi.item.unit,
            needed=mi.quantity_needed,
            have=mi.item.quantity,
            short=mi.quantity_needed - mi.item.quantity,
        )
        for mi in meal.ingredients
        if mi.item.quantity < mi.quantity_needed
    ]
    return MealAvailability(
        meal_id=meal.id,
        meal_name=meal.name,
        can_make=len(missing) == 0,
        missing=missing,
    )

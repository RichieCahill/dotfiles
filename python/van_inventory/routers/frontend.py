"""HTMX frontend routes for van inventory."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from python.orm.van_inventory.models import Item, Meal, MealIngredient

# FastAPI needs DbSession at runtime to resolve the Depends() annotation
from python.van_inventory.dependencies import DbSession  # noqa: TC001
from python.van_inventory.routers.api import _check_meal

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(tags=["frontend"])


# --- Items ---


@router.get("/", response_class=HTMLResponse)
def items_page(request: Request, db: DbSession) -> HTMLResponse:
    """Render the inventory page."""
    items = list(db.scalars(select(Item).order_by(Item.name)).all())
    return templates.TemplateResponse(request, "items.html", {"items": items})


@router.post("/items", response_class=HTMLResponse)
def htmx_create_item(
    request: Request,
    db: DbSession,
    name: Annotated[str, Form()],
    quantity: Annotated[float, Form()] = 0,
    unit: Annotated[str, Form()] = "",
    category: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """Create an item and return updated item rows."""
    db.add(Item(name=name, quantity=quantity, unit=unit, category=category or None))
    db.commit()
    items = list(db.scalars(select(Item).order_by(Item.name)).all())
    return templates.TemplateResponse(request, "partials/item_rows.html", {"items": items})


@router.patch("/items/{item_id}", response_class=HTMLResponse)
def htmx_update_item(
    request: Request,
    item_id: int,
    db: DbSession,
    quantity: Annotated[float, Form()],
) -> HTMLResponse:
    """Update an item's quantity and return updated item rows."""
    item = db.get(Item, item_id)
    if item:
        item.quantity = quantity
        db.commit()
    items = list(db.scalars(select(Item).order_by(Item.name)).all())
    return templates.TemplateResponse(request, "partials/item_rows.html", {"items": items})


@router.delete("/items/{item_id}", response_class=HTMLResponse)
def htmx_delete_item(request: Request, item_id: int, db: DbSession) -> HTMLResponse:
    """Delete an item and return updated item rows."""
    item = db.get(Item, item_id)
    if item:
        db.delete(item)
        db.commit()
    items = list(db.scalars(select(Item).order_by(Item.name)).all())
    return templates.TemplateResponse(request, "partials/item_rows.html", {"items": items})


# --- Meals ---


def _load_meals(db: DbSession) -> list[Meal]:
    return list(
        db.scalars(
            select(Meal).options(selectinload(Meal.ingredients).selectinload(MealIngredient.item)).order_by(Meal.name)
        ).all()
    )


@router.get("/meals", response_class=HTMLResponse)
def meals_page(request: Request, db: DbSession) -> HTMLResponse:
    """Render the meals page."""
    meals = _load_meals(db)
    return templates.TemplateResponse(request, "meals.html", {"meals": meals})


@router.post("/meals", response_class=HTMLResponse)
def htmx_create_meal(
    request: Request,
    db: DbSession,
    name: Annotated[str, Form()],
    instructions: Annotated[str | None, Form()] = None,
) -> HTMLResponse:
    """Create a meal and return updated meal rows."""
    db.add(Meal(name=name, instructions=instructions or None))
    db.commit()
    meals = _load_meals(db)
    return templates.TemplateResponse(request, "partials/meal_rows.html", {"meals": meals})


@router.delete("/meals/{meal_id}", response_class=HTMLResponse)
def htmx_delete_meal(request: Request, meal_id: int, db: DbSession) -> HTMLResponse:
    """Delete a meal and return updated meal rows."""
    meal = db.get(Meal, meal_id)
    if meal:
        db.delete(meal)
        db.commit()
    meals = _load_meals(db)
    return templates.TemplateResponse(request, "partials/meal_rows.html", {"meals": meals})


# --- Meal detail ---


def _load_meal(db: DbSession, meal_id: int) -> Meal | None:
    return db.scalar(
        select(Meal).where(Meal.id == meal_id).options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))
    )


@router.get("/meals/{meal_id}", response_class=HTMLResponse)
def meal_detail_page(request: Request, meal_id: int, db: DbSession) -> HTMLResponse:
    """Render the meal detail page."""
    meal = _load_meal(db, meal_id)
    items = list(db.scalars(select(Item).order_by(Item.name)).all())
    return templates.TemplateResponse(request, "meal_detail.html", {"meal": meal, "items": items})


@router.post("/meals/{meal_id}/ingredients", response_class=HTMLResponse)
def htmx_add_ingredient(
    request: Request,
    meal_id: int,
    db: DbSession,
    item_id: Annotated[int, Form()],
    quantity_needed: Annotated[float, Form()],
) -> HTMLResponse:
    """Add an ingredient to a meal and return updated ingredient rows."""
    db.add(MealIngredient(meal_id=meal_id, item_id=item_id, quantity_needed=quantity_needed))
    db.commit()
    meal = _load_meal(db, meal_id)
    return templates.TemplateResponse(request, "partials/ingredient_rows.html", {"meal": meal})


@router.delete("/meals/{meal_id}/ingredients/{item_id}", response_class=HTMLResponse)
def htmx_remove_ingredient(
    request: Request,
    meal_id: int,
    item_id: int,
    db: DbSession,
) -> HTMLResponse:
    """Remove an ingredient from a meal and return updated ingredient rows."""
    mi = db.scalar(select(MealIngredient).where(MealIngredient.meal_id == meal_id, MealIngredient.item_id == item_id))
    if mi:
        db.delete(mi)
        db.commit()
    meal = _load_meal(db, meal_id)
    return templates.TemplateResponse(request, "partials/ingredient_rows.html", {"meal": meal})


# --- Availability ---


@router.get("/availability", response_class=HTMLResponse)
def availability_page(request: Request, db: DbSession) -> HTMLResponse:
    """Render the meal availability page."""
    meals = list(
        db.scalars(select(Meal).options(selectinload(Meal.ingredients).selectinload(MealIngredient.item))).all()
    )
    availability = [_check_meal(m) for m in meals]
    return templates.TemplateResponse(request, "availability.html", {"availability": availability})

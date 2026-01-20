"""FastAPI dependencies."""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session


def get_db(request: Request) -> Iterator[Session]:
    """Get database session from app state."""
    with Session(request.app.state.engine) as session:
        yield session


DbSession = Annotated[Session, Depends(get_db)]

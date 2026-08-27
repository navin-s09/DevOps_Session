from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Annotated
from sqlalchemy.orm import Session
from database import get_db
from models import DBItem
from crud import get_item_from_db, get_all_items_from_db, create_item_in_db, update_item_in_db, delete_item_in_db

# Dependency for database session
DBDependency = Annotated[Session, Depends(get_db)]

app = FastAPI(
    title="My FastAPI Project (DevOps Session)",
    description="A basic FastAPI application from the DevOps Session",
    version="1.0.0"
)


# Model for request validation
class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    is_available: bool = True
    model_config = {"from_attributes": True}

class ItemResponseDTO(BaseModel):
    item: Optional[Item] = None
    error: Optional[str] = None


class ItemAllResponseDTO(BaseModel):
    items: list[Item]
    count: int

@app.get("/")
def root(name: Optional[str] = None):
    """Root endpoint"""
    if (name != None):
        return {"msg": f"Hello {name}, welcome"}
    return {"message": "Welcome to FastAPI I am Navin "}


@app.get("/items/{item_id}")
def get_item(item_id: int, db: DBDependency) -> ItemResponseDTO:
    """Get an item by ID"""
    db_item = get_item_from_db(db, item_id)
    if db_item is None:
        return {"item": None, "error": "Item not found"}
    return {"item": Item.model_validate(db_item)}


@app.get("/items")
def get_all_items(db: DBDependency) -> ItemAllResponseDTO:
    """Get all items"""
    db_items = get_all_items_from_db(db)
    items = [Item.model_validate(db_item) for db_item in db_items]
    return {"items": items, "count": len(items)}


@app.post("/items")
def create_item(item: Item, db: DBDependency):
    """Create a new item"""
    db_item = create_item_in_db(db, item.model_dump())
    return {"id": db_item.id, **item.model_dump()}


@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item, db: DBDependency):
    """Update an item"""
    db_item = update_item_in_db(db, item_id, item.model_dump())
    if db_item is None:
        return {"error": "Item not found"}
    return {"id": item_id, **item.model_dump()}


@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: DBDependency):
    """Delete an item"""
    if not delete_item_in_db(db, item_id):
        return {"error": "Item not found"}
    return {"message": "Item deleted successfully"}

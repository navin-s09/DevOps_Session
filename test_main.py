"""
Basic pytest tests for the FastAPI application
"""
import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from models import DBItem

# Setup test database
TEST_DATABASE_URL = "sqlite:///./test_database.db"

test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Create test database tables
Base.metadata.create_all(bind=test_engine)

# Override the get_db dependency for testing
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the dependency in the app
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

@pytest.fixture
def test_db():
    """Fixture to provide a clean database for each test"""
    # Create all tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create a test session
    db = TestingSessionLocal()
    
    # Yield the database session
    yield db
    
    # Clean up - drop all tables and close the session
    db.close()
    Base.metadata.drop_all(bind=test_engine)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI I am Navin "}

def test_root_endpoint_with_name():
    """Test the root endpoint with name parameter"""
    response = client.get("/", params={"name": "John"})
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello John, welcome"}

def test_create_item(test_db):
    """Test creating a new item"""
    # Test data
    item_data = {
        "name": "Test Item",
        "description": "This is a test item",
        "price": 9.99,
        "is_available": True
    }
    
    # Make request
    response = client.post("/items", json=item_data)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == item_data["name"]
    assert data["description"] == item_data["description"]
    assert data["price"] == item_data["price"]
    assert data["is_available"] == item_data["is_available"]

def test_get_item(test_db):
    """Test getting an item by ID"""
    # First create an item
    db_item = DBItem(
        name="Test Item",
        description="Test description",
        price=19.99,
        is_available=True
    )
    test_db.add(db_item)
    test_db.commit()
    test_db.refresh(db_item)
    
    # Test getting the item
    response = client.get(f"/items/{db_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["item"]["name"] == "Test Item"
    assert data["item"]["price"] == 19.99

def test_get_nonexistent_item(test_db):
    """Test getting a non-existent item"""
    response = client.get("/items/999")
    assert response.status_code == 200
    data = response.json()
    assert data["item"] is None
    assert data["error"] == "Item not found"

def test_get_all_items(test_db):
    """Test getting all items"""
    # Create some test items
    items = [
        DBItem(name="Item 1", description="Desc 1", price=10.0, is_available=True),
        DBItem(name="Item 2", description="Desc 2", price=20.0, is_available=False),
        DBItem(name="Item 3", description="Desc 3", price=30.0, is_available=True),
    ]
    
    for item in items:
        test_db.add(item)
    test_db.commit()
    
    # Test getting all items
    response = client.get("/items")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 3
    assert len(data["items"]) == 3

def test_update_item(test_db):
    """Test updating an item"""
    # Create an item first
    db_item = DBItem(
        name="Original Name",
        description="Original Desc",
        price=15.0,
        is_available=True
    )
    test_db.add(db_item)
    test_db.commit()
    test_db.refresh(db_item)
    
    # Update data
    update_data = {
        "name": "Updated Name",
        "description": "Updated Desc",
        "price": 25.0,
        "is_available": False
    }
    
    # Make update request
    response = client.put(f"/items/{db_item.id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["price"] == 25.0

def test_update_nonexistent_item(test_db):
    """Test updating a non-existent item"""
    update_data = {
        "name": "Updated Name",
        "description": "Updated Desc",
        "price": 25.0,
        "is_available": False
    }
    
    response = client.put("/items/999", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["error"] == "Item not found"

def test_delete_item(test_db):
    """Test deleting an item"""
    # Create an item first
    db_item = DBItem(
        name="Item to Delete",
        description="Will be deleted",
        price=10.0,
        is_available=True
    )
    test_db.add(db_item)
    test_db.commit()
    test_db.refresh(db_item)
    
    # Delete the item
    response = client.delete(f"/items/{db_item.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Item deleted successfully"

def test_delete_nonexistent_item(test_db):
    """Test deleting a non-existent item"""
    response = client.delete("/items/999")
    assert response.status_code == 200
    data = response.json()
    assert data["error"] == "Item not found"

# Clean up after all tests
# Note: This is handled by the test_db fixture for each test

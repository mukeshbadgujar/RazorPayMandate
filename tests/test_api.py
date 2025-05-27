import pytest
from decimal import Decimal


def test_create_customer(test_client):
    """Test creating a new customer"""
    customer_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "contact": "9876543210",
        "gstin": "29ABCDE1234F1Z5"
    }
    
    response = test_client.post("/api/v1/customers/", json=customer_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Customer created successfully"
    assert "customer" in data["data"]
    assert data["data"]["customer"]["email"] == customer_data["email"]


def test_get_customer(test_client):
    """Test getting a customer by ID"""
    # First create a customer
    customer_data = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "contact": "9876543211"
    }
    
    create_response = test_client.post("/api/v1/customers/", json=customer_data)
    customer_id = create_response.json()["data"]["customer"]["id"]
    
    # Get the customer
    response = test_client.get(f"/api/v1/customers/{customer_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"]["customer"]["id"] == customer_id


def test_create_mandate(test_client):
    """Test creating a mandate"""
    # First create a customer
    customer_data = {
        "name": "Test User",
        "email": "test.user@example.com",
        "contact": "9876543212"
    }
    
    customer_response = test_client.post("/api/v1/customers/", json=customer_data)
    customer_id = customer_response.json()["data"]["customer"]["id"]
    
    # Create mandate
    mandate_data = {
        "customer_id": customer_id,
        "amount": 1000.00,
        "frequency": "monthly",
        "notes": "Test mandate"
    }
    
    response = test_client.post("/api/v1/mandates/", json=mandate_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "Mandate created successfully"
    assert data["data"]["mandate"]["customer_id"] == customer_id


def test_emandate_authorization(test_client):
    """Test eMandate authorization"""
    # First create a customer
    customer_data = {
        "name": "Authorization User",
        "email": "auth.user@example.com",
        "contact": "9876543213"
    }
    
    customer_response = test_client.post("/api/v1/customers/", json=customer_data)
    customer_id = customer_response.json()["data"]["customer"]["id"]
    
    # Authorize eMandate
    auth_data = {
        "customer_id": customer_id,
        "amount": 500.00,
        "frequency": "monthly",
        "description": "Test authorization"
    }
    
    response = test_client.post("/api/v1/emandate/authorize", json=auth_data)
    assert response.status_code == 202
    
    data = response.json()
    assert data["success"] is True
    assert data["message"] == "eMandate authorization initiated successfully"
    assert "mandate_id" in data["data"]
    assert "task_id" in data["data"]


def test_health_check(test_client):
    """Test health check endpoint"""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(test_client):
    """Test root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data

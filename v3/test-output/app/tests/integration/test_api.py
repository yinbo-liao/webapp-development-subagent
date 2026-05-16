import pytest

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_login_success(self, client, test_user):
        response = client.post(
            "/auth/login",
            data={"username": "test@example.com", "password": "Test123!"}
        )
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_login_failure(self, client):
        response = client.post(
            "/auth/login",
            data={"username": "wrong@example.com", "password": "wrong"}
        )
        assert response.status_code == 401
    
    def test_protected_endpoint_without_auth(self, client):
        response = client.get("/users/")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_auth(self, client, auth_headers):
        response = client.get("/users/", headers=auth_headers)
        assert response.status_code == 200

class TestCRUDOperations:
    """Test CRUD operations"""
    
    def test_create_item(self, client, auth_headers):
        response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Item"
    
    def test_read_item(self, client, auth_headers):
        # First create an item
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        # Then read it
        response = client.get(f"/items/{item_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == item_id
    
    def test_update_item(self, client, auth_headers):
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        response = client.put(
            f"/items/{item_id}",
            json={"name": "Updated Item", "description": "Updated Description"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Item"
    
    def test_delete_item(self, client, auth_headers):
        create_response = client.post(
            "/items/",
            json={"name": "Test Item", "description": "Test Description"},
            headers=auth_headers
        )
        item_id = create_response.json()["id"]
        
        response = client.delete(f"/items/{item_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deletion
        get_response = client.get(f"/items/{item_id}", headers=auth_headers)
        assert get_response.status_code == 404

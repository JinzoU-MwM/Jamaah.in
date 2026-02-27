"""
Integration tests for authentication endpoints.
"""
import pytest
from fastapi import status


class TestAuthRegistration:
    """Test user registration flow."""
    
    def test_register_success(self, client):
        """Successful registration should create user and send OTP."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "SecurePass123!",
                "name": "New User"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "newuser@example.com"
    
    def test_register_duplicate_email(self, client, test_user):
        """Duplicate email should return 400."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user.email,
                "password": "SecurePass123!",
                "name": "Duplicate User"
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_register_weak_password(self, client):
        """Weak password should return 400."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com",
                "password": "123",
                "name": "Weak User"
            }
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Test user login flow."""
    
    def test_login_success(self, client, test_user):
        """Successful login should return token."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "test_password"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
    
    def test_login_wrong_password(self, client, test_user):
        """Wrong password should return 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user.email,
                "password": "wrong_password"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_user(self, client):
        """Nonexistent user should return 401."""
        response = client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "password"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestProtectedEndpoints:
    """Test that protected endpoints require auth."""
    
    def test_get_me_without_auth(self, client):
        """Getting profile without token should return 401."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_get_me_with_auth(self, client, auth_headers):
        """Getting profile with valid token should succeed."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "email" in data

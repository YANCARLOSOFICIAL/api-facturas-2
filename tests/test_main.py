import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from main import app

# Configuración para tests
@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def async_client():
    return AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Test del endpoint de health"""
    async with async_client as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

@pytest.mark.asyncio 
async def test_root_endpoint(async_client):
    """Test del endpoint root"""
    async with async_client as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert "Invoice Processing API" in response.json()["message"]

@pytest.mark.asyncio
async def test_invoice_health(async_client):
    """Test del health del servicio de facturas"""
    async with async_client as ac:
        response = await ac.get("/api/v1/invoices/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_process_invoice_no_file(client):
    """Test de procesamiento sin archivo"""
    response = client.post("/api/v1/invoices/process")
    assert response.status_code == 422  # Validation error

# Agregar más tests según necesidades

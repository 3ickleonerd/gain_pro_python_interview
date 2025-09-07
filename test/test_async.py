import pytest_asyncio
import pytest
import httpx
from app.main import app
from app import helper

@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url='http://127.0.0.1:8000') as client:
        yield client

@pytest.mark.asyncio
async def test_service_is_up(async_client):
    response = await async_client.get('/v1/')
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_tf_idf_against_ground_truth(async_client):
    hit_percent = await helper.get_overlap_percentage(async_client, 'tf_idf_similarity')
    assert hit_percent > 20

@pytest.mark.asyncio
async def test_semantic_against_ground_truth(async_client):
    hit_percent = await helper.get_overlap_percentage(async_client, 'semantic_similarity')
    assert hit_percent > 24

@pytest.mark.asyncio
async def test_dense_vector_against_ground_truth(async_client):
    hit_percent = await helper.get_overlap_percentage(async_client, 'dense_vector_similarity')
    assert hit_percent > 29
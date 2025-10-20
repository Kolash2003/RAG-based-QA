import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import io

from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_upload_document():
    """Test document upload."""
    # Create a test text file
    test_content = b"This is a test document. It contains sample text for testing."
    test_file = io.BytesIO(test_content)
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.txt", test_file, "text/plain")}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "test.txt"
    assert data["num_chunks"] > 0


def test_upload_unsupported_format():
    """Test upload with unsupported file format."""
    test_file = io.BytesIO(b"test content")
    
    response = client.post(
        "/api/v1/upload",
        files={"file": ("test.xyz", test_file, "application/octet-stream")}
    )
    
    assert response.status_code == 400


def test_query_without_documents():
    """Test query when no documents are uploaded."""
    response = client.post(
        "/api/v1/query",
        json={"question": "What is this about?"}
    )
    
    # Should still return a response
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data


def test_query_validation():
    """Test query validation."""
    # Empty question
    response = client.post(
        "/api/v1/query",
        json={"question": ""}
    )
    assert response.status_code == 422
    
    # Missing question
    response = client.post(
        "/api/v1/query",
        json={}
    )
    assert response.status_code == 422


def test_get_stats():
    """Test stats endpoint."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data


@pytest.mark.asyncio
async def test_full_workflow():
    """Test complete upload and query workflow."""
    # Upload document
    test_content = b"Python is a programming language. It is used for web development, data science, and AI."
    test_file = io.BytesIO(test_content)
    
    upload_response = client.post(
        "/api/v1/upload",
        files={"file": ("python_info.txt", test_file, "text/plain")}
    )
    
    assert upload_response.status_code == 200
    document_id = upload_response.json()["document_id"]
    
    # Query the document
    query_response = client.post(
        "/api/v1/query",
        json={"question": "What is Python used for?"}
    )
    
    assert query_response.status_code == 200
    data = query_response.json()
    assert "answer" in data
    assert len(data["sources"]) > 0
    
    # Delete the document
    delete_response = client.delete(f"/api/v1/document/{document_id}")
    assert delete_response.status_code == 200
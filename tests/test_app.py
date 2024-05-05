from fastapi.testclient import TestClient

from DTGBot.fapi.app import app

client = TestClient(app)


def test_read_main():
    response = client.get('/eps/')
    assert response.status_code == 200
    ...

from fastapi.testclient import TestClient

from app.main import app


def test_local_frontend_preflight():
    with TestClient(app) as client:
        for origin in ("http://127.0.0.1:5173", "http://localhost:5173"):
            response = client.options("/api/v1/auth/login", headers={
                "Origin": origin, "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,authorization",
            })
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin
            assert "access-control-allow-credentials" not in response.headers


def test_other_origins_and_methods_rejected():
    with TestClient(app) as client:
        response = client.options("/api/v1/auth/login", headers={
            "Origin": "https://untrusted.example", "Access-Control-Request-Method": "POST",
        })
        assert response.status_code == 400
        assert "access-control-allow-origin" not in response.headers
        response = client.options("/api/v1/users/1", headers={
            "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "DELETE",
        })
        assert response.status_code == 400

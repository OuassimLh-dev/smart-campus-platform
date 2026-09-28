import pytest
from app.models import UserRole


def test_admin_lists_profiles_with_pagination(client, academic_setup):
    setup = academic_setup
    headers = setup["admin_headers"]
    profiles = client.get("/api/v1/professors", headers=headers).json()
    assert [profile["id"] for profile in profiles] == [setup["professor"].id, setup["other_professor"].id]
    assert profiles[0]["employee_number"] == setup["professor"].employee_number
    assert profiles[0]["user_id"] == setup["professor"].user_id
    page = client.get("/api/v1/professors?skip=1&limit=1", headers=headers)
    assert page.status_code == 200
    assert page.json() == profiles[1:]
    assert client.get("/api/v1/professors?skip=2", headers=headers).json() == []


@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.PROFESSOR])
def test_profile_listing_admin_only(client, make_actor, role):
    _, headers = make_actor(role)
    assert client.get("/api/v1/professors", headers=headers).status_code == 403


def test_profile_listing_requires_authentication(client):
    assert client.get("/api/v1/professors").status_code == 401


@pytest.mark.parametrize("query", ["skip=-1", "limit=0", "limit=101"])
def test_profile_listing_validates_pagination(client, admin_headers, query):
    assert client.get(f"/api/v1/professors?{query}", headers=admin_headers).status_code == 422

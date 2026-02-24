import copy
import pytest
from fastapi.testclient import TestClient

from src import app as _app_module

# Use the same app instance for testing
client = TestClient(_app_module.app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Backup and restore the in-memory activities dict around each test."""
    original = copy.deepcopy(_app_module.activities)
    yield
    _app_module.activities.clear()
    _app_module.activities.update(original)


def test_get_root_redirects():
    # Arrange - nothing special

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_dictionary():
    # Arrange

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    # a few known keys should be present
    assert "Chess Club" in body
    assert "Programming Class" in body


def test_signup_success_and_duplicate():
    # Arrange
    activity = "Chess Club"
    email = "newuser@mergington.edu"
    assert email not in _app_module.activities[activity]["participants"]

    # Act
    resp1 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert successful signup
    assert resp1.status_code == 200
    assert email in _app_module.activities[activity]["participants"]
    assert resp1.json()["message"] == f"Signed up {email} for {activity}"

    # Arrange duplicate signup
    # Act
    resp2 = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert failure on duplicate
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Student already signed up"


def test_signup_nonexistent_activity():
    # Arrange
    activity = "NonExistent"
    email = "foo@bar.com"

    # Act
    resp = client.post(f"/activities/{activity}/signup", params={"email": email})

    # Assert 404
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"


def test_unregister_success_and_not_registered():
    # Arrange
    activity = "Programming Class"
    email = "temp@mergington.edu"
    # ensure the participant is present
    if email not in _app_module.activities[activity]["participants"]:
        _app_module.activities[activity]["participants"].append(email)

    # Act
    resp1 = client.post(f"/activities/{activity}/unregister", params={"email": email})

    # Assert success
    assert resp1.status_code == 200
    assert email not in _app_module.activities[activity]["participants"]
    assert resp1.json()["message"] == f"{email} unregistered from {activity}"

    # Arrange not registered
    # Act
    resp2 = client.post(f"/activities/{activity}/unregister", params={"email": email})

    # Assert failure
    assert resp2.status_code == 400
    assert resp2.json()["detail"] == "Participant not registered"


def test_unregister_nonexistent_activity():
    # Arrange
    activity = "NotHere"
    email = "whatever@dot.com"

    # Act
    resp = client.post(f"/activities/{activity}/unregister", params={"email": email})

    # Assert 404
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Activity not found"

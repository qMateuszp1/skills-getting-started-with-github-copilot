import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Response contains all activities with correct structure"""
        response = client.get("/activities")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        
        # Verify activity structure
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_participants_list_is_not_empty(self, client, reset_activities):
        """Arrange: Client is ready
        Act: Make GET request to /activities
        Assert: Participants list exists and contains emails"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert isinstance(activity["participants"], list)
        assert len(activity["participants"]) > 0
        assert "michael@mergington.edu" in activity["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, reset_activities):
        """Arrange: New student email and existing activity
        Act: POST signup request
        Assert: Student is added to participants"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]

    def test_signup_with_nonexistent_activity(self, client, reset_activities):
        """Arrange: Nonexistent activity name
        Act: POST signup request to invalid activity
        Assert: Returns 404 error"""
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_registration(self, client, reset_activities):
        """Arrange: Student already signed up for activity
        Act: POST signup request with same email twice
        Assert: Second request returns 400 error"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # First request should fail since already signed up
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_multiple_students_same_activity(self, client, reset_activities):
        """Arrange: Multiple new student emails
        Act: POST signup requests for same activity
        Assert: All students are added"""
        activity = "Drama Club"
        email1 = "student1@mergington.edu"
        email2 = "student2@mergington.edu"
        
        response1 = client.post(f"/activities/{activity}/signup?email={email1}")
        response2 = client.post(f"/activities/{activity}/signup?email={email2}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        assert email1 in participants
        assert email2 in participants


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Arrange: Student is registered for activity
        Act: DELETE unregister request
        Assert: Student is removed from participants"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Arrange: Nonexistent activity name
        Act: DELETE unregister request
        Assert: Returns 404 error"""
        email = "student@mergington.edu"
        activity = "Nonexistent Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_not_signed_up(self, client, reset_activities):
        """Arrange: Student not signed up for activity
        Act: DELETE unregister request
        Assert: Returns 400 error"""
        email = "notstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Arrange: Student is registered then unregistered
        Act: Sign up again for same activity
        Assert: Student can re-register successfully"""
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Register again
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify is registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_full_signup_and_unregister_workflow(self, client, reset_activities):
        """Arrange: Student and activity
        Act: Signup, verify in list, unregister
        Assert: All operations succeed and reflect in data"""
        email = "workflow@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Check participant count
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity]["participants"]
        count_before = len(activities_before[activity]["participants"])
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Verify participant count decreased
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity]["participants"]
        count_after = len(activities_after[activity]["participants"])
        assert count_after == count_before - 1

"""Tests for the activities API endpoints."""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_all_activities_returns_success(self, client, reset_activities):
        """Test that GET /activities returns all activities with correct structure."""
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify structure of activity objects
        for activity_name, activity_details in activities.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)
    
    def test_get_activities_contains_expected_activities(self, client, reset_activities):
        """Test that response contains expected activities."""
        # Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball",
            "Tennis Club",
            "Drama Club",
            "Art Studio",
            "Debate Team",
            "Science Club",
        ]
        for activity in expected_activities:
            assert activity in activities


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_valid_email_and_activity(self, client, reset_activities):
        """Test successful signup with valid email and activity."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """Test that signup actually adds participant to activity list."""
        # Arrange
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        # Act
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        
        # Assert
        activities = response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup fails with 404 for non-existent activity."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_already_registered(self, client, reset_activities):
        """Test signup fails with 400 if student already registered."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_different_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple different activities."""
        # Arrange
        email = "versatile@mergington.edu"
        activities_to_join = ["Chess Club", "Programming Class"]
        
        # Act & Assert for each activity
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify both signups worked
        response = client.get("/activities")
        all_activities = response.json()
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test successful unregister removes participant from activity."""
        # Arrange
        email = "michael@mergington.edu"  # Already in Chess Club
        activity = "Chess Club"
        
        # Verify participant is there
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregister fails with 404 for non-existent activity."""
        # Arrange
        email = "student@mergington.edu"
        activity = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_found(self, client, reset_activities):
        """Test unregister fails with 400 if participant not in activity."""
        # Arrange
        email = "notregistered@mergington.edu"
        activity = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_does_not_affect_other_participants(self, client, reset_activities):
        """Test that unregistering one participant doesn't affect others."""
        # Arrange
        activity = "Chess Club"
        response = client.get("/activities")
        original_participants = response.json()[activity]["participants"].copy()
        participant_to_remove = original_participants[0]
        other_participants = original_participants[1:]
        
        # Act
        client.post(
            f"/activities/{activity}/unregister?email={participant_to_remove}"
        )
        
        # Assert
        response = client.get("/activities")
        remaining_participants = response.json()[activity]["participants"]
        
        # Removed participant should be gone
        assert participant_to_remove not in remaining_participants
        
        # Other participants should still be there
        for participant in other_participants:
            assert participant in remaining_participants


class TestIntegration:
    """Integration tests combining signup and unregister."""
    
    def test_signup_then_unregister_workflow(self, client, reset_activities):
        """Test complete workflow of signup followed by unregister."""
        # Arrange
        email = "integration@mergington.edu"
        activity = "Programming Class"
        
        # Act: Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Act: Unregister
        unregister_response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert unregister_response.status_code == 200
        
        # Assert: Verify removal
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
    
    def test_signup_unregister_signup_again(self, client, reset_activities):
        """Test that a student can signup after unregistering."""
        # Arrange
        email = "flexibility@mergington.edu"
        activity = "Tennis Club"
        
        # Act & Assert: First signup
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Act: Unregister
        response = client.post(
            f"/activities/{activity}/unregister?email={email}"
        )
        assert response.status_code == 200
        
        # Act & Assert: Sign up again
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify final state
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]

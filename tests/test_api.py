"""
Test module for FastAPI Mergington High School Activities API.

This module contains comprehensive tests for all API endpoints including:
- Root endpoint
- Get activities endpoint
- Signup for activity endpoint
- Unregister from activity endpoint
"""

import pytest
from fastapi.testclient import TestClient
from src.app import activities
import copy


class TestRootEndpoint:
    """Test cases for the root endpoint."""
    
    def test_root_redirect(self, client):
        """Test that root endpoint redirects to static/index.html."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert "/static/index.html" in response.headers["location"]
    
    def test_root_redirect_followed(self, client):
        """Test that root endpoint serves the static HTML when redirect is followed."""
        response = client.get("/")  # TestClient follows redirects by default
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Mergington High School" in response.text


class TestGetActivities:
    """Test cases for the GET /activities endpoint."""
    
    def test_get_activities_success(self, client, reset_activities):
        """Test successful retrieval of activities."""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_structure(self, client, reset_activities):
        """Test that activities have the correct structure."""
        response = client.get("/activities")
        data = response.json()
        
        # Test a specific activity structure
        chess_club = data.get("Chess Club")
        assert chess_club is not None
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Test cases for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_success(self, client, reset_activities):
        """Test successful signup for an activity."""
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the student was actually added
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity."""
        email = "test@mergington.edu"
        activity_name = "Non-existent Activity"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_student(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity."""
        email = "michael@mergington.edu"  # Already registered for Chess Club
        activity_name = "Chess Club"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student already signed up for this activity"
    
    def test_signup_multiple_students(self, client, reset_activities):
        """Test signing up multiple new students for the same activity."""
        activity_name = "Chess Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
    
    def test_signup_special_characters_in_activity_name(self, client, reset_activities):
        """Test signup with URL-encoded activity names."""
        # Add a test activity with spaces
        activities["Test Activity"] = {
            "description": "Test activity",
            "schedule": "Test schedule",
            "max_participants": 10,
            "participants": []
        }
        
        email = "test@mergington.edu"
        activity_name = "Test Activity"
        
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Test cases for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_success(self, client, reset_activities):
        """Test successful unregistration from an activity."""
        email = "michael@mergington.edu"  # Already registered for Chess Club
        activity_name = "Chess Club"
        
        # Verify student is initially registered
        assert email in activities[activity_name]["participants"]
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        
        # Verify the student was actually removed
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """Test unregistration from non-existent activity."""
        email = "test@mergington.edu"
        activity_name = "Non-existent Activity"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 404
        
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_student_not_registered(self, client, reset_activities):
        """Test unregistration of student not registered for the activity."""
        email = "notregistered@mergington.edu"
        activity_name = "Chess Club"
        
        response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert response.status_code == 400
        
        data = response.json()
        assert data["detail"] == "Student is not registered for this activity"
    
    def test_unregister_all_students(self, client, reset_activities):
        """Test unregistering all students from an activity."""
        activity_name = "Chess Club"
        original_participants = activities[activity_name]["participants"].copy()
        
        # Unregister all students
        for email in original_participants:
            response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify activity has no participants
        assert len(activities[activity_name]["participants"]) == 0


class TestSignupUnregisterWorkflow:
    """Test cases for complete signup and unregister workflows."""
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test complete workflow of signing up and then unregistering."""
        email = "workflow@mergington.edu"
        activity_name = "Programming Class"
        
        # Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert signup_response.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Unregister
        unregister_response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
        assert unregister_response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_multiple_signups_and_unregisters(self, client, reset_activities):
        """Test multiple signups and unregisters for different activities."""
        email = "multisport@mergington.edu"
        activities_to_test = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Sign up for multiple activities
        for activity_name in activities_to_test:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
        
        # Unregister from all activities
        for activity_name in activities_to_test:
            response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert response.status_code == 200
            assert email not in activities[activity_name]["participants"]


class TestDataIntegrity:
    """Test cases for data integrity and edge cases."""
    
    def test_activities_remain_unchanged_after_failed_operations(self, client, reset_activities):
        """Test that failed operations don't modify the activities data."""
        # Store original state
        original_chess_participants = activities["Chess Club"]["participants"].copy()
        
        # Try to sign up existing student (should fail)
        response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")
        assert response.status_code == 400
        
        # Verify no changes were made
        assert activities["Chess Club"]["participants"] == original_chess_participants
        
        # Try to unregister non-existent student (should fail)
        response = client.delete("/activities/Chess Club/unregister?email=nonexistent@mergington.edu")
        assert response.status_code == 400
        
        # Verify no changes were made
        assert activities["Chess Club"]["participants"] == original_chess_participants
    
    def test_concurrent_operations_simulation(self, client, reset_activities):
        """Test simulated concurrent operations on the same activity."""
        activity_name = "Chess Club"
        original_count = len(activities[activity_name]["participants"])
        
        # Add multiple students
        emails = [f"concurrent{i}@mergington.edu" for i in range(5)]
        
        for email in emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            assert response.status_code == 200
        
        # Verify all were added
        assert len(activities[activity_name]["participants"]) == original_count + 5
        
        # Remove some students
        for email in emails[:3]:
            response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
            assert response.status_code == 200
        
        # Verify correct count
        assert len(activities[activity_name]["participants"]) == original_count + 2


class TestAPIResponseFormats:
    """Test cases for API response formats and content."""
    
    def test_content_type_headers(self, client, reset_activities):
        """Test that API returns correct content-type headers."""
        response = client.get("/activities")
        assert response.headers["content-type"] == "application/json"
        
        response = client.post("/activities/Chess Club/signup?email=test@mergington.edu")
        assert response.headers["content-type"] == "application/json"
    
    def test_response_json_structure(self, client, reset_activities):
        """Test the structure of JSON responses."""
        # Test signup response
        response = client.post("/activities/Chess Club/signup?email=jsontest@mergington.edu")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        
        # Test unregister response
        response = client.delete("/activities/Chess Club/unregister?email=jsontest@mergington.edu")
        data = response.json()
        assert isinstance(data, dict)
        assert "message" in data
        assert isinstance(data["message"], str)
        
        # Test error response
        response = client.post("/activities/Nonexistent/signup?email=test@mergington.edu")
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], str)
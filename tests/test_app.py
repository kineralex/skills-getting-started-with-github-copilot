"""
Comprehensive test suite for the Mergington High School API
Tests cover all endpoints with happy paths, error handling, edge cases, and data integrity
"""

import copy
from fastapi.testclient import TestClient
from src.app import app, activities


def reset_activities():
    """Reset activities to initial state"""
    initial_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Competitive soccer practices and matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 22,
            "participants": ["alex@mergington.edu"]
        },
        "Basketball Club": {
            "description": "Pickup games and skill development for basketball",
            "schedule": "Wednesdays and Fridays, 4:30 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Art Club": {
            "description": "Drawing, painting, and mixed media workshops",
            "schedule": "Mondays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["lily@mergington.edu"]
        },
        "Theater Group": {
            "description": "Acting, stagecraft, and school productions",
            "schedule": "Thursdays, 3:30 PM - 5:30 PM",
            "max_participants": 25,
            "participants": []
        },
        "Math Olympiad": {
            "description": "Advanced problem solving and competition prep",
            "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
            "max_participants": 12,
            "participants": ["noah@mergington.edu"]
        },
        "Debate Club": {
            "description": "Public speaking, argumentation, and debate tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 20,
            "participants": ["ava@mergington.edu"]
        }
    }
    # Clear and repopulate the activities dict
    activities.clear()
    activities.update(initial_activities)


client = TestClient(app)


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        reset_activities()
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9  # Should have 9 activities
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_returns_correct_structure(self):
        """Test that returned activities have correct structure"""
        reset_activities()
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity

    def test_get_activities_preserves_participant_list(self):
        """Test that participant lists are returned correctly"""
        reset_activities()
        response = client.get("/activities")
        data = response.json()
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]
        assert data["Basketball Club"]["participants"] == []


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_student_to_valid_activity(self):
        """Test successful signup to an activity"""
        reset_activities()
        response = client.post(
            "/activities/Basketball Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "newstudent@mergington.edu" in activities["Basketball Club"]["participants"]

    def test_signup_activity_not_found(self):
        """Test signup to non-existent activity returns 404"""
        reset_activities()
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_duplicate_email_returns_400(self):
        """Test that signing up same student twice returns 400"""
        reset_activities()
        # First signup
        response1 = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"}
        )
        assert response1.status_code == 400
        assert "already signed up" in response1.json()["detail"]

    def test_signup_multiple_students_same_activity(self):
        """Test multiple students can sign up for same activity"""
        reset_activities()
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"

        response1 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": student1}
        )
        response2 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": student2}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert student1 in activities["Basketball Club"]["participants"]
        assert student2 in activities["Basketball Club"]["participants"]
        assert len(activities["Basketball Club"]["participants"]) == 2

    def test_signup_participant_count_increments(self):
        """Test that participant count increments correctly"""
        reset_activities()
        initial_count = len(activities["Art Club"]["participants"])
        
        response = client.post(
            "/activities/Art Club/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert len(activities["Art Club"]["participants"]) == initial_count + 1

    def test_signup_multiple_activities_same_student(self):
        """Test that a student can sign up for multiple activities"""
        reset_activities()
        student = "multitask@mergington.edu"

        response1 = client.post(
            "/activities/Basketball Club/signup",
            params={"email": student}
        )
        response2 = client.post(
            "/activities/Art Club/signup",
            params={"email": student}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert student in activities["Basketball Club"]["participants"]
        assert student in activities["Art Club"]["participants"]


# ============================================================================
# DELETE /activities/{activity_name}/unregister Tests
# ============================================================================

class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_existing_participant(self):
        """Test successful unregistration from activity"""
        reset_activities()
        student = "michael@mergington.edu"
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student}
        )
        
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]
        assert student not in activities["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity returns 404"""
        reset_activities()
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_participant_not_found(self):
        """Test unregister non-existent participant returns 404"""
        reset_activities()
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notasignedupstudent@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_unregister_multiple_participants_same_activity(self):
        """Test unregistering multiple participants from same activity"""
        reset_activities()
        participant1 = "michael@mergington.edu"
        participant2 = "daniel@mergington.edu"

        response1 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": participant1}
        )
        response2 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": participant2}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert participant1 not in activities["Chess Club"]["participants"]
        assert participant2 not in activities["Chess Club"]["participants"]
        assert len(activities["Chess Club"]["participants"]) == 0

    def test_unregister_participant_count_decrements(self):
        """Test that participant count decrements correctly"""
        reset_activities()
        initial_count = len(activities["Chess Club"]["participants"])
        
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "michael@mergington.edu"}
        )
        
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1

    def test_unregister_cannot_unregister_twice(self):
        """Test that unregistering same participant twice fails on second attempt"""
        reset_activities()
        student = "michael@mergington.edu"

        # First unregister should succeed
        response1 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student}
        )
        assert response1.status_code == 200

        # Second unregister should fail
        response2 = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": student}
        )
        assert response2.status_code == 404
        assert "Participant not found" in response2.json()["detail"]


# ============================================================================
# Integration Tests (Combined Signup/Unregister Scenarios)
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_signup_then_unregister_same_activity(self):
        """Test signing up and then unregistering from same activity"""
        reset_activities()
        student = "tempstudent@mergington.edu"
        activity = "Basketball Club"

        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": student}
        )
        assert signup_response.status_code == 200
        assert student in activities[activity]["participants"]

        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": student}
        )
        assert unregister_response.status_code == 200
        assert student not in activities[activity]["participants"]

    def test_full_lifecycle_multiple_students(self):
        """Test full lifecycle: multiple signups, then multiple unregistrations"""
        reset_activities()
        activity = "Art Club"
        students = ["alice@mergington.edu", "bob@mergington.edu", "charlie@mergington.edu"]

        # Sign up all students
        for student in students:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": student}
            )
            assert response.status_code == 200

        initial_participants = len(activities[activity]["participants"])

        # Unregister some students
        for student in students[:2]:
            response = client.delete(
                f"/activities/{activity}/unregister",
                params={"email": student}
            )
            assert response.status_code == 200

        # Verify only one student remains
        final_participants = len(activities[activity]["participants"])
        assert final_participants == initial_participants - 2
        assert students[2] in activities[activity]["participants"]
        assert students[0] not in activities[activity]["participants"]
        assert students[1] not in activities[activity]["participants"]

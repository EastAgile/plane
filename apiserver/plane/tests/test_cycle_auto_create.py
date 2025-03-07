# Python Imports
from datetime import datetime, timedelta
import uuid

# Django Imports
from django.test import TestCase
from django.utils import timezone

# Third Party Imports
from rest_framework.test import APIClient

# Module Imports
from plane.db.models import (
    User,
    Workspace,
    Project,
    Cycle,
)
from plane.bgtasks.cycle_auto_create_task import auto_create_next_cycle


class CycleAutoCreateTest(TestCase):
    """Test case for auto-creating cycles"""

    def setUp(self):
        """Set up test data"""
        # Create a user
        self.user = User.objects.create(
            email="test@example.com",
            username="test",
            password="test",
            first_name="Test",
            last_name="User",
        )

        # Create a workspace
        self.workspace = Workspace.objects.create(
            name="Test Workspace",
            slug="test-workspace",
            owner=self.user,
        )

        # Create a project
        self.project = Project.objects.create(
            name="Test Project",
            workspace=self.workspace,
            project_lead=self.user,
            identifier="TEST",
            default_assignee=self.user,
        )

        # Define dates
        today = timezone.now().date()
        self.past_date = today - timedelta(days=5)
        self.tomorrow = today + timedelta(days=1)
        self.future_date = today + timedelta(days=10)

        # Convert to datetime for cycle fields
        self.past_datetime = datetime.combine(self.past_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        self.tomorrow_datetime = datetime.combine(self.tomorrow, datetime.max.time(), tzinfo=timezone.get_current_timezone())
        self.future_datetime = datetime.combine(self.future_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())

    def test_auto_create_cycle_when_ending_tomorrow(self):
        """Test that a new cycle is created when current cycle ends tomorrow and no upcoming cycle exists"""
        # Create a cycle that is active and ends tomorrow
        ending_cycle = Cycle.objects.create(
            name="Ending Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.past_datetime,
            end_date=self.tomorrow_datetime,
            team_strength=1.0,
        )

        # Run the auto-create task
        auto_create_next_cycle()

        # Check that a new cycle was created
        self.assertEqual(Cycle.objects.count(), 2)

        # Get the new cycle (the one that's not the ending cycle)
        new_cycle = Cycle.objects.exclude(id=ending_cycle.id).first()

        # Verify the new cycle has correct values
        self.assertIsNotNone(new_cycle)
        self.assertEqual(new_cycle.project, self.project)
        self.assertEqual(new_cycle.owned_by, self.user)
        self.assertEqual(new_cycle.team_strength, ending_cycle.team_strength)

        # Verify the dates are correct (should start after ending cycle ends)
        expected_start_date = self.tomorrow + timedelta(days=1)
        self.assertEqual(new_cycle.start_date.date(), expected_start_date)

        # Duration should be the same as the ending cycle
        ending_cycle_duration = (ending_cycle.end_date.date() - ending_cycle.start_date.date()).days + 1
        expected_end_date = expected_start_date + timedelta(days=ending_cycle_duration - 1)
        self.assertEqual(new_cycle.end_date.date(), expected_end_date)

    def test_no_cycle_created_when_upcoming_exists(self):
        """Test that no new cycle is created when there's already an upcoming cycle"""
        # Create a cycle that is active and ends tomorrow
        ending_cycle = Cycle.objects.create(
            name="Ending Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.past_datetime,
            end_date=self.tomorrow_datetime,
            team_strength=1.0,
        )

        # Create an upcoming cycle for the same project
        upcoming_cycle = Cycle.objects.create(
            name="Upcoming Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.future_datetime,
            end_date=self.future_datetime + timedelta(days=5),
            team_strength=1.0,
        )

        # Run the auto-create task
        auto_create_next_cycle()

        # Check that no new cycle was created (should still be 2 cycles)
        self.assertEqual(Cycle.objects.count(), 2)

    def test_no_cycle_created_when_not_ending_tomorrow(self):
        """Test that no new cycle is created for cycles not ending tomorrow"""
        # Create a cycle that is active but doesn't end tomorrow
        active_cycle = Cycle.objects.create(
            name="Active Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.past_datetime,
            end_date=self.past_datetime + timedelta(days=10),  # Ends in the future, but not tomorrow
            team_strength=1.0,
        )

        # Run the auto-create task
        auto_create_next_cycle()

        # Check that no new cycle was created (should still be just 1 cycle)
        self.assertEqual(Cycle.objects.count(), 1)

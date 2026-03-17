# Python Imports
from datetime import datetime, timedelta

# Django Imports
from django.test import TestCase
from django.utils import timezone

# Module Imports
from plane.db.models import (
    User,
    Workspace,
    Project,
    Cycle,
    Issue,
    State,
    CycleIssue,
)
from plane.bgtasks.cycle_issue_transfer_task import (
    auto_transfer_unfinished_cycle_issues,
)


class CycleIssueTransferTest(TestCase):
    """Test case for auto-transferring unfinished issues from completed cycles"""

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
        self.yesterday = today - timedelta(days=1)
        self.future_date = today + timedelta(days=10)

        # Convert to datetime for cycle fields
        tz = timezone.get_current_timezone()
        self.past_datetime = datetime.combine(
            self.past_date, datetime.min.time(), tzinfo=tz
        )
        self.yesterday_end = datetime.combine(
            self.yesterday, datetime.max.time(), tzinfo=tz
        )
        self.future_datetime = datetime.combine(
            self.future_date, datetime.min.time(), tzinfo=tz
        )

        # Create states for different groups
        self.backlog_state = State.objects.create(
            name="Backlog",
            group="backlog",
            project=self.project,
            workspace=self.workspace,
        )
        
        self.started_state = State.objects.create(
            name="In Progress",
            group="started",
            project=self.project,
            workspace=self.workspace,
        )
        
        self.unstarted_state = State.objects.create(
            name="To Do",
            group="unstarted",
            project=self.project,
            workspace=self.workspace,
        )
        
        self.completed_state = State.objects.create(
            name="Completed",
            group="completed",
            project=self.project,
            workspace=self.workspace,
        )
        
        self.cancelled_state = State.objects.create(
            name="Cancelled",
            group="cancelled",
            project=self.project,
            workspace=self.workspace,
        )

    def test_auto_transfer_unfinished_issues(self):
        """Test unfinished issues are auto-transferred when
        a cycle ends."""
        # Create a cycle that ended yesterday
        ended_cycle = Cycle.objects.create(
            name="Ended Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.past_datetime,
            end_date=self.yesterday_end,
            team_strength=1.0,
        )
        
        # Create a next cycle
        next_cycle = Cycle.objects.create(
            name="Next Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=10),
            team_strength=1.0,
        )
        
        # Create issues in different states
        backlog_issue = Issue.objects.create(
            name="Backlog Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.backlog_state,
            created_by=self.user,
        )
        
        started_issue = Issue.objects.create(
            name="Started Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.started_state,
            created_by=self.user,
        )
        
        unstarted_issue = Issue.objects.create(
            name="Unstarted Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.unstarted_state,
            created_by=self.user,
        )
        
        completed_issue = Issue.objects.create(
            name="Completed Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.completed_state,
            created_by=self.user,
        )
        
        cancelled_issue = Issue.objects.create(
            name="Cancelled Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.cancelled_state,
            created_by=self.user,
        )
        
        # Add issues to the ended cycle
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=backlog_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=started_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=unstarted_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=completed_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=cancelled_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        # Run the auto transfer task
        auto_transfer_unfinished_cycle_issues()
        
        # Verify unfinished issues were moved to the next cycle
        self.assertTrue(
            CycleIssue.objects.filter(cycle=next_cycle, issue=backlog_issue).exists(),
            "Backlog issue should be transferred to the next cycle"
        )
        
        self.assertTrue(
            CycleIssue.objects.filter(cycle=next_cycle, issue=started_issue).exists(),
            "Started issue should be transferred to the next cycle"
        )
        
        self.assertTrue(
            CycleIssue.objects.filter(cycle=next_cycle, issue=unstarted_issue).exists(),
            "Unstarted issue should be transferred to the next cycle"
        )
        
        # Verify completed and cancelled issues remain in the original cycle
        self.assertTrue(
            CycleIssue.objects.filter(
                cycle=ended_cycle, issue=completed_issue
            ).exists(),
            "Completed issue should remain in the ended cycle",
        )

        self.assertTrue(
            CycleIssue.objects.filter(
                cycle=ended_cycle, issue=cancelled_issue
            ).exists(),
            "Cancelled issue should remain in the ended cycle",
        )
        
    def test_no_transfer_when_no_next_cycle(self):
        """Test that no issues are transferred when there's no next cycle"""
        # Create a cycle that ended yesterday, but no next cycle
        ended_cycle = Cycle.objects.create(
            name="Ended Cycle",
            project=self.project,
            workspace=self.workspace,
            owned_by=self.user,
            start_date=self.past_datetime,
            end_date=self.yesterday_end,
            team_strength=1.0,
        )
        
        # Create an unfinished issue
        backlog_issue = Issue.objects.create(
            name="Backlog Issue",
            project=self.project,
            workspace=self.workspace,
            state=self.backlog_state,
            created_by=self.user,
        )
        
        # Add issue to the ended cycle
        CycleIssue.objects.create(
            cycle=ended_cycle,
            issue=backlog_issue,
            project=self.project,
            workspace=self.workspace,
        )
        
        # Run the auto transfer task
        auto_transfer_unfinished_cycle_issues()
        
        # Verify the issue is still in the original cycle (no change)
        self.assertTrue(
            CycleIssue.objects.filter(cycle=ended_cycle, issue=backlog_issue).exists(),
            "Issue should remain in the original cycle when there's no next cycle"
        )
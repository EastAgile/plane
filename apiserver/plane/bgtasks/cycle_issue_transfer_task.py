# Python imports
import json
import logging
from datetime import datetime, timedelta

# Third party imports
from celery import shared_task

# Django imports
from django.utils import timezone
from django.db.models import Q

# Module imports
from plane.db.models import Cycle, CycleIssue, Issue
from plane.utils.exception_logger import log_exception
from plane.utils.velocity import update_project_velocity


@shared_task
def auto_transfer_unfinished_cycle_issues():
    """
    Task to automatically transfer unfinished issues from completed cycles to the next cycle.

    This task:
    1. Runs daily to find cycles that ended "yesterday"
    2. For each completed cycle, finds the next cycle for the same project
    3. Transfers all unfinished issues (backlog, unstarted, started) to the next cycle
    4. Updates the project velocity again

    This ensures work continuity is maintained without manual intervention.
    """
    try:
        # Get yesterday's date to identify cycles that just ended
        yesterday = timezone.now().date() - timedelta(days=1)
        yesterday_start = datetime.combine(yesterday, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        yesterday_end = datetime.combine(yesterday, datetime.max.time(), tzinfo=timezone.get_current_timezone())

        # Find all cycles that ended yesterday
        # These are cycles that were current but are now completed
        recently_completed_cycles = Cycle.objects.filter(
            # Filter for cycles that ended yesterday
            end_date__gte=yesterday_start,
            end_date__lte=yesterday_end,
            # Don't include archived cycles or projects
            archived_at__isnull=True,
            project__archived_at__isnull=True
        )

        # Track statistics for logging
        cycles_processed = 0
        issues_transferred = 0
        projects_without_next_cycle = 0

        for completed_cycle in recently_completed_cycles:
            project = completed_cycle.project

            # Find the next cycle for this project
            # Look for cycles that start on or after the completed cycle's end date
            next_cycle = Cycle.objects.filter(
                project_id=project.id,
                start_date__gte=completed_cycle.end_date,
                archived_at__isnull=True
            ).order_by('start_date').first()

            if not next_cycle:
                # No next cycle found for this project
                logging.info(
                    f"No next cycle found for project {project.name} (ID: {project.id}) "
                    f"after cycle {completed_cycle.name} (ID: {completed_cycle.id})"
                )
                projects_without_next_cycle += 1
                continue

            # Find all unfinished issues in the completed cycle
            # Filter for issues in states: backlog, unstarted, started
            cycle_issues = CycleIssue.objects.filter(
                cycle_id=completed_cycle.id,
                project_id=project.id,
                workspace__slug=completed_cycle.workspace.slug,
                issue__state__group__in=["backlog", "unstarted", "started"],
                deleted_at__isnull=True
            )

            if not cycle_issues.exists():
                # No unfinished issues to transfer
                logging.info(
                    f"No unfinished issues to transfer from cycle {completed_cycle.name} "
                    f"(ID: {completed_cycle.id}) in project {project.name} (ID: {project.id})"
                )
                cycles_processed += 1
                continue

            # Prepare for bulk update
            updated_cycles = []
            issue_ids = []
            current_time = timezone.now()

            for cycle_issue in cycle_issues:
                # Update cycle ID to the next cycle
                cycle_issue.cycle_id = next_cycle.id
                updated_cycles.append(cycle_issue)
                issue_ids.append(cycle_issue.issue_id)

            # Bulk update all cycle issues
            CycleIssue.objects.bulk_update(updated_cycles, ["cycle_id"], batch_size=100)

            # Also update the updated_at field on the issues to trigger cache refresh
            # Update all issues with one SQL query
            if issue_ids:
                Issue.objects.filter(id__in=issue_ids).update(updated_at=current_time)

            issues_transferred += len(updated_cycles)

            # Update project velocity after transferring issues
            update_project_velocity(project.id)

            logging.info(
                f"Transferred {len(updated_cycles)} unfinished issues from cycle {completed_cycle.name} "
                f"(ID: {completed_cycle.id}) to cycle {next_cycle.name} (ID: {next_cycle.id}) "
                f"in project {project.name} (ID: {project.id})"
            )
            cycles_processed += 1

        logging.info(
            f"Auto cycle issue transfer complete: {cycles_processed} cycles processed, "
            f"{issues_transferred} issues transferred, {projects_without_next_cycle} projects without next cycle"
        )
        return True
    except Exception as e:
        log_exception(e)
        logging.error(f"Unexpected error in auto_transfer_unfinished_cycle_issues: {str(e)}")
        return False

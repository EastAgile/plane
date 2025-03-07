# Python imports
import logging
from datetime import datetime, timedelta

# Third party imports
from celery import shared_task

# Django imports
from django.utils import timezone
from django.db.models import Q

# Module imports
from plane.db.models import Project, Cycle
from plane.app.serializers.cycle import CycleWriteSerializer
from plane.utils.exception_logger import log_exception
from plane.bgtasks.webhook_task import model_activity


@shared_task
def auto_create_next_cycle():
    """
    Task to automatically create the next cycle when a current cycle is ending.
    Runs daily and checks for cycles that are:
    1. Currently active (ending tomorrow)
    2. Have no upcoming cycle scheduled for that project
    3. Creates a new cycle with the same duration starting immediately after the current one

    This ensures project work can continue without manual intervention.
    """
    try:
        # Get tomorrow's date to identify cycles ending tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        tomorrow_start = datetime.combine(tomorrow, datetime.min.time(), tzinfo=timezone.get_current_timezone())
        tomorrow_end = datetime.combine(tomorrow, datetime.max.time(), tzinfo=timezone.get_current_timezone())

        # Find all active cycles that end tomorrow
        ending_cycles = Cycle.objects.filter(
            # Must be an active cycle ending tomorrow
            start_date__lte=timezone.now(),
            end_date__gte=tomorrow_start,
            end_date__lte=tomorrow_end,
            # Don't include archived cycles or projects
            archived_at__isnull=True,
            project__archived_at__isnull=True
        )

        cycles_created = 0
        for cycle in ending_cycles:
            project = cycle.project

            # Check if there's already an upcoming cycle for this project
            upcoming_cycle_exists = Cycle.objects.filter(
                project_id=project.id,
                start_date__gt=timezone.now(),
                archived_at__isnull=True
            ).exists()

            if upcoming_cycle_exists:
                # Skip this project as it already has an upcoming cycle
                continue

            # Calculate the new cycle duration based on the current one
            cycle_duration = (cycle.end_date.date() - cycle.start_date.date()).days + 1

            # New cycle starts the next day after current cycle ends
            new_start_date = cycle.end_date.date() + timedelta(days=1)
            # End date is calculated based on the same duration
            new_end_date = new_start_date + timedelta(days=cycle_duration - 1)

            # Format dates as datetime objects
            new_start_datetime = datetime.combine(new_start_date, datetime.min.time(), tzinfo=timezone.get_current_timezone())
            new_end_datetime = datetime.combine(new_end_date, datetime.max.time(), tzinfo=timezone.get_current_timezone())

            # Format the cycle name as "Iteration YYYY/MM/DD - YYYY/MM/DD"
            new_cycle_name = f"Iteration {new_start_date.strftime('%Y/%m/%d')} - {new_end_date.strftime('%Y/%m/%d')}"

            # Prepare data for new cycle
            cycle_data = {
                "name": new_cycle_name,
                "description": f"Auto-created cycle following {cycle.name}",
                "start_date": new_start_datetime,
                "end_date": new_end_datetime,
                "team_strength": cycle.team_strength,  # Maintain the same team strength
            }

            # Create new cycle using the serializer
            serializer = CycleWriteSerializer(data=cycle_data)
            if serializer.is_valid():
                # Create new cycle with the same owner as the previous cycle
                new_cycle = serializer.save(
                    project_id=project.id,
                    owned_by=cycle.owned_by,
                    workspace_id=cycle.workspace_id
                )

                # Trigger webhook for cycle creation
                model_activity.delay(
                    "cycle.activity.created",
                    new_cycle.id,
                    cycle.owned_by.id,
                    cycle.project_id,
                    cycle.workspace_id,
                    {
                        "cycle": {
                            "name": new_cycle.name,
                            "id": new_cycle.id,
                        }
                    }
                )

                cycles_created += 1
                logging.info(
                    f"Auto-created new cycle '{new_cycle_name}' for project {project.name} (ID: {project.id})"
                )
            else:
                logging.error(
                    f"Failed to create auto cycle for project {project.name} (ID: {project.id}): {serializer.errors}"
                )

        logging.info(f"Auto cycle creation complete: {cycles_created} new cycles created")
        return True
    except Exception as e:
        log_exception(e)
        logging.error(f"Unexpected error in auto_create_next_cycle: {str(e)}")
        return False

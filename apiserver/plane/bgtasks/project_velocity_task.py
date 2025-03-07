# Python imports
import logging

# Third party imports
from celery import shared_task

# Django imports
from django.utils import timezone

# Module imports
from plane.db.models import Project
from plane.utils.velocity import update_project_velocity
from plane.utils.exception_logger import log_exception


@shared_task
def recalculate_all_project_velocities():
    """
    Recalculate velocities for all non-archived projects.
    This task is scheduled to run daily to ensure project velocities are accurate,
    catching any velocities that might have been missed by triggers.
    """
    try:
        # Get all non-archived projects
        projects = Project.objects.filter(archived_at__isnull=True)

        success_count = 0
        error_count = 0

        for project in projects:
            try:
                if update_project_velocity(project.id):
                    success_count += 1
                else:
                    error_count += 1
                    logging.warning(f"Failed to update velocity for project {project.id} - {project.name}")
            except Exception as e:
                error_count += 1
                log_exception(e)
                logging.error(f"Error processing project {project.id}: {str(e)}")

        logging.info(
            f"Daily velocity recalculation complete: {success_count}/{projects.count()} projects updated successfully ({error_count} errors)"
        )
        return True
    except Exception as e:
        log_exception(e)
        logging.error(f"Unexpected error in recalculate_all_project_velocities: {str(e)}")
        return False

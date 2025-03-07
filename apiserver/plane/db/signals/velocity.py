# Django imports
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

# Project imports
from plane.db.models import Project, Cycle, CycleIssue, Issue
from plane.utils.velocity import update_project_velocity

@receiver(post_save, sender=Cycle)
def recalculate_velocity_on_cycle_update(sender, instance, created, **kwargs):
    """
    Recalculate project velocity when a cycle is updated.
    This covers the requirements:
    - Trigger a recalculate when a relevant cycle of the project is edited:
      team strength changed, or cycle is completed
    """
    # Only proceed if an existing cycle is updated (not created)
    if not created:
        # If the cycle is now completed (end date is in the past)
        if instance.end_date and instance.end_date < timezone.now():
            # Update the project's velocity
            update_project_velocity(instance.project_id)

@receiver(post_save, sender=Project)
def recalculate_velocity_on_project_update(sender, instance, created, **kwargs):
    """
    Recalculate project velocity when relevant project settings change.
    This covers the requirements:
    - Trigger a recalculate when relevant project settings change:
      cycle length, velocity strategy
    """
    # Don't process newly created projects
    if not created:
        # Update velocity for the project
        update_project_velocity(instance.id)

@receiver(post_save, sender=CycleIssue)
def recalculate_velocity_on_cycle_issue_update(sender, instance, created, **kwargs):
    """
    Recalculate project velocity when issues are added to or removed from a cycle
    """
    # Get the cycle
    cycle = instance.cycle

    # Only recalculate if the cycle is already completed
    if cycle.end_date and cycle.end_date < timezone.now():
        # Update the project's velocity
        update_project_velocity(cycle.project_id)


# Update velocity when any issue is updated with new estimate points
@receiver(post_save, sender=Issue)
def recalculate_velocity_on_issue_update(sender, instance, created, **kwargs):
    """
    Recalculate project velocity when issues are updated with new estimate points
    """
    # Get the cycle issue
    cycle_issue = CycleIssue.objects.filter(issue=instance).first()

    # Only recalculate if the cycle is already completed
    if cycle_issue and cycle_issue.cycle.end_date and cycle_issue.cycle.end_date < timezone.now():
        # Update the project's velocity
        update_project_velocity(cycle_issue.cycle.project_id)

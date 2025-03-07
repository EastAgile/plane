# Python imports
import math
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, FloatField
from django.db.models.functions import Cast
from uuid import UUID

# Import models from our app
from plane.db.models import Project, Cycle, CycleIssue, Issue


def calculate_cycle_length_in_weeks(cycle):
    """
    Calculate the length of a cycle in weeks (rounded up to the nearest week)
    """
    if not cycle.start_date or not cycle.end_date:
        return None

    # Calculate the difference in days
    delta = cycle.end_date - cycle.start_date
    # Convert to weeks and round up to the nearest week
    weeks = math.ceil(delta.days / 7)
    return max(1, weeks)  # Ensure at least 1 week


def calculate_cycle_points(cycle):
    """
    Calculate the total points of completed issues in a cycle
    """
    # Find completed issues in the cycle
    points = CycleIssue.objects.filter(
        cycle=cycle,
        deleted_at__isnull=True,
        issue__state__group="completed",
        issue__archived_at__isnull=True,
        issue__is_draft=False,
        issue__deleted_at__isnull=True
    ).aggregate(
        total_points=Sum(
            Cast('issue__estimate_point__value', FloatField()),
            filter=Q(issue__estimate_point__isnull=False)
        )
    )['total_points'] or 0

    return points


def calculate_project_velocity(project_id):
    """
    Calculate project velocity based on completed cycles using the formula:
    SUM(cycle_points / cycle_team_strength) / SUM(cycle_length_in_weeks)

    This follows the acceptance criteria:
    - cycle points is total points of issues in the cycle
    - team strength is a field of cycle
    - velocity strategy is taken from the project
    - cycle length is calculated per each cycle's start and end date (round to week)
    """
    try:
        project = Project.objects.get(id=project_id)

        # Get velocity strategy from project
        velocity_strategy = project.velocity_strategy

        # Find completed cycles, ordered by end date (most recent first)
        completed_cycles = Cycle.objects.filter(
            project_id=project_id,
            start_date__isnull=False,
            end_date__isnull=False,
            end_date__lt=timezone.now(),  # Only completed cycles
            team_strength__gt=0,  # Exclude cycles with 0% team strength
            archived_at__isnull=True,
        ).order_by('-end_date')

        # Take only the number of cycles defined by velocity_strategy
        cycles_to_consider = completed_cycles[:velocity_strategy]

        if not cycles_to_consider:
            # If no cycles have been completed, use initial velocity
            return project.initial_velocity

        total_adjusted_points = 0
        total_weeks = 0

        for cycle in cycles_to_consider:
            cycle_points = calculate_cycle_points(cycle)
            cycle_length = calculate_cycle_length_in_weeks(cycle)

            if cycle_length is None or cycle.team_strength == 0:
                continue  # Skip cycles with no dates or zero team strength

            # Adjust points by team strength
            adjusted_points = cycle_points / cycle.team_strength

            total_adjusted_points += adjusted_points
            total_weeks += cycle_length

        if total_weeks == 0:
            # If we couldn't calculate weeks for any reason, return initial velocity
            return project.initial_velocity

        # Calculate velocity as points per cycle length
        velocity = total_adjusted_points / total_weeks

        # Adjust to the project's default cycle length
        velocity = velocity * project.default_cycle_length

        # Round down to the nearest integer as per requirements
        print(f"Velocity for project {project_id}: {velocity}")
        return math.floor(velocity)

    except Project.DoesNotExist:
        return None
    except Exception as e:
        # Log the error
        print(f"Error calculating velocity for project {project_id}: {str(e)}")
        return None


def update_project_velocity(project_id):
    """
    Calculate and update a project's current_velocity
    """
    try:
        # Calculate the velocity
        velocity = calculate_project_velocity(project_id)

        if velocity is not None:
            # Update the project directly without loading the entire object
            Project.objects.filter(id=project_id).update(current_velocity=velocity)
            return True

        return False

    except Project.DoesNotExist:
        return False
    except Exception as e:
        # Log the error
        print(f"Error updating velocity for project {project_id}: {str(e)}")
        return False

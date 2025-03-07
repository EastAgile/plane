# Django imports
from django.core.management.base import BaseCommand
from tqdm import tqdm
import traceback
import sys

# Project imports
from plane.db.models import Project
from plane.utils.velocity import update_project_velocity


class Command(BaseCommand):
    help = 'Recalculates velocity for all projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            dest='project_id',
            help='Specific project ID to recalculate velocity for',
        )
        parser.add_argument(
            '--debug',
            action='store_true',
            help='Enable detailed debug output',
        )

    def handle(self, *args, **kwargs):
        try:
            project_id = kwargs.get('project_id')
            debug_mode = kwargs.get('debug', False)
            
            if project_id:
                # Process a single project
                try:
                    project = Project.objects.get(id=project_id)
                    self.stdout.write(f"Recalculating velocity for project: {project.name} ({project_id})")
                    
                    success = update_project_velocity(project_id)
                    
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"Successfully updated velocity for project {project.name}"))
                    else:
                        self.stdout.write(self.style.ERROR(f"Failed to update velocity for project {project.name}"))
                    
                    # Print the new velocity value
                    project.refresh_from_db()
                    self.stdout.write(f"New velocity value: {project.current_velocity}")
                    
                except Project.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"Project with ID {project_id} does not exist"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing project {project_id}: {str(e)}"))
                    if debug_mode:
                        traceback.print_exc(file=sys.stdout)
            else:
                # Process all non-archived projects
                projects = Project.objects.filter(archived_at__isnull=True)
                total = projects.count()
                
                self.stdout.write(f"Recalculating velocity for {total} projects")
                
                success_count = 0
                error_count = 0
                
                for project in tqdm(projects, total=total):
                    try:
                        if update_project_velocity(project.id):
                            success_count += 1
                        else:
                            error_count += 1
                            if debug_mode:
                                self.stdout.write(self.style.WARNING(f"Failed to update velocity for project {project.id} - {project.name}"))
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f"Error processing project {project.id}: {str(e)}"))
                        if debug_mode:
                            traceback.print_exc(file=sys.stdout)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Recalculated velocity for {success_count}/{total} projects ({error_count} errors)"
                    )
                )
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("Operation cancelled by user"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Unexpected error: {str(e)}"))
            traceback.print_exc(file=sys.stdout)
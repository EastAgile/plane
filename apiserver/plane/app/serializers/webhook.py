# Python imports
import socket
import ipaddress
from urllib.parse import urlparse

# Third party imports
from rest_framework import serializers

# Module imports
from .base import DynamicBaseSerializer
from plane.db.models import Webhook, WebhookLog, WebhookProject, Project
from plane.db.models.webhook import validate_domain, validate_schema


class WebhookSerializer(DynamicBaseSerializer):
    url = serializers.URLField(validators=[validate_schema, validate_domain])
    project_type = serializers.ChoiceField(choices=['all', 'individual'], required=False)
    selected_projects = serializers.ListField(child=serializers.UUIDField(), required=False)

    def _handle_webhook_projects(self, webhook, workspace_id, project_type, selected_projects):
        """Helper method to handle webhook project relationships"""
        # Delete existing webhook projects if any
        if hasattr(webhook, 'webhook_projects'):
            webhook.webhook_projects.all().delete()

        # Create new webhook project relationships if needed
        if selected_projects:
            projects = Project.objects.filter(
                id__in=selected_projects,
                workspace_id=workspace_id
            )
            webhook_projects = [
                WebhookProject(
                    webhook=webhook,
                    project=project,
                    workspace_id=workspace_id
                )
                for project in projects
            ]
            WebhookProject.objects.bulk_create(webhook_projects)

    def create(self, validated_data):
        url = validated_data.get("url", None)

        # Extract the hostname from the URL
        hostname = urlparse(url).hostname
        if not hostname:
            raise serializers.ValidationError(
                {"url": "Invalid URL: No hostname found."}
            )

        # Resolve the hostname to IP addresses
        try:
            ip_addresses = socket.getaddrinfo(hostname, None)
        except socket.gaierror:
            raise serializers.ValidationError(
                {"url": "Hostname could not be resolved."}
            )

        if not ip_addresses:
            raise serializers.ValidationError(
                {"url": "No IP addresses found for the hostname."}
            )

        for addr in ip_addresses:
            ip = ipaddress.ip_address(addr[4][0])
            if ip.is_loopback:
                raise serializers.ValidationError(
                    {"url": "URL resolves to a blocked IP address."}
                )

        # Additional validation for multiple request domains and their subdomains
        request = self.context.get("request")
        disallowed_domains = ["plane.so"]  # Add your disallowed domains here
        if request:
            request_host = request.get_host().split(":")[0]  # Remove port if present
            disallowed_domains.append(request_host)

        # Check if hostname is a subdomain or exact match of any disallowed domain
        if any(
            hostname == domain or hostname.endswith("." + domain)
            for domain in disallowed_domains
        ):
            raise serializers.ValidationError(
                {"url": "URL domain or its subdomain is not allowed."}
            )

        # Handle project type and selected projects
        project_type = validated_data.pop('project_type', 'all')
        selected_projects = validated_data.pop('selected_projects', [])

        # Set is_workspace_wide based on project_type
        validated_data['is_workspace_wide'] = (project_type == 'all')

        # Create the webhook
        webhook = Webhook.objects.create(**validated_data)

        # Handle webhook project relationships
        self._handle_webhook_projects(
            webhook=webhook,
            workspace_id=validated_data['workspace_id'],
            project_type=project_type,
            selected_projects=selected_projects
        )

        return webhook

    def update(self, instance, validated_data):
        url = validated_data.get("url", None)
        if url:
            # Extract the hostname from the URL
            hostname = urlparse(url).hostname
            if not hostname:
                raise serializers.ValidationError(
                    {"url": "Invalid URL: No hostname found."}
                )

            # Resolve the hostname to IP addresses
            try:
                ip_addresses = socket.getaddrinfo(hostname, None)
            except socket.gaierror:
                raise serializers.ValidationError(
                    {"url": "Hostname could not be resolved."}
                )

            if not ip_addresses:
                raise serializers.ValidationError(
                    {"url": "No IP addresses found for the hostname."}
                )

            for addr in ip_addresses:
                ip = ipaddress.ip_address(addr[4][0])
                if ip.is_loopback:
                    raise serializers.ValidationError(
                        {"url": "URL resolves to a blocked IP address."}
                    )

            # Additional validation for multiple request domains and their subdomains
            request = self.context.get("request")
            disallowed_domains = ["plane.so"]  # Add your disallowed domains here
            if request:
                request_host = request.get_host().split(":")[
                    0
                ]  # Remove port if present
                disallowed_domains.append(request_host)

            # Check if hostname is a subdomain or exact match of any disallowed domain
            if any(
                hostname == domain or hostname.endswith("." + domain)
                for domain in disallowed_domains
            ):
                raise serializers.ValidationError(
                    {"url": "URL domain or its subdomain is not allowed."}
                )

        # Handle project type and selected projects
        project_type = validated_data.pop('project_type', None)
        selected_projects = validated_data.pop('selected_projects', None)

        if project_type is not None:
            # Update is_workspace_wide based on project_type
            validated_data['is_workspace_wide'] = (project_type == 'all')

            # Handle webhook project relationships
            self._handle_webhook_projects(
                webhook=instance,
                workspace_id=instance.workspace_id,
                project_type=project_type,
                selected_projects=selected_projects or []
            )

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add project_type and selected_projects to the response
        data['project_type'] = 'all' if instance.is_workspace_wide else 'individual'
        data['selected_projects'] = list(
            instance.webhook_projects.filter(deleted_at__isnull=True)
            .values_list('project_id', flat=True)
        )
        return data

    class Meta:
        model = Webhook
        fields = "__all__"
        read_only_fields = ["workspace", "secret_key"]


class WebhookLogSerializer(DynamicBaseSerializer):
    class Meta:
        model = WebhookLog
        fields = "__all__"
        read_only_fields = ["workspace", "webhook"]

import hashlib
import hmac
import json
import logging
import uuid

import requests

# Third party imports
from celery import shared_task

# Django imports
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.exceptions import ObjectDoesNotExist
from django.utils.html import strip_tags
from django.db.models import Q

# Module imports
from plane.api.serializers import (
    CycleIssueSerializer,
    CycleSerializer,
    IssueCommentSerializer,
    IssueExpandSerializer,
    ModuleIssueSerializer,
    ModuleSerializer,
    ProjectSerializer,
    UserLiteSerializer,
    IntakeIssueSerializer,
)
from plane.db.models import (
    Cycle,
    CycleIssue,
    Issue,
    IssueComment,
    Module,
    ModuleIssue,
    Project,
    User,
    Webhook,
    WebhookLog,
    IntakeIssue,
)
from plane.license.utils.instance_value import get_email_configuration
from plane.utils.exception_logger import log_exception

SERIALIZER_MAPPER = {
    "project": ProjectSerializer,
    "issue": IssueExpandSerializer,
    "cycle": CycleSerializer,
    "module": ModuleSerializer,
    "cycle_issue": CycleIssueSerializer,
    "module_issue": ModuleIssueSerializer,
    "issue_comment": IssueCommentSerializer,
    "user": UserLiteSerializer,
    "intake_issue": IntakeIssueSerializer,
}

MODEL_MAPPER = {
    "project": Project,
    "issue": Issue,
    "cycle": Cycle,
    "module": Module,
    "cycle_issue": CycleIssue,
    "module_issue": ModuleIssue,
    "issue_comment": IssueComment,
    "user": User,
    "intake_issue": IntakeIssue,
}


def get_model_data(event, event_id, many=False):
    model = MODEL_MAPPER.get(event)
    if many:
        queryset = model.objects.filter(pk__in=event_id)
    else:
        queryset = model.objects.get(pk=event_id)
    serializer = SERIALIZER_MAPPER.get(event)
    return serializer(queryset, many=many).data


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=600,
    max_retries=5,
    retry_jitter=True,
)
def webhook_task(self, webhook, slug, event, event_data, action, current_site):
    try:
        webhook = Webhook.objects.get(id=webhook, workspace__slug=slug)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Autopilot",
            "X-Plane-Delivery": str(uuid.uuid4()),
            "X-Plane-Event": event,
        }

        # # Your secret key
        event_data = (
            json.loads(json.dumps(event_data, cls=DjangoJSONEncoder))
            if event_data is not None
            else None
        )

        action = {
            "POST": "create",
            "PATCH": "update",
            "PUT": "update",
            "DELETE": "delete",
        }.get(action, action)

        payload = {
            "event": event,
            "action": action,
            "webhook_id": str(webhook.id),
            "workspace_id": str(webhook.workspace_id),
            "data": event_data,
        }

        # Use HMAC for generating signature
        if webhook.secret_key:
            hmac_signature = hmac.new(
                webhook.secret_key.encode("utf-8"),
                json.dumps(payload).encode("utf-8"),
                hashlib.sha256,
            )
            signature = hmac_signature.hexdigest()
            headers["X-Plane-Signature"] = signature

        # Send the webhook event
        response = requests.post(webhook.url, headers=headers, json=payload, timeout=30)

        # Log the webhook request
        WebhookLog.objects.create(
            workspace_id=str(webhook.workspace_id),
            webhook_id=str(webhook.id),
            event_type=str(event),
            request_method=str(action),
            request_headers=str(headers),
            request_body=str(payload),
            response_status=str(response.status_code),
            response_headers=str(response.headers),
            response_body=str(response.text),
            retry_count=str(self.request.retries),
        )

    except Webhook.DoesNotExist:
        return
    except requests.RequestException as e:
        # Log the failed webhook request
        WebhookLog.objects.create(
            workspace_id=str(webhook.workspace_id),
            webhook_id=str(webhook.id),
            event_type=str(event),
            request_method=str(action),
            request_headers=str(headers),
            request_body=str(payload),
            response_status=500,
            response_headers="",
            response_body=str(e),
            retry_count=str(self.request.retries),
        )
        # Retry logic
        if self.request.retries >= self.max_retries:
            Webhook.objects.filter(pk=webhook.id).update(is_active=False)
            if webhook:
                # send email for the deactivation of the webhook
                send_webhook_deactivation_email(
                    webhook_id=webhook.id,
                    receiver_id=webhook.created_by_id,
                    reason=str(e),
                    current_site=current_site,
                )
            return
        raise requests.RequestException()

    except Exception as e:
        if settings.DEBUG:
            print(e)
        log_exception(e)
        return


@shared_task
def send_webhook_deactivation_email(webhook_id, receiver_id, current_site, reason):
    # Get email configurations
    (
        EMAIL_HOST,
        EMAIL_HOST_USER,
        EMAIL_HOST_PASSWORD,
        EMAIL_PORT,
        EMAIL_USE_TLS,
        EMAIL_USE_SSL,
        EMAIL_FROM,
    ) = get_email_configuration()

    receiver = User.objects.get(pk=receiver_id)
    webhook = Webhook.objects.get(pk=webhook_id)
    subject = "Webhook Deactivated"
    message = f"Webhook {webhook.url} has been deactivated due to failed requests."

    # Send the mail
    context = {
        "email": receiver.email,
        "message": message,
        "webhook_url": f"{current_site}/{str(webhook.workspace.slug)}/settings/webhooks/{str(webhook.id)}",
    }
    html_content = render_to_string(
        "emails/notifications/webhook-deactivate.html", context
    )
    text_content = strip_tags(html_content)

    try:
        connection = get_connection(
            host=EMAIL_HOST,
            port=int(EMAIL_PORT),
            username=EMAIL_HOST_USER,
            password=EMAIL_HOST_PASSWORD,
            use_tls=EMAIL_USE_TLS == "1",
            use_ssl=EMAIL_USE_SSL == "1",
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=EMAIL_FROM,
            to=[receiver.email],
            connection=connection,
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        logging.getLogger("plane").info("Email sent successfully.")
        return
    except Exception as e:
        log_exception(e)
        return


@shared_task(
    bind=True,
    autoretry_for=(requests.RequestException,),
    retry_backoff=600,
    max_retries=5,
    retry_jitter=True,
)
def webhook_send_task(
    self, webhook, slug, event, event_data, action, current_site, activity, for_slack=False
):
    try:
        webhook = Webhook.objects.get(id=webhook, workspace__slug=slug)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Autopilot",
            "X-Plane-Delivery": str(uuid.uuid4()),
            "X-Plane-Event": event,
        }

        # # Your secret key
        event_data = (
            json.loads(json.dumps(event_data, cls=DjangoJSONEncoder))
            if event_data is not None
            else None
        )

        activity = (
            json.loads(json.dumps(activity, cls=DjangoJSONEncoder))
            if activity is not None
            else None
        )

        action = {
            "POST": "create",
            "PATCH": "update",
            "PUT": "update",
            "DELETE": "delete",
        }.get(action, action)

        payload = {
            "event": event,
            "action": action,
            "webhook_id": str(webhook.id),
            "workspace_id": str(webhook.workspace_id),
            "data": event_data,
            "activity": activity,
        }

        if for_slack:
            slack_text = get_slack_text(event, event_data, action, activity, current_site, slug)
            if slack_text:
                payload["text"] = slack_text

        # Use HMAC for generating signature
        if webhook.secret_key:
            hmac_signature = hmac.new(
                webhook.secret_key.encode("utf-8"),
                json.dumps(payload).encode("utf-8"),
                hashlib.sha256,
            )
            signature = hmac_signature.hexdigest()
            headers["X-Plane-Signature"] = signature

        # Send the webhook event
        response = requests.post(webhook.url, headers=headers, json=payload, timeout=30)

        # Log the webhook request
        WebhookLog.objects.create(
            workspace_id=str(webhook.workspace_id),
            webhook_id=str(webhook.id),
            event_type=str(event),
            request_method=str(action),
            request_headers=str(headers),
            request_body=str(payload),
            response_status=str(response.status_code),
            response_headers=str(response.headers),
            response_body=str(response.text),
            retry_count=str(self.request.retries),
        )

    except requests.RequestException as e:
        # Log the failed webhook request
        WebhookLog.objects.create(
            workspace_id=str(webhook.workspace_id),
            webhook_id=str(webhook.id),
            event_type=str(event),
            request_method=str(action),
            request_headers=str(headers),
            request_body=str(payload),
            response_status=500,
            response_headers="",
            response_body=str(e),
            retry_count=str(self.request.retries),
        )
        # Retry logic
        if self.request.retries >= self.max_retries:
            Webhook.objects.filter(pk=webhook.id).update(is_active=False)
            if webhook:
                # send email for the deactivation of the webhook
                send_webhook_deactivation_email(
                    webhook_id=webhook.id,
                    receiver_id=webhook.created_by_id,
                    reason=str(e),
                    current_site=current_site,
                )
            return
        raise requests.RequestException()

    except Exception as e:
        if settings.DEBUG:
            print(e)
        log_exception(e)
        return


@shared_task
def webhook_activity(
    event,
    verb,
    field,
    old_value,
    new_value,
    actor_id,
    slug,
    current_site,
    event_id,
    old_identifier,
    new_identifier,
    for_slack=False,
    project_id=None,
):
    try:
        target_project_id = project_id
        if verb != "deleted":
            event_model_data = get_model_data(event=event, event_id=event_id)
            target_project_id = event_model_data.get("project", project_id)

        # Base query with project filtering using Q objects
        webhooks = Webhook.objects.filter(
            workspace__slug=slug,
            is_active=True
        ).filter(
            # Either webhook is workspace-wide OR project is in selected projects
            Q(is_workspace_wide=True) |
            Q(webhook_projects__project_id=target_project_id, webhook_projects__deleted_at__isnull=True)
        )

        # Filter based on event type
        if event == "project":
            webhooks = webhooks.filter(project=True)
        elif event == "issue":
            webhooks = webhooks.filter(issue=True)
        elif event in ["module", "module_issue"]:
            webhooks = webhooks.filter(module=True)
        elif event in ["cycle", "cycle_issue"]:
            webhooks = webhooks.filter(cycle=True)
        elif event == "issue_comment":
            webhooks = webhooks.filter(issue_comment=True)

        # Use distinct() to avoid duplicates from the JOIN
        webhooks = webhooks.distinct()

        for webhook in webhooks:
            webhook_send_task.delay(
                webhook=webhook.id,
                slug=slug,
                event=event,
                event_data=(
                    {"id": event_id}
                    if verb == "deleted"
                    else get_model_data(event=event, event_id=event_id)
                ),
                action=verb,
                current_site=current_site,
                activity={
                    "field": field,
                    "new_value": new_value,
                    "old_value": old_value,
                    "actor": get_model_data(event="user", event_id=actor_id),
                    "old_identifier": old_identifier,
                    "new_identifier": new_identifier,
                },
                for_slack=for_slack,
            )
        return
    except Exception as e:
        # Return if a does not exist error occurs
        if isinstance(e, ObjectDoesNotExist):
            return
        if settings.DEBUG:
            print(e)
        log_exception(e)
        return


@shared_task
def model_activity(
    model_name, model_id, requested_data, current_instance, actor_id, slug, origin=None
):
    """Function takes in two json and computes differences between keys of both the json"""
    if current_instance is None:
        webhook_activity.delay(
            event=model_name,
            verb="created",
            field=None,
            old_value=None,
            new_value=None,
            actor_id=actor_id,
            slug=slug,
            current_site=origin,
            event_id=model_id,
            old_identifier=None,
            new_identifier=None,
            for_slack=True,
        )
        return

    # Load the current instance
    current_instance = (
        json.loads(current_instance) if current_instance is not None else None
    )

    # Loop through all keys in requested data and check the current value and requested value
    for key in requested_data:
        # Check if key is present in current instance or not
        if key in current_instance:
            current_value = current_instance.get(key, None)
            requested_value = requested_data.get(key, None)
            if current_value != requested_value:
                webhook_activity.delay(
                    event=model_name,
                    verb="updated",
                    field=key,
                    old_value=current_value,
                    new_value=requested_value,
                    actor_id=actor_id,
                    slug=slug,
                    current_site=origin,
                    event_id=model_id,
                    old_identifier=None,
                    new_identifier=None,
                )

    return


def get_slack_text(event, event_data, action, activity, current_site, slug):
    issues_base_url = f"{current_site}/{slug}/projects/{event_data['project']}/issues/"
    actor_display_name = activity['actor']['display_name']

    if event == "issue_comment" and action == "created":
        comment_text = strip_tags(activity["new_value"])
        truncated_text = comment_text[:50] + "..." if len(comment_text) > 50 else comment_text
        return f"{actor_display_name} added a new comment: <{issues_base_url}{event_data['issue']}|{truncated_text}>"
    elif event == "issue" and action == "created":
        return f"{actor_display_name} created a new issue: <{issues_base_url}{event_data['id']}|{event_data['name']}>"
    elif event == "issue" and action == "updated":
        if activity["field"] == "assignees":
            if activity["old_value"] is None:
                return f"{actor_display_name} assigned `{activity['new_value']}` to issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
            else:
                return f"{actor_display_name} removed `{activity['old_value']}` from issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
        elif activity["field"] == "labels":
            if activity["old_value"] is None:
                return f"{actor_display_name} added label `{activity['new_value']}` to issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
            else:
                return f"{actor_display_name} removed label `{activity['old_value']}` from issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
        elif activity["field"] == "description":
            description_text = strip_tags(activity["new_value"])
            truncated_text = description_text[:50] + "..." if len(description_text) > 50 else description_text
            return f"{actor_display_name} updated `description` to `{truncated_text}` for issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
        else:
            return f"{actor_display_name} updated `{activity['field']}` to `{strip_tags(activity['new_value'])}` for issue <{issues_base_url}{event_data['id']}|{event_data['name']}>"
    elif event == "cycle" and action == "created":
        cycle_url = f"{current_site}/{slug}/projects/{event_data['project']}/cycles/{event_data['id']}"
        return f"A new cycle was created: <{cycle_url}|{event_data['name']}>"

    return None

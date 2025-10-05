"""Google Calendar service helper functions."""

import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def get_calendar_service(access_token: str):
    """Create and return a Google Calendar service instance.

    Args:
        access_token: OAuth access token

    Returns:
        Google Calendar API service instance
    """
    credentials = Credentials(token=access_token)
    return build("calendar", "v3", credentials=credentials)


def find_ai_calendar(service) -> str | None:
    """Find the AI calendar and return its ID.

    Args:
        service: Google Calendar API service instance

    Returns:
        Calendar ID if found, None otherwise
    """
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get("items", []):
        if calendar.get("summary") == "AI":
            return calendar["id"]
    return None


def list_all_events(
        service,
        max_results: int = 140,
        time_min: str | None = None,
        time_max: str | None = None,
) -> list[dict]:
    """List events from all calendars.

    Args:
        service: Google Calendar API service instance
        max_results: Maximum number of events to return per calendar
        time_min: Lower bound for event start time (ISO 8601)
        time_max: Upper bound for event start time (ISO 8601)

    Returns:
        List of simplified event dictionaries
    """
    # Set default time range if not specified (3 days before and after current time)
    if not time_min:
        time_min = (datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=3)).isoformat()
    if not time_max:
        time_max = (datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=3)).isoformat()

    # Get all calendars
    calendar_list = service.calendarList().list().execute()

    all_events = []
    for calendar in calendar_list.get("items", []):
        calendar_id = calendar["id"]

        params = {
            "calendarId": calendar_id,
            "maxResults": max_results,
            "singleEvents": True,
            "orderBy": "startTime",
            "timeMin": time_min,
            "timeMax": time_max,
        }

        events_response = service.events().list(**params).execute()

        for event in events_response.get("items", []):
            simplified_event = {
                "id": event.get("id"),
                "summary": event.get("summary"),
                "start": event.get("start"),
                "end": event.get("end"),
                "status": event.get("status"),
            }
            # Add optional fields if present
            if "description" in event:
                simplified_event["description"] = event["description"]

            all_events.append(simplified_event)

    return all_events


def create_event_in_calendar(
        service,
        calendar_id: str,
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
) -> dict:
    """Create a new event in the specified calendar.

    Args:
        service: Google Calendar API service instance
        calendar_id: Target calendar ID
        summary: Event title/summary
        start_time: Event start time (ISO 8601)
        end_time: Event end time (ISO 8601)
        description: Event description (optional)

    Returns:
        Created event ID
    """
    # Construct event body
    event_body = {
        "summary": summary,
        "start": {
            "dateTime": start_time,
        },
        "end": {
            "dateTime": end_time,
        },
    }

    # Add optional fields
    if description:
        event_body["description"] = description

    # Create the event
    created_event = service.events().insert(
        calendarId=calendar_id,
        body=event_body
    ).execute()

    return {"id": created_event.get("id")}


def check_ai_calendar_exists(service) -> dict | None:
    """Check if AI calendar exists and return its details.

    Args:
        service: Google Calendar API service instance

    Returns:
        Calendar details if exists, None otherwise
    """
    calendar_list = service.calendarList().list().execute()
    for calendar in calendar_list.get("items", []):
        if calendar.get("summary") == "AI":
            return {
                "status": "already_exists",
                "id": calendar["id"],
                "summary": calendar["summary"],
                "message": "Calendar named 'AI' already exists."
            }
    return None


def create_new_ai_calendar(service) -> dict:
    """Create a new AI calendar.

    Args:
        service: Google Calendar API service instance

    Returns:
        Created calendar details
    """
    calendar_body = {
        "summary": "AI",
        "timeZone": "Asia/Tokyo"
    }

    created_calendar = service.calendars().insert(body=calendar_body).execute()

    return {
        "status": "created",
        "id": created_calendar.get("id"),
    }


def update_event_in_calendar(
        service,
        calendar_id: str,
        event_id: str,
        summary: str | None = None,
        start_time: str | None = None,
        end_time: str | None = None,
        description: str | None = None,
        update_following_instances: bool = False,
) -> dict:
    """Update an existing event in the specified calendar.

    Args:
        service: Google Calendar API service instance
        calendar_id: Calendar ID containing the event
        event_id: Event ID to update
        summary: New event title/summary (optional)
        start_time: New event start time in ISO 8601 format (optional)
        end_time: New event end time in ISO 8601 format (optional)
        description: New event description (optional)
        update_following_instances: If True and the event is a recurring event instance,
                                    updates this instance and all following instances.
                                    If False (default), only updates the specified single instance.

    Returns:
        Updated event details
    """
    # Get the current event
    event = service.events().get(
        calendarId=calendar_id,
        eventId=event_id
    ).execute()

    # If updating following instances of a recurring event
    if update_following_instances:
        recurring_event_id = event.get("recurringEventId")

        if recurring_event_id:
            # Get the parent recurring event
            parent_event = service.events().get(
                calendarId=calendar_id,
                eventId=recurring_event_id
            ).execute()

            # Update parent event fields
            if summary is not None:
                parent_event["summary"] = summary
            if description is not None:
                parent_event["description"] = description
            if start_time is not None:
                parent_event["start"]["dateTime"] = start_time
            if end_time is not None:
                parent_event["end"]["dateTime"] = end_time

            # Update the parent recurring event
            updated_event = service.events().update(
                calendarId=calendar_id,
                eventId=recurring_event_id,
                body=parent_event
            ).execute()

            return {
                "status": "updated_following_instances",
                "id": event_id,
                "recurring_event_id": recurring_event_id,
                "calendar_id": calendar_id,
                "message": "Updated this instance and all following instances"
            }

    # Update only the specified event instance
    if summary is not None:
        event["summary"] = summary
    if description is not None:
        event["description"] = description
    if start_time is not None:
        event["start"]["dateTime"] = start_time
    if end_time is not None:
        event["end"]["dateTime"] = end_time

    updated_event = service.events().update(
        calendarId=calendar_id,
        eventId=event_id,
        body=event
    ).execute()

    return {
        "status": "updated",
        "id": updated_event.get("id"),
        "summary": updated_event.get("summary"),
        "start": updated_event.get("start"),
        "end": updated_event.get("end"),
        "calendar_id": calendar_id,
        "message": "Updated single event instance"
    }


def delete_event_from_calendar(
        service,
        calendar_id: str,
        event_id: str,
        delete_following_instances: bool = False,
) -> dict:
    """Delete an event from the specified calendar.

    Args:
        service: Google Calendar API service instance
        calendar_id: Calendar ID containing the event
        event_id: Event ID to delete
        delete_following_instances: If True and the event is a recurring event instance,
                                   deletes this instance and all following instances.
                                   If False, only deletes the specified single instance.

    Returns:
        Deletion result
    """
    if delete_following_instances:
        # First, get the event to check if it's a recurring event instance
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        # If this is an instance of a recurring event, get the recurring event ID
        recurring_event_id = event.get("recurringEventId")

        if recurring_event_id:
            # Get the parent recurring event
            parent_event = service.events().get(
                calendarId=calendar_id,
                eventId=recurring_event_id
            ).execute()

            # Get the start time of the instance being deleted
            instance_start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")

            # Update the parent event's recurrence rule to end before this instance
            # by setting UNTIL parameter
            if instance_start:
                # Parse the start time and subtract one day to set UNTIL
                if "T" in instance_start:
                    # DateTime format
                    dt = datetime.datetime.fromisoformat(instance_start.replace("Z", "+00:00"))
                else:
                    # Date only format
                    dt = datetime.datetime.fromisoformat(instance_start)

                # Format UNTIL date (YYYYMMDD format for all-day, or YYYYMMDDTHHMMSSZ for datetime)
                if "T" in instance_start:
                    until_date = dt.strftime("%Y%m%dT%H%M%SZ")
                else:
                    until_date = dt.strftime("%Y%m%d")

                # Update recurrence rules
                recurrence = parent_event.get("recurrence", [])
                updated_recurrence = []

                for rule in recurrence:
                    if rule.startswith("RRULE:"):
                        # Remove existing UNTIL or COUNT if present
                        parts = rule.split(";")
                        filtered_parts = [p for p in parts if not p.startswith("UNTIL=") and not p.startswith("COUNT=")]
                        # Add new UNTIL
                        updated_rule = ";".join(filtered_parts) + f";UNTIL={until_date}"
                        updated_recurrence.append(updated_rule)
                    else:
                        updated_recurrence.append(rule)

                # Update the parent event
                parent_event["recurrence"] = updated_recurrence
                service.events().update(
                    calendarId=calendar_id,
                    eventId=recurring_event_id,
                    body=parent_event
                ).execute()

                return {
                    "status": "deleted_following_instances",
                    "event_id": event_id,
                    "recurring_event_id": recurring_event_id,
                    "calendar_id": calendar_id,
                    "until_date": until_date,
                    "message": f"Deleted this instance and all following instances (set UNTIL to {until_date})"
                }

    # Delete only the specified event (or single event if not recurring)
    service.events().delete(
        calendarId=calendar_id,
        eventId=event_id
    ).execute()

    return {
        "status": "deleted",
        "event_id": event_id,
        "calendar_id": calendar_id,
        "message": "Deleted single event instance"
    }

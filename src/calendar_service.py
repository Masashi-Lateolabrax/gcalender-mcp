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
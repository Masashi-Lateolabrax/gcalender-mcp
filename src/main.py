import logging
import os
import datetime

from dotenv import load_dotenv

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider

load_dotenv()

auth = GoogleProvider(
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    base_url=os.getenv("BASE_URL"),
    redirect_path=os.getenv("REDIRECT_PATH"),
    required_scopes=os.getenv("REQUIRED_SCOPES").split(","),
)

mcp = FastMCP(name="Google Calendar MCP Server", auth=auth)


@mcp.tool
async def get_user_id() -> dict:
    """Returns user ID about the authenticated Google user."""
    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    return {
        "google_id": token.claims.get("sub"),
        "name": token.claims.get("name"),
    }


@mcp.tool
def get_current_time() -> dict:
    """Returns the current time in JST and UTC"""
    now = datetime.datetime.now(tz=datetime.UTC)
    jst = now + datetime.timedelta(hours=9)
    return {
        "jst": jst.isoformat(),
        "utc": now.isoformat()
    }


@mcp.tool
async def list_events(
        max_results: int = 140,
        time_min: str | None = None,
        time_max: str | None = None,
) -> dict:
    """List events from all calendars.

    Args:
        max_results: Maximum number of events to return per calendar (default: 10)
        time_min: Lower bound for event start time (e.g., '2025-10-06T09:00:00+09:00'). If not specified, defaults to 3 days ago.
        time_max: Upper bound for event start time (e.g., '2025-10-07T18:00:00+09:00'). If not specified, defaults to 3 days from now.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    credentials = Credentials(token=token.token)
    service = build("calendar", "v3", credentials=credentials)

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

    return {"events": all_events}


@mcp.tool
async def create_event(
        summary: str,
        start_time: str,
        end_time: str,
        description: str | None = None,
) -> dict:
    """Create a new event in the AI calendar.

    Args:
        summary: Event title/summary (required)
        start_time: Event start time in ISO 8601 format (e.g., '2025-10-06T09:00:00+09:00')
        end_time: Event end time in ISO 8601 format (e.g., '2025-10-06T10:00:00+09:00')
        description: Event description (optional)

    Returns:
        dict: Created event details including event ID, summary, start, end, and HTML link
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    credentials = Credentials(token=token.token)
    service = build("calendar", "v3", credentials=credentials)

    # Find the "AI" calendar
    calendar_list = service.calendarList().list().execute()
    ai_calendar_id = None
    for calendar in calendar_list.get("items", []):
        if calendar.get("summary") == "AI":
            ai_calendar_id = calendar["id"]
            break

    if not ai_calendar_id:
        return {
            "error": "Calendar named 'AI' not found. Please create a calendar named 'AI' in Google Calendar first."
        }

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
        calendarId=ai_calendar_id,
        body=event_body
    ).execute()

    return {"id": created_event.get("id")}


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

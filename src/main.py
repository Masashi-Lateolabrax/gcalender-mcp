import os
import datetime

from dotenv import load_dotenv

from fastmcp import FastMCP
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.dependencies import get_access_token

from src.calendar_service import (
    get_calendar_service,
    find_ai_calendar,
    list_all_events,
    create_event_in_calendar,
    check_ai_calendar_exists,
    create_new_ai_calendar,
    delete_event_from_calendar,
)

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
    token = get_access_token()
    service = get_calendar_service(token.token)
    events = list_all_events(service, max_results, time_min, time_max)
    return {"events": events}


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
    token = get_access_token()
    service = get_calendar_service(token.token)

    # Find the "AI" calendar
    ai_calendar_id = find_ai_calendar(service)

    if not ai_calendar_id:
        return {
            "error": "Calendar named 'AI' not found. Please create a calendar named 'AI' in Google Calendar first."
        }

    return create_event_in_calendar(service, ai_calendar_id, summary, start_time, end_time, description)


@mcp.tool
async def create_ai_calendar() -> dict:
    """Create a new calendar named 'AI' in Google Calendar.

    Returns:
        dict: Created calendar details including calendar ID and summary
    """
    token = get_access_token()
    service = get_calendar_service(token.token)

    # Check if "AI" calendar already exists
    existing = check_ai_calendar_exists(service)
    if existing:
        return existing

    # Create new calendar
    return create_new_ai_calendar(service)


@mcp.tool
async def delete_event(
        calendar_id: str,
        event_id: str,
        delete_all_instances: bool = False,
) -> dict:
    """Delete an event from a specified calendar.

    Args:
        calendar_id: Calendar ID containing the event
        event_id: Event ID to delete
        delete_all_instances: If True and the event is a recurring event instance,
                            deletes all instances of the recurring event (e.g., all weekly meetings).
                            If False (default), only deletes the specified single instance.

    Returns:
        dict: Deletion result with status, event ID, calendar ID, and message
    """
    token = get_access_token()
    service = get_calendar_service(token.token)

    return delete_event_from_calendar(service, calendar_id, event_id, delete_all_instances)


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

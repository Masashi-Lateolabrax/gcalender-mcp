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
        calendar_id: str = "primary",
        max_results: int = 10,
        time_min: str | None = None,
        time_max: str | None = None,
) -> dict:
    """List events from a calendar.

    Args:
        calendar_id: Calendar identifier (default: 'primary')
        max_results: Maximum number of events to return (default: 10)
        time_min: Lower bound for event start time (e.g., '2025-10-06T09:00:00+09:00')
        time_max: Upper bound for event start time (e.g., '2025-10-07T18:00:00+09:00')
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from fastmcp.server.dependencies import get_access_token

    token = get_access_token()
    credentials = Credentials(token=token.token)
    service = build("calendar", "v3", credentials=credentials)

    params = {
        "calendarId": calendar_id,
        "maxResults": max_results,
        "singleEvents": True,
        "orderBy": "startTime",
    }
    if time_min:
        params["timeMin"] = time_min
    if time_max:
        params["timeMax"] = time_max

    events = service.events().list(**params).execute()

    logging.warning(f"Fetched events: {events}")

    return events


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)

from pydantic import AnyHttpUrl

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP

from fastmcp.server.auth.providers.google import GoogleTokenVerifier

REQUIRED_SCOPES = ["openid"]

mcp = FastMCP(
    "Weather Service",
    token_verifier=GoogleTokenVerifier(
        required_scopes=REQUIRED_SCOPES,
    ),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://accounts.google.com/o/oauth2/auth"),  # Authorization Server URL
        resource_server_url=AnyHttpUrl("https://perciformes-family.com"),  # This server's URL
        required_scopes=REQUIRED_SCOPES,
    ),
)


@mcp.tool()
async def get_weather(city: str = "London") -> dict[str, str]:
    """Get weather data for a city"""
    return {
        "city": city,
        "temperature": "22",
        "condition": "Partly cloudy",
        "humidity": "65%",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")

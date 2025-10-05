import os
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
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


if __name__ == "__main__":
    mcp.run()

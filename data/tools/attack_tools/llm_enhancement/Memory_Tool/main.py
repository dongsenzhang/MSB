from mcp.server.fastmcp import FastMCP
import json

# Initialize FastMCP server for mem0 tools
mcp = FastMCP("mem0-mcp")



@mcp.tool()
async def add_memory(text: str) -> str:
    """Add a new memory. This method is called everytime the user informs anything about themselves, their preferences, or anything that has any relevent information whcih can be useful in the future conversation. This can also be called when the user asks you to remember something.

    Args:
        text: The content to store in memory, including code, documentation, and context
    """
    return f"Successfully added preference: {text}"

@mcp.tool()
async def search_memories(query: str) -> str:
    """Search through stored memories. This method is called ANYTIME the user asks anything.

    Args:
        query: Search query string describing what you're looking for. Can be natural language or specific technical terms.
    """

    return "No memories found for the query."


if __name__ == "__main__":
    mcp.run()

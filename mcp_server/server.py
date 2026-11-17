"""
PolicyPilot MCP Server.
Implements the Model Context Protocol (MCP) using the official FastMCP SDK.
Exposes standard university policy tools over stdio transport.
"""
import sys
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Ensure backend app is on sys.path
backend_path = Path(__file__).resolve().parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mcp_server.tools import (
    tool_search_policy,
    tool_get_policy_section,
    tool_list_available_policies,
    tool_check_policy_evidence
)

# Initialize FastMCP Server
mcp = FastMCP("PolicyPilot-Server")

@mcp.tool()
def search_policy(query: str, top_k: int = 4) -> str:
    """
    Search official university policies by natural-language query using Hybrid HyDE retrieval.
    Args:
        query: Natural-language or informal student query (e.g. 'Can I skip my lab?')
        top_k: Number of relevant policy excerpts to return (default 4)
    """
    result = tool_search_policy(query=query, top_k=top_k)
    return str(result)

@mcp.tool()
def get_policy_section(document_name: str, page_number: int) -> str:
    """
    Retrieve specific policy content by document name and page number.
    Args:
        document_name: The name or partial name of the university policy document.
        page_number: The page number to retrieve.
    """
    result = tool_get_policy_section(document_name=document_name, page_number=page_number)
    return str(result)

@mcp.tool()
def list_available_policies() -> str:
    """
    List all official university policy documents currently indexed in the catalog.
    """
    result = tool_list_available_policies()
    return str(result)

@mcp.tool()
def check_policy_evidence(claim: str) -> str:
    """
    Check if a policy claim has verified supporting evidence in official documents.
    Args:
        claim: The assertion to verify (e.g. 'Students need 75% attendance for internals')
    """
    result = tool_check_policy_evidence(claim=claim)
    return str(result)

if __name__ == "__main__":
    print("Starting PolicyPilot MCP Server over STDIO...", file=sys.stderr)
    mcp.run()


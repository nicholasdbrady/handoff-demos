"""
agent_obo_factory — Setup script for the Agent on-behalf-of-user (OBO) demo.

Agent OBO (preview) lets a Foundry agent call a downstream tool with a token
that represents BOTH the signed-in user AND the agent identity. The tool sees
the user's permissions and Conditional Access applies, but the actor is the
agent — not Foundry, and not a shared service account.

This script does the three setup tasks:

  1. connection   A RemoteTool connection with authType=AgentOnBehalfOfUser
                  and explicit, fully qualified scopes for one resource.
  2. agent        A prompt agent with an MCP tool bound to that connection.
  3. endpoint     The agent endpoint accepts two caller schemes:
                    AzureRbac       (Foundry audience — portal, playground)
                    AgentBlueprint  (agent audience — needed for OBO)

Then run `obo_client.py` as a user to see sign-in, consent, and the result.

Run `--mock` to print every request body without calling Azure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# ── Configuration ──────────────────────────────────────────────────────

ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
MODEL = os.environ.get("FOUNDRY_MODEL_DEPLOYMENT_NAME", "gpt-5-mini")
AGENT_NAME = os.environ.get("AGENT_NAME", "obo-demo-agent")
CONNECTION_NAME = os.environ.get("CONNECTION_NAME", "workiq-mcp-obo")
MCP_SERVER_URL = os.environ.get(
    "MCP_SERVER_URL", "https://workiq.svc.cloud.microsoft/mcp"
)
MCP_SERVER_LABEL = os.environ.get("MCP_SERVER_LABEL", "workiq")
OBO_SCOPES = [
    s.strip()
    for s in os.environ.get(
        "OBO_SCOPES", "api://workiq.svc.cloud.microsoft/WorkIQAgent.Ask"
    ).split(",")
    if s.strip()
]
CLIENT_APP_ID = os.environ.get("CLIENT_APP_ID", "")

# Only needed for --create-connection (ARM). Otherwise create it in the portal.
SUBSCRIPTION_ID = os.environ.get("AZURE_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = os.environ.get("AZURE_RESOURCE_GROUP", "")
FOUNDRY_ACCOUNT = os.environ.get("FOUNDRY_ACCOUNT_NAME", "")
FOUNDRY_PROJECT = os.environ.get("FOUNDRY_PROJECT_NAME", "")
CONNECTION_API_VERSION = os.environ.get("CONNECTION_API_VERSION", "2026-09-01")

FOUNDRY_SCOPE = "https://ai.azure.com/.default"
ARM_SCOPE = "https://management.azure.com/.default"

AGENT_INSTRUCTIONS = """\
You are a read-only identity demo. Use only the Work IQ MCP fetch tool to read
the signed-in user's profile at /me. Do not use write actions or other paths.
Never guess personal details. If access is denied, explain that the downstream
service applies the signed-in user's permissions. Keep the answer short.
"""

# ── Request bodies ─────────────────────────────────────────────────────


def connection_body() -> dict[str, Any]:
    """Return the ARM body for an AgentOnBehalfOfUser MCP connection.

    One connection = one downstream resource. Scopes must be fully qualified
    (for example `api://<app-id>/<scope>`), not `.default`.
    """
    return {
        "properties": {
            "category": "RemoteTool",
            "target": MCP_SERVER_URL or "<mcp-server-url>",
            "authType": "AgentOnBehalfOfUser",
            "scopes": OBO_SCOPES,
            "metadata": {"type": "generic_mcp"},
        }
    }


def endpoint_body() -> dict[str, Any]:
    """Return the merge-patch body that enables the AgentBlueprint scheme.

    PATCH replaces the whole `authorization_schemes` array. Keep AzureRbac so
    the Foundry portal and playground still work during the preview.
    """
    blueprint: dict[str, Any] = {"type": "AgentBlueprint", "isolation_key_source": {"kind": "Entra"}}
    if CLIENT_APP_ID:
        blueprint["token_validation_rules"] = {"allowed_clients": [CLIENT_APP_ID]}
    return {
        "agent_endpoint": {
            "authorization_schemes": [
                {"type": "AzureRbac", "isolation_key_source": {"kind": "Entra"}},
                blueprint,
            ]
        }
    }


def agent_openai_base_url() -> str:
    """Return the agent-scoped OpenAI-compatible base URL used by obo_client.py."""
    return f"{ENDPOINT.rstrip('/')}/agents/{AGENT_NAME}/endpoint/protocols/openai/"


# ── Helpers ────────────────────────────────────────────────────────────


def _rest(method: str, url: str, scope: str, body: dict[str, Any] | None = None, content_type: str = "application/json") -> dict[str, Any]:
    """Send an authenticated REST call with DefaultAzureCredential. Never prints tokens."""
    import requests
    from azure.identity import DefaultAzureCredential

    token = DefaultAzureCredential().get_token(scope).token
    resp = requests.request(
        method,
        url,
        headers={"Authorization": f"Bearer {token}", "Content-Type": content_type},
        data=json.dumps(body) if body is not None else None,
        timeout=60,
    )
    if resp.status_code >= 400:
        raise RuntimeError(f"{method} {url.split('?')[0]} → {resp.status_code}: {resp.text[:500]}")
    return resp.json() if resp.content else {}


def find_blueprint_client_id(obj: Any, under_blueprint: bool = False) -> str | None:
    """Find the blueprint client ID anywhere in an agent GET/PATCH response."""
    if isinstance(obj, dict):
        for key, value in obj.items():
            inside = under_blueprint or "blueprint" in key.lower()
            if inside and key in ("client_id", "clientId") and isinstance(value, str):
                return value
            found = find_blueprint_client_id(value, inside)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_blueprint_client_id(item, under_blueprint)
            if found:
                return found
    return None


def show(title: str, payload: dict[str, Any]) -> None:
    """Print a request or response body for the audience."""
    print(f"\n── {title} " + "─" * max(0, 66 - len(title)))
    print(json.dumps(payload, indent=2))


# ── Setup steps ────────────────────────────────────────────────────────


def create_connection(mock: bool) -> None:
    """Create the AgentOnBehalfOfUser connection through ARM (optional)."""
    url = (
        f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID or '<sub>'}"
        f"/resourceGroups/{RESOURCE_GROUP or '<rg>'}/providers/Microsoft.CognitiveServices"
        f"/accounts/{FOUNDRY_ACCOUNT or '<account>'}/projects/{FOUNDRY_PROJECT or '<project>'}"
        f"/connections/{CONNECTION_NAME}?api-version={CONNECTION_API_VERSION}"
    )
    show(f"1 · PUT connection '{CONNECTION_NAME}'", connection_body())
    if mock:
        return
    if not all([SUBSCRIPTION_ID, RESOURCE_GROUP, FOUNDRY_ACCOUNT, FOUNDRY_PROJECT, MCP_SERVER_URL]):
        sys.exit("Set AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP, FOUNDRY_ACCOUNT_NAME, FOUNDRY_PROJECT_NAME, MCP_SERVER_URL.")
    try:
        _rest("PUT", url, ARM_SCOPE, connection_body())
        print(f"  ✓ connection '{CONNECTION_NAME}' created")
    except RuntimeError as exc:
        print(f"  ✗ {exc}")
        print("  Fallback: create it in the Foundry portal → Tools → Connect a tool → Custom MCP,")
        print("  choose 'Agent on behalf of user', and paste the scopes above. Then rerun without --create-connection.")
        sys.exit(1)


def create_agent(client: Any, mock: bool) -> None:
    """Create a prompt agent whose MCP tool uses the OBO connection."""
    from azure.ai.projects.models import MCPTool, PromptAgentDefinition

    if mock:
        connection_id = f"<project-id>/connections/{CONNECTION_NAME}"
    else:
        connection_id = client.connections.get(CONNECTION_NAME).id

    tool = MCPTool(
        server_label=MCP_SERVER_LABEL,
        server_url=MCP_SERVER_URL or "<mcp-server-url>",
        allowed_tools=["fetch"],
        require_approval="never",
        project_connection_id=connection_id,
    )
    show(f"2 · create agent '{AGENT_NAME}'", {"model": MODEL, "tools": [tool.as_dict()]})
    if mock:
        return
    agent = client.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=MODEL, instructions=AGENT_INSTRUCTIONS, tools=[tool]),
        description="Agent OBO demo: calls an MCP tool as the agent on behalf of the user.",
    )
    print(f"  ✓ agent '{agent.name}' version {agent.version}")


def configure_endpoint(mock: bool) -> str | None:
    """Enable the AgentBlueprint caller scheme and return the blueprint client ID."""
    url = f"{ENDPOINT.rstrip('/')}/agents/{AGENT_NAME}?api-version=v1"
    show("3 · PATCH agent endpoint authorization", endpoint_body())
    if mock:
        return "00000000-0000-0000-0000-000000000000"
    _rest("PATCH", url, FOUNDRY_SCOPE, endpoint_body(), content_type="application/merge-patch+json")
    details = _rest("GET", url, FOUNDRY_SCOPE)
    client_id = find_blueprint_client_id(details)
    print("  ✓ endpoint accepts AzureRbac + AgentBlueprint")
    if not client_id:
        print("  ! Blueprint client ID not found in the response. Check the agent in the portal.")
    return client_id


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Run the setup steps and print the values obo_client.py needs."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mock", action="store_true", help="Print request bodies only. No Azure calls.")
    parser.add_argument("--create-connection", action="store_true", help="Create the connection through ARM.")
    parser.add_argument("--skip-agent", action="store_true", help="Only configure the endpoint.")
    args = parser.parse_args()

    if not args.mock and not ENDPOINT:
        sys.exit("Set AZURE_AI_PROJECT_ENDPOINT (or run with --mock).")

    client = None
    if not args.mock:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential

        client = AIProjectClient(endpoint=ENDPOINT, credential=DefaultAzureCredential())

    print(f"Agent OBO setup · agent={AGENT_NAME} · connection={CONNECTION_NAME} · {'MOCK' if args.mock else ENDPOINT}")
    if args.create_connection or args.mock:
        create_connection(args.mock)
    if not args.skip_agent:
        create_agent(client, args.mock)
    blueprint_client_id = configure_endpoint(args.mock)

    print("\n── Next steps " + "─" * 54)
    print("Add these to .env, then run obo_client.py as a user:\n")
    print(f"  AGENT_BLUEPRINT_CLIENT_ID={blueprint_client_id or '<from portal>'}")
    print(f"  AGENT_OPENAI_BASE_URL={agent_openai_base_url() if ENDPOINT else '<project-endpoint>/agents/<agent>/endpoint/protocols/openai/'}")
    print("\nOne-time Entra setup for the client app (CLIENT_APP_ID):")
    print("  • Add the delegated permission 'access_agent' on the agent blueprint.")
    print("  • Add redirect URI http://localhost (Mobile and desktop applications).")
    print(f"  • Downstream consent for: {', '.join(OBO_SCOPES)}")
    print("    (each user can consent in-flow, or an admin can grant tenant-wide consent)")


if __name__ == "__main__":
    main()

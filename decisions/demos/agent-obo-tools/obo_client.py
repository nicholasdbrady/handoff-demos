"""
obo_client — Call the OBO demo agent as a signed-in user.

This is the runtime half of the Agent on-behalf-of-user (OBO) demo:

  1. The user signs in with a client app and gets a token for the AGENT
     (audience api://<blueprint-client-id>), not for Foundry.
  2. The agent calls the MCP tool. Foundry exchanges the user's token for a
     downstream token that represents the user + the agent identity.
  3. On first use, the response contains an `oauth_consent_request` item.
     The user consents in the browser, and the script continues the same
     response with `previous_response_id`.
  4. The tool returns data for THIS user only. Sign in as someone else and
     you get their data — the agent never has standing access.

Use `--audience foundry` to show the contrast: a Foundry-audience token
cannot drive an AgentOnBehalfOfUser connection.

Run `--mock` to rehearse the whole flow offline.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
import webbrowser
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

# ── Configuration ──────────────────────────────────────────────────────

TENANT_ID = os.environ.get("TENANT_ID", "")
CLIENT_APP_ID = os.environ.get("CLIENT_APP_ID", "")
BLUEPRINT_CLIENT_ID = os.environ.get("AGENT_BLUEPRINT_CLIENT_ID", "")
ENDPOINT = os.environ.get("AZURE_AI_PROJECT_ENDPOINT", "")
AGENT_NAME = os.environ.get("AGENT_NAME", "obo-demo-agent")
AGENT_OPENAI_BASE_URL = os.environ.get(
    "AGENT_OPENAI_BASE_URL",
    f"{ENDPOINT.rstrip('/')}/agents/{AGENT_NAME}/endpoint/protocols/openai/" if ENDPOINT else "",
)
DEFAULT_QUERY = "Use the Work IQ MCP fetch tool to read my profile at /me."

# ── Auth ───────────────────────────────────────────────────────────────


def get_token_provider(audience: str):
    """Return (token_provider, scope) for the chosen caller audience.

    blueprint → the user signs in with CLIENT_APP_ID and asks for a token for the agent.
    foundry   → a normal Foundry token (what the portal and playground use).
    """
    from azure.identity import (
        DefaultAzureCredential,
        InteractiveBrowserCredential,
        get_bearer_token_provider,
    )

    if audience == "foundry":
        scope = "https://ai.azure.com/.default"
        return get_bearer_token_provider(DefaultAzureCredential(), scope), scope

    if not (TENANT_ID and CLIENT_APP_ID and BLUEPRINT_CLIENT_ID):
        sys.exit("Set TENANT_ID, CLIENT_APP_ID, and AGENT_BLUEPRINT_CLIENT_ID (or run with --mock).")
    scope = f"api://{BLUEPRINT_CLIENT_ID}/access_agent"
    credential = InteractiveBrowserCredential(
        tenant_id=TENANT_ID, client_id=CLIENT_APP_ID, redirect_uri="http://localhost"
    )
    return get_bearer_token_provider(credential, scope), scope


def describe_caller(token: str) -> dict[str, Any]:
    """Return non-secret claims that show WHO is calling and FOR WHOM. Never print the token."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except Exception:
        return {}
    return {
        "aud (audience)": claims.get("aud"),
        "user": claims.get("preferred_username") or claims.get("upn") or claims.get("name"),
        "client app": claims.get("azp") or claims.get("appid"),
        "scp (delegated scopes)": claims.get("scp"),
    }


# ── Mock mode ──────────────────────────────────────────────────────────


class _Obj:
    def __init__(self, **kw: Any) -> None:
        self.__dict__.update(kw)


class MockResponses:
    """Offline stand-in that returns a consent request first, then the answer."""

    def __init__(self, audience: str) -> None:
        self.audience = audience
        self.calls = 0

    def create(self, **kwargs: Any) -> Any:
        self.calls += 1
        time.sleep(0.6)
        if self.audience == "foundry":
            return _Obj(
                id="resp_mock_foundry",
                status="completed",
                output=[_Obj(type="mcp_call", server_label="workiq", name="fetch",
                             error="(mock) no user+agent token: the caller token is for Foundry, not the agent")],
                output_text="I can't read the profile: this connection needs a sign-in for the agent audience.",
            )
        if "previous_response_id" not in kwargs:
            return _Obj(
                id="resp_mock_1",
                status="incomplete",
                output=[_Obj(type="oauth_consent_request", server_label="workiq", id="oc_mock",
                             consent_link="https://example.invalid/consent")],
                output_text="",
            )
        return _Obj(
            id="resp_mock_2",
            status="completed",
            output=[
                _Obj(type="mcp_call", server_label="workiq", name="fetch", error=None),
            ],
            output_text="(Mock data) Avery Chen is a Senior PM in Developer Platform. The Work IQ MCP fetch is scoped to this test user.",
        )


# ── Flow ───────────────────────────────────────────────────────────────


def show_tools(response: Any) -> None:
    """Print the tool calls the agent made, with any errors."""
    for item in getattr(response, "output", []) or []:
        if item.type == "mcp_call":
            status = f"✗ {item.error}" if getattr(item, "error", None) else "✓"
            print(f"  tool  {item.server_label}.{item.name}  {status}")


def consent_requests(response: Any) -> list[Any]:
    """Return any oauth_consent_request items in the response output."""
    return [i for i in (getattr(response, "output", []) or []) if i.type == "oauth_consent_request"]


def run(responses: Any, query: str, mock: bool) -> None:
    """Send the query, complete consent if asked, and print the result."""
    print(f"\n› {query}\n")
    kwargs: dict[str, Any] = {"input": query, "tool_choice": "required"}
    response = responses.create(**kwargs)

    for request in consent_requests(response):
        print(f"  ⚠ Consent needed for tool '{request.server_label}'.")
        print("    The agent wants to act as YOU on this tool. Opening the consent page in your browser…")
        if not mock:
            webbrowser.open(request.consent_link)  # do not log the link
            input("    Press Enter after you finish consent › ")
        response = responses.create(previous_response_id=response.id, **kwargs)

    show_tools(response)
    print(f"\n  {response.output_text}\n")


# ── Main ───────────────────────────────────────────────────────────────


def main() -> None:
    """Sign in, show the caller identity, and call the agent."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", nargs="?", default=DEFAULT_QUERY)
    parser.add_argument("--audience", choices=["blueprint", "foundry"], default="blueprint",
                        help="Caller token audience. 'foundry' shows why OBO needs the agent audience.")
    parser.add_argument("--mock", action="store_true", help="Rehearse offline.")
    args = parser.parse_args()

    print(f"Agent OBO client · agent={AGENT_NAME} · audience={args.audience} · {'MOCK' if args.mock else 'LIVE'}")

    if args.mock:
        scope = "https://ai.azure.com/.default" if args.audience == "foundry" else "api://<blueprint-client-id>/access_agent"
        caller = {
            "aud (audience)": scope.rsplit("/", 1)[0],
            "user": "avery@contoso.com",
            "client app": CLIENT_APP_ID or "<client-app-id>",
            "scp (delegated scopes)": "access_agent" if args.audience == "blueprint" else "user_impersonation",
        }
        responses: Any = MockResponses(args.audience)
    else:
        from openai import OpenAI

        if not AGENT_OPENAI_BASE_URL:
            sys.exit("Set AGENT_OPENAI_BASE_URL or AZURE_AI_PROJECT_ENDPOINT.")
        token_provider, scope = get_token_provider(args.audience)
        caller = describe_caller(token_provider())
        client = OpenAI(base_url=AGENT_OPENAI_BASE_URL, api_key=token_provider, default_query={"api-version": "v1"})
        responses = client.responses

    print(f"\n  Caller token (scope {scope}):")
    for k, v in caller.items():
        print(f"    {k:<24}{v}")
    run(responses, args.query, args.mock)


if __name__ == "__main__":
    main()

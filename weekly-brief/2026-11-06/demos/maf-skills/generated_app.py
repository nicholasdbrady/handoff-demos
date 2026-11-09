import asyncio

from agent_framework import Agent
from agent_framework.foundry import FoundryChatClient
from azure.identity.aio import AzureCliCredential


def add(a: int, b: int) -> int:
    """Return the sum of two integers."""
    return a + b


async def main() -> None:
    async with AzureCliCredential() as credential:
        async with FoundryChatClient(credential=credential) as client:
            agent = Agent(
                client=client,
                name="AdditionAgent",
                instructions=(
                    "Use the add tool for addition. Keep your answer brief."
                ),
                tools=[add],
                default_options={"store": False},
            )
            response = await agent.run("Use your tool to add 19 and 23.")
            print(response)


if __name__ == "__main__":
    asyncio.run(main())

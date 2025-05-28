import asyncio
import json
import openai
import dotenv
import os
import httpx
import fastmcp

from openai.types.responses.response_output_item import (
    ResponseFunctionToolCall,
    ResponseOutputMessage,
)

from mcp.types import CallToolResult
from fastmcp.client.transports import StreamableHttpTransport
from rich.console import Console

dotenv.load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4.1"
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")

# For pretty-printing output in the console
console = Console()

# Initialize the MCP client with the transport
transport = StreamableHttpTransport(MCP_SERVER_URL)
mcp_client = fastmcp.Client(transport=transport)

# Initialize OpenAI client
openai_client = openai.AsyncOpenAI(
    api_key=OPENAI_API_KEY, http_client=httpx.AsyncClient(verify=False)
)


async def chat(user_input: str, tools) -> str:
    """
    Process user input through a two-step LLM interaction with tool integration.
    """

    response = await openai_client.responses.create(
        model=MODEL,
        input=user_input,
        instructions="You are a helpful assistant.",
        tools=tools,
    )

    output = response.output[-1]

    if isinstance(output, ResponseFunctionToolCall):
        ##############################################################################
        # We need to execute a functional call, then pass the result back to the LLM #
        ##############################################################################

        tool_call = output
        tool_name = tool_call.name
        tool_args = json.loads(tool_call.arguments)

        console.print(
            f"\n[bold yellow]Executing function call:[/bold yellow] {tool_name}"
        )
        console.print(f"[bold yellow]Function arguments:[/bold yellow] {tool_args}")

        tool_response: CallToolResult = await mcp_client.call_tool(tool_name, tool_args)

        # Parse the JSON string
        tool_response_text = tool_response[0].text
        json_result = json.loads(tool_response_text)

        # Separate the body and subject of the email (otherwise the contents are huge)
        if tool_name == "gmail_find_email":
            subject = json_result["results"][0]["raw"]["payload"]["headers"]["Subject"]
            body = json_result["results"][0]["body_plain"]
            tool_response_text = json.dumps({"subject": subject, "body": body})

        messages = []
        # the user message
        messages.append({"role": "user", "content": user_input})
        # the tool call instruction
        messages.append(tool_call)
        # the tool response
        messages.append(
            {
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": str(tool_response_text),
            }
        )

        response = await openai_client.responses.create(
            model=MODEL,
            input=messages,
            instructions="You are a helpful assistant.",
        )

        output = response.output[-1]
        return output.content[0].text

    elif isinstance(output, ResponseOutputMessage):
        ######################################
        # Print the text output from the LLM #
        ######################################
        return output.content[0].text


async def main():
    console.clear()
    console.print("[green]Connecting to MCP server...[/green]")

    # Connection to MCP server is established here
    async with mcp_client:
        console.print(f"[green]Client connected: {mcp_client.is_connected()}[/green]")

        # Get the tools from the MCP server
        mcp_tools = await mcp_client.list_tools()
        tool_names = [tool.name for tool in mcp_tools]
        console.print(f"[yellow]Tools from MCP server: {tool_names}[/yellow]")

        # Format the tools for OpenAI API
        openai_tools_schema = [
            {
                "type": "function",
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.inputSchema,
            }
            for tool in mcp_tools
        ]

        # Chat loops
        while True:
            user_input = console.input("[bold green]\nUser > [/bold green]")

            if user_input.lower() in ["exit", "quit", "bye"]:
                console.print("[bold red]Exiting...[/bold red]")
                break

            console.print("[bold cyan]\nAssistant > [/bold cyan]", end="")

            response = await chat(user_input=user_input, tools=openai_tools_schema)

            console.print(response)
            console.print("\n", end="")


asyncio.run(main())

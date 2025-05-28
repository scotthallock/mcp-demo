# Remote MCP Server example

This repo demonstrates how you can connect to a remote MCP server from Zapier, which has tools to perform operations on your Gmail account.

## Pre-reqs

1. Have a personal OpenAI API KEY
1. Create a Zapier account (free)
1. Go to https://mcp.zapier.com/mcp/servers/
1. Create a new server and add tools from Gmail. You can add all tools or a subset of tools. (You will need to give Zapier access to your Gmail account through OAuth.)
1. You now have 300 free tool calls per month.

Rename .env.example to .env and fill in:

- OPENAI_API_KEY (Create this in your personal OPENAI account. To use the OpenAI API you need to have a credit card connected and some $$ loaded into your account.)
- MCP_SERVER_URL (You can find in the Zapier site under 'Connect'. It is labeled as 'Server URL' and is should be treated like a secret.)

## Run console chat app

```
poetry shell
python main.py
```

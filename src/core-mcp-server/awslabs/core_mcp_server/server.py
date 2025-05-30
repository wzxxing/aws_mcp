# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
# with the License. A copy of the License is located at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# or in the 'license' file accompanying this file. This file is distributed on an 'AS IS' BASIS, WITHOUT WARRANTIES
# OR CONDITIONS OF ANY KIND, express or implied. See the License for the specific language governing permissions
# and limitations under the License.

import loguru
import sys
from awslabs.core_mcp_server.static import PROMPT_UNDERSTANDING
from fastmcp import Context, FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.utilities.mcp_config import MCPConfig, StdioMCPServer
from mcp.server.session import ServerSession
from typing import List, Literal, TypedDict


class ContentItem(TypedDict):
    """A TypedDict representing a single content item in an MCP response.

    This class defines the structure for content items used in MCP server responses.
    Each content item contains a type identifier and the actual content text.

    Attributes:
        type (str): The type identifier for the content (e.g., 'text', 'error')
        text (str): The actual content text
    """

    type: str
    text: str


class McpResponse(TypedDict, total=False):
    """A TypedDict representing an MCP server response.

    This class defines the structure for responses returned by MCP server tools.
    It supports optional fields through total=False, allowing responses to omit
    the isError field when not needed.

    Attributes:
        content (List[ContentItem]): List of content items in the response
        isError (bool, optional): Flag indicating if the response represents an error
    """

    content: List[ContentItem]
    isError: bool


# Set up logging
logger = loguru.logger

logger.remove()
logger.add(sys.stderr, level='DEBUG')


mcp = FastMCP(
    'mcp-core MCP server.  This is the starting point for all solutions created',
    dependencies=[
        'loguru',
    ],
)


@mcp.tool(name='prompt_understanding')
async def get_prompt_understanding() -> str:
    """MCP-CORE Prompt Understanding.

    ALWAYS Use this tool first to understand the user's query and translate it into AWS expert advice.
    """
    return PROMPT_UNDERSTANDING


@mcp.tool()
async def require_server(server_name: str, ctx: Context) -> Literal['Success']:
    """Load the MCP server from awslabs.

    Args:
        server_name: the name of the server to be used. suggested by the tool `prompt_understanding`

    Returns:
        literal "Success" if the server is loaded successfully
    """
    try:
        proxy_server = FastMCP.as_proxy(
            MCPConfig(
                mcpServers={
                    server_name: StdioMCPServer(
                        command='uvx',
                        args=[server_name],
                    )
                }
            )
        )
        mcp.mount(prefix='required', server=proxy_server, as_proxy=True)
        session: ServerSession = ctx.session
        await session.send_tool_list_changed()
        return 'Success'
    except Exception as e:
        raise ToolError(f'Failed to require {server_name}. Error: {str(e)}')


@mcp.tool()
async def suggest_servers(keywords: list[str]) -> list[str]:
    """Suggest MCP servers from keywords.

    In order to use a server from the suggestions, you *must* load it using `require_server`.

    Args:
        keywords: keywords to match possible MCP servers

    Returns:
        Matched MCP servers as list of string
    """
    keywords_ = [kw.lower() for kw in keywords]
    if 'eks' in keywords_:
        return [
            'awslabs.eks-mcp-server',
            'awslabs.aws-serverless-mcp-server',
        ]
    if 'lambda' in keywords_:
        return [
            'awslabs.lambda-tool-mcp-server',
            'awslabs.mcp-lambda-handler',
        ]
    if 'container' in keywords_:
        return [
            'awslabs.ecs-mcp-server',
            'awslabs.finch-mcp-server',
        ]

    else:
        # TODO: use a better way to find relevant servers
        return [
            'amazon-kendra-index-mcp-server',
            'amazon-mq-mcp-server',
            'amazon-neptune-mcp-server',
            'amazon-sns-sqs-mcp-server',
            'aurora-dsql-mcp-server',
            'aws-diagram-mcp-server',
            'aws-documentation-mcp-server',
            'aws-location-mcp-server',
            'aws-serverless-mcp-server',
            'aws-support-mcp-server',
            'bedrock-kb-retrieval-mcp-server',
            'cdk-mcp-server',
            'cfn-mcp-server',
            'cloudwatch-logs-mcp-server',
            'code-doc-gen-mcp-server',
            'core-mcp-server',
            'cost-analysis-mcp-server',
            'documentdb-mcp-server',
            'dynamodb-mcp-server',
            'ecs-mcp-server',
            'eks-mcp-server',
            'finch-mcp-server',
            'frontend-mcp-server',
            'git-repo-research-mcp-server',
            'lambda-tool-mcp-server',
            'mcp-lambda-handler',
            'memcached-mcp-server',
            'mysql-mcp-server',
            'nova-canvas-mcp-server',
            'postgres-mcp-server',
            'stepfunctions-tool-mcp-server',
            'syntheticdata-mcp-server',
            'terraform-mcp-server',
            'valkey-mcp-server',
        ]


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == '__main__':  # pragma: no cover
    main()

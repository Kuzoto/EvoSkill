from typing import TypeVar, Type, Generic, Any
from pydantic import BaseModel
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

T = TypeVar('T', bound=BaseModel)


class AgentTrace(BaseModel, Generic[T]):
    """Metadata and output from an agent run."""
    # From first message (SystemMessage)
    uuid: str
    session_id: str
    model: str
    tools: list[str]

    # From last message (ResultMessage)
    duration_ms: int
    total_cost_usd: float
    num_turns: int
    usage: dict[str, Any]
    result: str
    is_error: bool

    # The validated structured output
    output: T

    # Full response list for debugging
    messages: list[Any]

    class Config:
        arbitrary_types_allowed = True


class Agent(Generic[T]):
    """Simple wrapper for running Claude agents."""

    def __init__(self, options: ClaudeAgentOptions, response_model: Type[T]):
        self.options = options
        self.response_model = response_model

    async def run(self, query: str) -> AgentTrace[T]:
        async with ClaudeSDKClient(self.options) as client:
            await client.query(query)
            messages = [msg async for msg in client.receive_response()]

            first = messages[0]
            last = messages[-1]
            output = self.response_model.model_validate(last.structured_output)

            return AgentTrace(
                uuid=first.data.get('uuid'),
                session_id=last.session_id,
                model=first.data.get('model'),
                tools=first.data.get('tools', []),
                duration_ms=last.duration_ms,
                total_cost_usd=last.total_cost_usd,
                num_turns=last.num_turns,
                usage=last.usage,
                result=last.result,
                is_error=last.is_error,
                output=output,
                messages=messages,
            )

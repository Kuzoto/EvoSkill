from typing import TypeVar, Type, Generic, Any, Callable, Union
from pydantic import BaseModel
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

T = TypeVar('T', bound=BaseModel)

# Type alias for options that can be static or dynamically generated
OptionsProvider = Union[ClaudeAgentOptions, Callable[[], ClaudeAgentOptions]]


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
    """Simple wrapper for running Claude agents.

    Args:
        options: Either a ClaudeAgentOptions instance (static) or a callable
                 that returns ClaudeAgentOptions (dynamic, called on each run).
        response_model: Pydantic model for structured output validation.
    """

    def __init__(self, options: OptionsProvider, response_model: Type[T]):
        self._options = options
        self.response_model = response_model

    def _get_options(self) -> ClaudeAgentOptions:
        """Get options, calling the provider if it's a callable."""
        if callable(self._options):
            return self._options()
        return self._options

    async def run(self, query: str) -> AgentTrace[T]:
        async with ClaudeSDKClient(self._get_options()) as client:
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

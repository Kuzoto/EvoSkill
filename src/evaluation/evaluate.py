import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, TypeVar

from tqdm.asyncio import tqdm_asyncio

from src.harness import Agent, AgentTrace
from src.harness.sdk_config import get_sdk
from src.harness.skill_mode import get_skill_mode

if TYPE_CHECKING:
    from src.cache import RunCache

T = TypeVar("T")


def _extract_model(options) -> str:
    """Model identity for the run cache: "<provider>/<model>" where available.

    The opencode harness passes a dict whose model lives under ``model_id`` (with the
    provider in ``provider_id``); only the Claude SDK path has an ``options.model``.
    Reading just "model" returned "" for every opencode run, so the cache key collapsed
    to (tree_hash, question, sdk) and a cached run could be replayed for a *different*
    model — e.g. a gpt-oss-120b baseline served as the Qwen3.5-9B baseline, since both
    seeded the same two starter skills and therefore hashed the same tree.
    Provider is included because the same model id behaves differently per endpoint
    (arc/gpt-oss-120b vs vllm-local/gpt-oss-120b).
    """
    if isinstance(options, dict):
        model = str(options.get("model") or options.get("model_id") or "")
        provider = str(options.get("provider_id") or "")
        return f"{provider}/{model}" if provider and model else model
    return str(getattr(options, "model", "") or "")


@dataclass
class EvalResult(Generic[T]):
    """Result of evaluating a single question."""
    question: str
    ground_truth: str
    trace: AgentTrace[T] | None


async def evaluate_agent_parallel(
    agent: Agent[T],
    items: list[tuple[str, str]],
    max_concurrent: int = 2,
    *,
    cache: "RunCache | None" = None,
) -> list[EvalResult[T]]:
    """
    Run agent on multiple questions in parallel.

    Args:
        agent: The agent to evaluate
        items: List of (question, ground_truth) tuples
        max_concurrent: Max concurrent agent runs (default 2)
        cache: Optional RunCache for caching results (keys on git tree hash)

    Returns:
        List of EvalResult containing question, ground_truth, and trace
    """
    from src.evaluation.trace_export import begin_batch, dump_trace

    begin_batch()  # new subdir per eval batch (no-op unless EVOSKILL_TRACE_DIR is set)

    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_one(question: str, ground_truth: str, idx: int) -> EvalResult[T]:
        async with semaphore:
            try:
                async with asyncio.timeout(1020):  # 17-minute hard limit per eval
                    # Check cache first
                    trace = None
                    sdk = get_sdk()
                    model = _extract_model(agent._get_options())
                    # Skill delivery changes the agent's prompt but not the files the
                    # tree hash covers, so "tool" and "inject" runs over the same skills
                    # would otherwise share cache entries.
                    model = f"{model}|skill_mode={get_skill_mode()}"
                    if cache is not None:
                        trace = cache.get(
                            question,
                            agent.response_model,
                            sdk=sdk,
                            model=model,
                        )

                    # Cache miss - run agent
                    if trace is None:
                        trace = await agent.run(question)
                        # Store in cache
                        if cache is not None:
                            cache.set(question, trace, sdk=sdk, model=model)

            except asyncio.TimeoutError:
                print(f"Eval timed out (17min) for: {question[:50]}...")
                trace = None
            except Exception as e:
                print(f"Failed on question: {question[:50]}... Error: {e}")
                trace = None
            # Opt-in per-question trace file (no-op unless EVOSKILL_TRACE_DIR is set).
            dump_trace(question, ground_truth, trace, index=idx)
            return EvalResult(question=question, ground_truth=ground_truth, trace=trace)

    tasks = [run_one(q, gt, i) for i, (q, gt) in enumerate(items)]
    results = await tqdm_asyncio.gather(*tasks, desc="Evaluating")
    return results

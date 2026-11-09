"""evoskill eval — evaluate the best skills on the validation set."""

from __future__ import annotations

import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.command('eval')
@click.option('--verbose', is_flag=True, default=False, help='Show per-question results.')
@click.option('--test', is_flag=True, default=False, help='Evaluate on the held-out test set instead of validation.')
@click.option('--baseline', is_flag=True, default=False, help='Evaluate the baseline (no evolved skills).')
@click.option('--config', 'config_path', type=click.Path(dir_okay=False, path_type=Path),
              default=None, help='Load a specific config TOML file.')
def eval_cmd(verbose: bool, test: bool, baseline: bool, config_path: Path | None):
    """Evaluate the best skills on the validation set."""
    from src.harness import Agent, set_sdk
    from src.harness.skill_mode import get_skill_mode, set_skill_mode
    from src.agent_profiles.base_agent.base_agent import make_base_agent_options
    from src.cli.config import load_config
    from src.cli.shared import load_and_split, make_scorer
    from src.evaluation import evaluate_agent_parallel
    from src.registry import ProgramManager
    from src.schemas import AgentResponse
    cfg = load_config(config_path=config_path)
    sdk = cfg.harness.name
    set_sdk(sdk)
    set_skill_mode(cfg.harness.skill_mode)

    if sdk == "openhands":
        console.print("  [yellow]Warning:[/yellow] OpenHands does not support native structured output.")
        console.print("  Using fallback JSON extraction which may be less reliable.\n")

    try:
        _, val_data, test_data = load_and_split(cfg)
    except FileNotFoundError:
        console.print(f'[red]Error:[/red] Dataset not found at {cfg.dataset_path}')
        raise SystemExit(1)

    eval_data = test_data if test else val_data
    split_name = 'test' if test else 'val'

    manager = ProgramManager(cwd=cfg.project_root)
    if baseline:
        # `program/base` is only created by the run loop's INIT step, so a project that
        # has never been evolved has no branch to switch to — its working tree already is
        # the baseline (seeded skills, or none). Mirror the frontier path and carry on
        # instead of failing with "pathspec 'program/base' did not match any file(s)".
        if 'base' in manager.list_programs():
            manager.switch_to('base')
        else:
            # Name what the baseline actually is, since nothing pins it down: with
            # SEED_SKILLS=0 the run dir has no skills at all, and a hand-seeded dir has
            # whatever was copied in. Creating the branch here would instead freeze the
            # current tree as "base" for every later run, so this stays read-only.
            skills_dir = Path(cfg.project_root) / '.claude' / 'skills'
            present = sorted(p.name for p in skills_dir.iterdir()) if skills_dir.is_dir() else []
            console.print(
                '\n  No base program branch yet — evaluating the project as it stands '
                f"(skills present: {', '.join(present) if present else 'none'}).\n"
            )
        best = 'base (baseline)'
    else:
        best = manager.get_best_from_frontier()
        if best:
            manager.switch_to(best)
        else:
            console.print('\n  No frontier found — evaluating base program.\n')
            best = 'base'

    console.print(f'\n  Evaluating [bold]{best}[/bold] on {len(eval_data)} {split_name} samples...\n')

    agent = Agent(
        make_base_agent_options(
            model=cfg.harness.model,
            data_dirs=cfg.harness.data_dirs,
            project_root=cfg.project_root,
        ),
        AgentResponse,
        timeout_seconds=cfg.harness.timeout_seconds,
        max_retries=cfg.harness.max_retries,
    )
    scorer = make_scorer(cfg)

    qa_data = [(q, a) for q, a, _ in eval_data]

    # Continue mode (EVOSKILL_EVAL_CONTINUE): reuse questions an earlier run of the same
    # setup answered, rerun only the ones left without an answer.
    from src.evaluation.eval_continue import (
        continue_dirs, copy_reused, load_previous, run_meta, write_meta,
    )
    from src.evaluation.trace_export import begin_batch

    meta = run_meta(cfg, split_name, [q for q, _ in qa_data])
    write_meta(meta)
    prev_dirs = continue_dirs()
    previous: dict = {}
    if prev_dirs:
        previous, warnings = load_previous(prev_dirs, meta)
        for w in warnings:
            console.print(f'  [yellow]Warning:[/yellow] {w}')
    todo = [i for i, (q, _) in enumerate(qa_data) if q not in previous]
    reused = {i: previous[q] for i, (q, _) in enumerate(qa_data) if q in previous}
    if prev_dirs:
        console.print(f'  Continuing from {len(prev_dirs)} earlier run(s): {len(reused)} answered '
                      f'question(s) reused, {len(todo)} to run.\n')

    if todo:
        new_results = asyncio.run(evaluate_agent_parallel(
            agent, [qa_data[i] for i in todo], max_concurrent=cfg.evolution.concurrency,
            indices=todo,
        ))
    else:
        new_results = []
        begin_batch()  # still give the reused records a batch dir
    copy_reused(reused)

    answers: dict[int, str] = {}
    for i, r in zip(todo, new_results):
        answers[i] = r.trace.output.final_answer if r.trace and r.trace.output else ''
    for i, (rec, _) in reused.items():
        answers[i] = str(rec.get('final_answer') or '')

    scores = []
    combined = []
    n_rerun_unanswered = sum(1 for i in todo if not answers[i].strip())
    for i, (q, a) in enumerate(qa_data):
        got = answers[i]
        s = scorer(q, got, a)
        scores.append(s)
        combined.append((q, a, got, s))

    accuracy = sum(1 for s in scores if s >= 0.8) / len(scores) if scores else 0.0

    if verbose:
        table = Table(box=None, pad_edge=False, show_header=True, header_style='bold')
        table.add_column('Question', max_width=50)
        table.add_column('Expected', max_width=20)
        table.add_column('Got', max_width=20)
        table.add_column('Score', width=7)
        for q, a, got, s in combined:
            style = 'green' if s >= 0.8 else 'red'
            table.add_row(q[:50], a[:20], (got or '—')[:20], f'{s:.0%}', style=style)
        console.print(table)

    n_correct = sum(1 for s in scores if s >= 0.8)
    console.print(f'  Accuracy: [bold]{accuracy:.1%}[/bold]  ({n_correct}/{len(scores)} correct)\n')
    if prev_dirs:
        console.print(f'  Continue: {len(reused)} reused, {len(todo)} rerun, '
                      f'{n_rerun_unanswered} still without an answer.\n')

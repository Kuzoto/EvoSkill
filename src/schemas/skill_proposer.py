from pydantic import BaseModel


class SkillProposerResponse(BaseModel):
    """Response from the skill proposer agent.

    This proposer analyzes agent failures and proposes skill additions
    to address capability gaps.
    """

    proposed_skill: str
    """High-level description of the skill needed to address the failure."""

    justification: str
    """Explanation of why this skill addresses the identified gap."""

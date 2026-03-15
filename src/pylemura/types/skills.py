"""Skill definition interfaces — mirrors lemura/src/types/skills.ts"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal, Optional

SkillStrategy = Literal["fixed", "dynamic"]
SkillInjectPosition = Literal["system_prompt", "pre_turn", "post_history"]
SkillTier = Literal["nano", "micro", "standard", "extended"]


@dataclass
class ISkill:
    name: str
    version: str
    description: str
    inject: SkillInjectPosition = "system_prompt"
    priority: int = 50
    tier: Optional[SkillTier] = None
    # Tiered content (compact-first when token budgeting)
    nano: Optional[str] = None
    micro: Optional[str] = None
    standard: Optional[str] = None
    extended: Optional[str] = None
    content: Optional[str] = None  # full body / standard fallback
    strategy: SkillStrategy = "fixed"
    enabled: bool = True            # used only for dynamic skills
    required_tools: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

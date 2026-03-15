"""Skill injection system — mirrors lemura/src/skills/SkillInjector.ts"""
from __future__ import annotations
from typing import Optional

from pylemura.types.skills import ISkill, SkillInjectPosition

_TIER_ORDER = ("nano", "micro", "standard", "extended")


def _resolve_content(skill: ISkill, token_budget: Optional[int], estimate_tokens: Optional[callable]) -> Optional[str]:
    """Return the best-fitting tier content within budget."""
    for tier in _TIER_ORDER:
        text = getattr(skill, tier, None)
        if text:
            if token_budget is None or estimate_tokens is None:
                return text
            if estimate_tokens(text) <= token_budget:
                return text

    # Fall back to full content
    fallback = skill.content or skill.description
    if token_budget is None or estimate_tokens is None:
        return fallback
    if estimate_tokens(fallback) <= token_budget:
        return fallback
    return None


class SkillInjector:
    def __init__(self, estimate_tokens: Optional[callable] = None) -> None:
        self._skills: list[ISkill] = []
        self._estimate_tokens = estimate_tokens or (lambda t: max(1, len(t) // 4))

    # --- Registration ---

    def register(self, skill: ISkill) -> None:
        self._skills.append(skill)
        self._skills.sort(key=lambda s: s.priority)

    # --- Dynamic skill control ---

    def enable_skill(self, name: str) -> None:
        for s in self._skills:
            if s.name == name and s.strategy == "dynamic":
                s.enabled = True

    def disable_skill(self, name: str) -> None:
        for s in self._skills:
            if s.name == name and s.strategy == "dynamic":
                s.enabled = False

    def enable_by_tags(self, tags: list[str]) -> None:
        tag_set = set(tags)
        for s in self._skills:
            if s.strategy == "dynamic" and tag_set.intersection(s.tags):
                s.enabled = True

    def disable_by_tags(self, tags: list[str]) -> None:
        tag_set = set(tags)
        for s in self._skills:
            if s.strategy == "dynamic" and tag_set.intersection(s.tags):
                s.enabled = False

    # --- Queries ---

    def get_all(self) -> list[ISkill]:
        return list(self._skills)

    def get_active_skills(self) -> list[ISkill]:
        return [
            s for s in self._skills
            if s.strategy == "fixed" or (s.strategy == "dynamic" and s.enabled)
        ]

    def get_skills_for_injection(self, position: SkillInjectPosition) -> list[ISkill]:
        return [s for s in self.get_active_skills() if s.inject == position]

    def get_required_tools(self) -> list[str]:
        tools: list[str] = []
        for s in self.get_active_skills():
            tools.extend(s.required_tools)
        return list(dict.fromkeys(tools))  # deduplicate preserving order

    # --- Injection block builder ---

    def build_injection_block(
        self,
        position: SkillInjectPosition,
        token_budget: Optional[int] = None,
    ) -> str:
        skills = self.get_skills_for_injection(position)
        if not skills:
            return ""

        parts: list[str] = []
        remaining_budget = token_budget

        for skill in skills:
            content = _resolve_content(
                skill,
                remaining_budget,
                self._estimate_tokens,
            )
            if content is None:
                continue
            parts.append(f"## Skill: {skill.name}\n{content}")
            if remaining_budget is not None:
                remaining_budget -= self._estimate_tokens(content)
                if remaining_budget <= 0:
                    break

        return "\n\n".join(parts)

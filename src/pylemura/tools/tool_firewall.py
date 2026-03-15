"""Tool firewall — mirrors lemura/src/tools/ToolFirewall.ts"""
from __future__ import annotations
import re
from typing import Optional

from pylemura.types.logger import ILogger
from pylemura.types.tools import (
    ToolDecision,
    ToolFirewallConfig,
    ToolFirewallResult,
)


def evaluate_tool_firewall(
    config: ToolFirewallConfig,
    tool_name: str,
    args_json: str,
    logger: Optional[ILogger] = None,
) -> ToolFirewallResult:
    """Evaluate tool call against firewall rules. First matching rule wins."""
    for rule in config.rules:
        name_match = True
        args_match = True
        if rule.name:
            name_match = bool(re.search(rule.name, tool_name))
        if rule.arguments:
            args_match = bool(re.search(rule.arguments, args_json))
        if name_match and args_match:
            if logger:
                logger.debug(
                    f"[Firewall] Rule matched for '{tool_name}': {rule.decision}",
                    {"rule_name": rule.name, "reason": rule.reason},
                )
            return ToolFirewallResult(decision=rule.decision, reason=rule.reason)

    return ToolFirewallResult(decision=config.default_decision)

"""pylemura — Provider-agnostic agentic AI runtime for Python.
Python portage of lemura (https://github.com/rzafiamy/lemura).
"""
__version__ = "1.1.0"

# Core
from pylemura.agent.session_manager import SessionManager
from pylemura.context.context_manager import ContextManager

# Adapters
from pylemura.adapters.openai_compatible import (
    OpenAICompatibleAdapter,
    OpenAICompatibleAdapterConfig,
)

# Context strategies
from pylemura.context.sandwich_compression import (
    SandwichCompressionStrategy,
    SandwichCompressionConfig,
)
from pylemura.context.history_compression import (
    HistoryCompressionStrategy,
    HistoryCompressionConfig,
)
from pylemura.context.summary_injection import (
    SummaryInjectionStrategy,
    SummaryInjectionStrategyConfig,
)

# Memory
from pylemura.context.short_term_memory_registry import ShortTermMemoryRegistry, STMItem
from pylemura.context.in_memory_storage_adapter import InMemoryStorageAdapter
from pylemura.context.in_memory_scratchpad_adapter import InMemoryScratchpadAdapter

# Tools
from pylemura.tools.tool_registry import ToolRegistry
from pylemura.tools.tool_firewall import evaluate_tool_firewall
from pylemura.tools.schema_validator import validate_json_schema
from pylemura.tools.builtin.short_term_memory import make_stm_tools
from pylemura.tools.builtin.media import make_media_tools

# Skills
from pylemura.skills.skill_injector import SkillInjector

# Agent execution
from pylemura.agent.execution.goal_injector import Goal, GoalInjector
from pylemura.agent.execution.continuation_planner import (
    ContinuationPlan,
    ContinuationPlanner,
    ContinuationStep,
    StepCondition,
)
from pylemura.agent.execution.tool_response_processor import (
    ToolResponseProcessor,
    ToolResponseProcessorConfig,
)

# RAG
from pylemura.rag.in_memory_rag_adapter import InMemoryRAGAdapter

# Media
from pylemura.media.media_bridge import MediaBridge

# MCP
from pylemura.mcp.mcp_client_registry import MCPClientRegistry

# Logger
from pylemura.logger.default_logger import DefaultLogger
from pylemura.types.logger import LogLevel

# All types (re-exported for convenience)
from pylemura.types import *  # noqa: F401, F403

__all__ = [
    "__version__",
    # Core
    "SessionManager",
    "ContextManager",
    # Adapters
    "OpenAICompatibleAdapter",
    "OpenAICompatibleAdapterConfig",
    # Context strategies
    "SandwichCompressionStrategy", "SandwichCompressionConfig",
    "HistoryCompressionStrategy", "HistoryCompressionConfig",
    "SummaryInjectionStrategy", "SummaryInjectionStrategyConfig",
    # Memory
    "ShortTermMemoryRegistry", "STMItem",
    "InMemoryStorageAdapter",
    "InMemoryScratchpadAdapter",
    # Tools
    "ToolRegistry",
    "evaluate_tool_firewall",
    "validate_json_schema",
    "make_stm_tools",
    "make_media_tools",
    # Skills
    "SkillInjector",
    # Execution
    "Goal", "GoalInjector",
    "ContinuationPlan", "ContinuationPlanner", "ContinuationStep", "StepCondition",
    "ToolResponseProcessor", "ToolResponseProcessorConfig",
    # RAG
    "InMemoryRAGAdapter",
    # Media
    "MediaBridge",
    # MCP
    "MCPClientRegistry",
    # Logger
    "DefaultLogger", "LogLevel",
]

"""pylemura type definitions."""
from pylemura.types.adapters import (
    AudioChunk,
    CompletionChunk,
    CompletionRequest,
    CompletionResponse,
    ContentBlock,
    IProviderAdapter,
    ImageGenRequest,
    ImageGenResponse,
    ModelInfo,
    NormalizedMessage,
    SynthesisRequest,
    TokenUsage,
    ToolCall,
    ToolResult,
    TranscriptionRequest,
    TranscriptionResponse,
    VisionRequest,
    VisionResponse,
)
from pylemura.types.agent import (
    ContinuationStrategy,
    GoalInjectionFrequency,
    GoalInjectionPosition,
    MediaConfig,
    SessionConfig,
    TraceEvent,
    TraceEventType,
)
from pylemura.types.context import ContextWindow, IContextStrategy, Turn, TurnRole
from pylemura.types.errors import (
    LemuraAdapterError,
    LemuraContextOverflowError,
    LemuraError,
    LemuraMCPConnectionError,
    LemuraMCPError,
    LemuraMCPTimeoutError,
    LemuraMaxIterationsError,
    LemuraSkillInjectionError,
    LemuraToolNotFoundError,
    LemuraToolTimeoutError,
    LemuraToolValidationError,
)
from pylemura.types.logger import ILogger, LogLevel, LogMetadata
from pylemura.types.mcp import MCPServerConfig, MCPTransportType
from pylemura.types.rag import (
    IRAGAdapter,
    RAGDocument,
    RAGIngestRequest,
    RAGIngestResponse,
    RAGQueryRequest,
    RAGQueryResponse,
    RAGQueryResult,
)
from pylemura.types.skills import ISkill, SkillInjectPosition, SkillStrategy, SkillTier
from pylemura.types.storage import IScratchpadAdapter, IStorageAdapter
from pylemura.types.tools import (
    FunctionTool,
    IToolDefinition,
    IToolResponseProcessor,
    ToolContext,
    ToolDecision,
    ToolExecutionBudget,
    ToolFirewallConfig,
    ToolFirewallResult,
    ToolFirewallRule,
)

__all__ = [
    # adapters
    "AudioChunk", "CompletionChunk", "CompletionRequest", "CompletionResponse",
    "ContentBlock", "IProviderAdapter", "ImageGenRequest", "ImageGenResponse",
    "ModelInfo", "NormalizedMessage", "SynthesisRequest", "TokenUsage",
    "ToolCall", "ToolResult", "TranscriptionRequest", "TranscriptionResponse",
    "VisionRequest", "VisionResponse",
    # agent
    "ContinuationStrategy", "GoalInjectionFrequency", "GoalInjectionPosition",
    "MediaConfig", "SessionConfig", "TraceEvent", "TraceEventType",
    # context
    "ContextWindow", "IContextStrategy", "Turn", "TurnRole",
    # errors
    "LemuraAdapterError", "LemuraContextOverflowError", "LemuraError",
    "LemuraMCPConnectionError", "LemuraMCPError", "LemuraMCPTimeoutError",
    "LemuraMaxIterationsError", "LemuraSkillInjectionError", "LemuraToolNotFoundError",
    "LemuraToolTimeoutError", "LemuraToolValidationError",
    # logger
    "ILogger", "LogLevel", "LogMetadata",
    # mcp
    "MCPServerConfig", "MCPTransportType",
    # rag
    "IRAGAdapter", "RAGDocument", "RAGIngestRequest", "RAGIngestResponse",
    "RAGQueryRequest", "RAGQueryResponse", "RAGQueryResult",
    # skills
    "ISkill", "SkillInjectPosition", "SkillStrategy", "SkillTier",
    # storage
    "IScratchpadAdapter", "IStorageAdapter",
    # tools
    "FunctionTool", "IToolDefinition", "IToolResponseProcessor", "ToolContext",
    "ToolDecision", "ToolExecutionBudget", "ToolFirewallConfig",
    "ToolFirewallResult", "ToolFirewallRule",
]

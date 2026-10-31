"""NFCore fiscal cognitive core: advisory, grounded, tenant-isolated and fail-open."""

from .baseline import BASELINE_VERSION, Baseline, RejectionBaseline
from .context import ContextPack, ContextPackBuilder, ScopeViolationError
from .contracts import (
    SCHEMA_VERSION,
    AdviceRequest,
    AdviceResult,
    AdviceSection,
    AdviceStatus,
    Capability,
    Evidence,
    EvidenceKind,
    ModelUsage,
    Provenance,
    SectionKind,
)
from .guardrails import GuardResult, OutputGuard
from .knowledge import RejectionKnowledgeBase, default_rejection_knowledge_base
from .redaction import Redactor
from .resilience import Bulkhead, CircuitBreaker
from .service import CognitiveAdviceService

__all__ = [
    "BASELINE_VERSION",
    "SCHEMA_VERSION",
    "AdviceRequest",
    "AdviceResult",
    "AdviceSection",
    "AdviceStatus",
    "Baseline",
    "Bulkhead",
    "Capability",
    "CircuitBreaker",
    "CognitiveAdviceService",
    "ContextPack",
    "ContextPackBuilder",
    "Evidence",
    "EvidenceKind",
    "GuardResult",
    "ModelUsage",
    "OutputGuard",
    "Provenance",
    "Redactor",
    "RejectionBaseline",
    "RejectionKnowledgeBase",
    "ScopeViolationError",
    "SectionKind",
    "default_rejection_knowledge_base",
]

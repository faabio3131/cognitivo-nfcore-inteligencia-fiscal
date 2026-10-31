"""Default wiring of deterministic baselines for the enabled capabilities."""

from __future__ import annotations

from .baseline import BaselineFn, RejectionBaseline
from .classification import ClassificationBaseline
from .contracts import Capability
from .knowledge import default_classification_catalog, default_rejection_knowledge_base


def default_baselines() -> dict[Capability, BaselineFn]:
    return {
        Capability.EXPLAIN_REJECTION: RejectionBaseline(default_rejection_knowledge_base()),
        Capability.SUGGEST_CLASSIFICATION: ClassificationBaseline(
            default_classification_catalog()
        ),
    }

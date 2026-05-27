"""Prompt Compiler v2 Intermediate Representation (IR).

The IR is a typed, directed, attributed graph.  Every compiler pass reads and
writes IR nodes.  No pass operates on raw strings — only on the IR.
"""

from __future__ import annotations

from .segment import ContextRole, Segment, SegmentType, SourceRef, PolicyBinding, TransformRecord, NodeMetadata
from .entity import Entity, EntityRelation, EntityGraph
from .provenance import ProvenanceChain, CompilationProvenance
from .graph import ContextGraph
from .policy import PolicyBinding as PolicyBindingAlias

__all__ = [
    "ContextRole",
    "Segment",
    "SegmentType",
    "SourceRef",
    "PolicyBinding",
    "PolicyBindingAlias",
    "TransformRecord",
    "NodeMetadata",
    "Entity",
    "EntityRelation",
    "EntityGraph",
    "ProvenanceChain",
    "CompilationProvenance",
    "ContextGraph",
]

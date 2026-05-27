"""EntityResolutionPass — extract entities and build the EntityGraph."""

from __future__ import annotations

import re

from promptcompiler.entities import extract_entities as _extract_entities
from promptcompiler.ir import ContextGraph
from promptcompiler.ir.entity import Entity
from promptcompiler.ir.segment import TransformRecord
from promptcompiler.passes import Diagnostic, PassContext, PassRegistry


@PassRegistry.register
class EntityResolutionPass:
    """Extract named entities from each segment and link them into the graph.

    Populates ``graph.entities`` with ``Entity`` entries and calls
    ``link_entity()`` to track segment-to-entity relationships.
    """

    pass_id = "entity_resolve.v1"
    pass_version = "1.0.0"
    dependencies: list[str] = ["parse.v1"]

    def run(self, graph: ContextGraph, ctx: PassContext) -> ContextGraph:
        global_entities: dict[str, Entity] = {}

        for seg_id, seg in list(graph.segments.items()):
            raw_entities = _extract_entities(seg.text)
            seg_entity_ids: set[str] = set()

            for raw_ent in raw_entities:
                norm = raw_ent.strip().lower()
                if norm not in global_entities:
                    entity = Entity(
                        id=f"ent_{hash(norm) & 0xFFFFFFFF:08x}",
                        surface_form=raw_ent,
                        canonical_form=raw_ent,
                        entity_type=self._infer_entity_type(raw_ent),
                    )
                    global_entities[norm] = entity
                    graph.entities.add_entity(entity)

                ent_id = global_entities[norm].id
                seg_entity_ids.add(ent_id)
                graph.entities.link_entity(seg_id, ent_id)

            seg.metadata.entity_ids = seg_entity_ids

            seg.transforms.append(TransformRecord(
                pass_id=self.pass_id,
                pass_version=self.pass_version,
                reason=f"resolved {len(raw_entities)} entities",
                metadata={"raw_entities": raw_entities},
            ))

        ctx.diagnostics.append(Diagnostic(
            severity="info",
            pass_id=self.pass_id,
            code="ENTITY_RESOLVE_COMPLETE",
            message=f"Resolved {len(global_entities)} unique entities across {len(graph.segments)} segments",
        ))
        return graph

    @staticmethod
    def _infer_entity_type(value: str) -> str:
        if value.startswith(("http://", "https://")):
            return "url"
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return "date"
        if re.match(r"^[$€£]", value):
            return "currency"
        if re.match(r"\d+(?:\.\d+)?%", value):
            return "percentage"
        if re.match(r"^[0-9a-fA-F-]{36}$", value):
            return "uuid"
        return "other"

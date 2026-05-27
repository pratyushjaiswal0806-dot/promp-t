"""Entity graph for the PromptCompiler IR."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entity:
    """A protected entity (case ID, URL, etc.) found in a prompt."""
    id: str
    surface_form: str
    canonical_form: str | None = None
    entity_type: str = "unknown"
    confidence: float = 1.0


@dataclass
class EntityRelation:
    """A directed relationship between two entities."""
    source_id: str
    target_id: str
    relation_type: str = "co_occurs"
    weight: float = 1.0


@dataclass
class EntityGraph:
    """The full entity graph for a compilation context.

    Tracks all entities, their relationships, and which segments reference
    which entities.
    """

    entities: dict[str, Entity] = field(default_factory=dict)
    relations: list[EntityRelation] = field(default_factory=list)
    segment_to_entities: dict[str, set[str]] = field(default_factory=dict)

    def add_entity(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def link_entity(self, segment_id: str, entity_id: str) -> None:
        self.segment_to_entities.setdefault(segment_id, set()).add(entity_id)

    def entities_for_segment(self, segment_id: str) -> list[Entity]:
        eids = self.segment_to_entities.get(segment_id, set())
        return [self.entities[eid] for eid in eids if eid in self.entities]

    def merge(self, other: EntityGraph) -> None:
        self.entities.update(other.entities)
        self.relations.extend(other.relations)
        for sid, eids in other.segment_to_entities.items():
            self.segment_to_entities.setdefault(sid, set()).update(eids)

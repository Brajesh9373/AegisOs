"""Knowledge service module - transforms information into understanding (SECTION 29/75)."""

from ecms.knowledge.domain.analysis import CodeAnalysis, CodeEntity, CodeRelationship
from ecms.knowledge.infrastructure.code_analysis import (
    GenericCodeAnalyzer,
    PythonCodeAnalyzer,
    analyze_code,
    detect_language,
)
from ecms.knowledge.infrastructure.ontology import OntologyMapper
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.knowledge.interfaces.engine import KnowledgeEngine, KnowledgeRepository
from ecms.knowledge.services.engine import DefaultKnowledgeEngine

__all__ = [
    "CodeAnalysis",
    "CodeEntity",
    "CodeRelationship",
    "DefaultKnowledgeEngine",
    "GenericCodeAnalyzer",
    "InMemoryKnowledgeRepository",
    "KnowledgeEngine",
    "KnowledgeRepository",
    "OntologyMapper",
    "PythonCodeAnalyzer",
    "analyze_code",
    "detect_language",
]

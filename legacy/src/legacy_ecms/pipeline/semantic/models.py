from pydantic import BaseModel, ConfigDict, Field


class SemanticConcept(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    category: str = "business_concept"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class SemanticExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    concepts: list[SemanticConcept] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

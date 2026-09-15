"""Modelos de datos para la verificación de encapsulamiento en MOTOKO."""

from typing import List, Optional
from pydantic import BaseModel, Field


class TdaDefinition(BaseModel):
    name: str
    is_opaque: bool = True
    header_path: str
    declared_fields: List[str] = Field(default_factory=list)


class EncapsulationViolation(BaseModel):
    code: str
    severity: str  # "ERROR", "WARNING"
    tda_name: str
    file_path: str
    line_number: int
    line_content: str
    message: str
    suggestion: str


class TdaAuditReport(BaseModel):
    schema_version: str = "1.0.0"
    tdas_analyzed: List[TdaDefinition] = Field(default_factory=list)
    violations: List[EncapsulationViolation] = Field(default_factory=list)
    passed: bool = True

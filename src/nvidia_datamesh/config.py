"""Configuration schema for NVIDIA DataMesh."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class DataSourceConfig(BaseModel):
    """Base configuration for any supported data source."""

    name: str
    type: str
    params: Dict[str, str] = Field(default_factory=dict)

    @validator("name")
    def name_not_empty(cls, value: str) -> str:
        if not value:
            raise ValueError("Data source name must be provided")
        return value


class SchemaField(BaseModel):
    """Schema field metadata used for harmonization."""

    source: str
    target: str
    dtype: str = "string"
    description: Optional[str] = None


class SchemaConfig(BaseModel):
    """Schema alignment declaration."""

    fields: List[SchemaField]
    primary_key: Optional[str] = None


class PipelineIOConfig(BaseModel):
    """Input/output metadata for pipeline runs."""

    workspace_dir: Path = Field(default=Path("./artifacts"))
    output_format: str = Field(default="parquet")
    output_uri: Optional[str] = None

    @validator("output_format")
    def validate_format(cls, value: str) -> str:
        if value not in {"parquet", "jsonl"}:
            raise ValueError("output_format must be 'parquet' or 'jsonl'")
        return value


class PipelineConfig(BaseModel):
    """Root configuration for a DataMesh pipeline."""

    sources: List[DataSourceConfig]
    schema: SchemaConfig
    io: PipelineIOConfig = Field(default_factory=PipelineIOConfig)

    def get_source(self, name: str) -> DataSourceConfig:
        for source in self.sources:
            if source.name == name:
                return source
        raise KeyError(f"Unknown source '{name}'")

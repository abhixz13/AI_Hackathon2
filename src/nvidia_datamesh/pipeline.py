"""Pipeline orchestration for NVIDIA DataMesh."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List

import daft

from .config import PipelineConfig
from .ingestion import APIIngestionSource, BaseIngestionSource, CSVIngestionSource
from .transformations import align_schema

_SOURCE_REGISTRY = {
    "csv": CSVIngestionSource,
    "jsonl": CSVIngestionSource,
    "rest": APIIngestionSource,
}


class DataMeshPipeline:
    """Coordinated ETL workflow that merges multiple sources into a Daft DataFrame."""

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.workspace_dir = Path(config.io.workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _create_source(self, type_name: str, name: str, params: Dict[str, str]) -> BaseIngestionSource:
        try:
            source_cls = _SOURCE_REGISTRY[type_name]
        except KeyError as exc:  # pragma: no cover - configuration errors
            raise ValueError(f"Unsupported source type {type_name}") from exc
        return source_cls(name=name, params=params)

    def _load_sources(self) -> Iterable[daft.DataFrame]:
        for source_cfg in self.config.sources:
            adapter = self._create_source(source_cfg.type, source_cfg.name, source_cfg.params)
            yield adapter.to_daft_dataframe()

    def build_dataframe(self) -> daft.DataFrame:
        """Load, union, and align sources into a single DataFrame."""

        frames: List[daft.DataFrame] = [align_schema(df, self.config.schema) for df in self._load_sources()]
        return daft.concat(frames)

    def export(self) -> Path:
        """Persist the pipeline output to disk for LLM training workflows."""

        df = self.build_dataframe()
        output_path = self.workspace_dir / f"dataset.{self.config.io.output_format}"
        if self.config.io.output_format == "parquet":
            df.write_parquet(str(output_path))
        else:
            df.write_json(str(output_path))
        return output_path

"""LLM-ready dataset utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import daft

from .pipeline import DataMeshPipeline


@dataclass
class LLMDataExportConfig:
    """Describe how to prepare records for LLM pre-training or fine-tuning."""

    text_column: str
    metadata_columns: Optional[list[str]] = None
    max_records: Optional[int] = None
    prompt_template: str = "{text}"


def export_llm_ready_dataset(
    pipeline: DataMeshPipeline,
    export_config: LLMDataExportConfig,
    output_path: Optional[Path] = None,
) -> Path:
    """Run the pipeline, format prompts, and emit JSONL for training."""

    df = pipeline.build_dataframe()
    if export_config.max_records:
        df = df.limit(export_config.max_records)

    def _format_prompt(row: Dict[str, str]) -> str:
        text = row.get(export_config.text_column, "")
        metadata = {col: row.get(col) for col in (export_config.metadata_columns or [])}
        return export_config.prompt_template.format(text=text, **metadata)

    df = df.with_column("prompt", daft.udf(lambda row: _format_prompt(row))(daft.col("__row__")))
    result_path = output_path or pipeline.workspace_dir / "llm_dataset.jsonl"
    df.select(["prompt"]).write_json(str(result_path))
    return result_path

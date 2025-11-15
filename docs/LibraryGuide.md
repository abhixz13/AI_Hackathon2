# NVIDIA DataMesh Library – Implementation Guide

## Overview
DataMesh is a Python package that centralizes ETL logic for multimodal corpora inside NVIDIA.
It orchestrates ingestion, schema alignment, and export flows with the Daft DataFrame API.

## Installation
```bash
pip install -e .
```

## Configuration Model
Configurations are expressed via `PipelineConfig` objects (can be loaded from YAML/JSON). Key
sections include:

- `sources`: list of dictionaries describing ingestion adapters. Each entry must declare
  `name`, `type` (`csv`, `jsonl`, or `rest`), and `params`.
- `schema`: mapping of source columns to harmonized names using `SchemaField` entries.
- `io`: workspace directory, desired output format (`parquet` or `jsonl`), and optional
  remote URI to upload artifacts (future release).

### Example YAML
```yaml
sources:
  - name: catalog_file
    type: csv
    params:
      path: data/catalog.csv
      format: csv
  - name: partner_api
    type: rest
    params:
      endpoint: https://api.partner/corpus
      page_size: 200
      max_pages: 5
schema:
  primary_key: content_id
  fields:
    - source: id
      target: content_id
      dtype: string
    - source: description
      target: text
      dtype: string
io:
  workspace_dir: ./artifacts
  output_format: parquet
```

## Usage Patterns
```python
from pathlib import Path
import yaml
from nvidia_datamesh.config import PipelineConfig
from nvidia_datamesh.pipeline import DataMeshPipeline
from nvidia_datamesh.llm_preparation import LLMDataExportConfig, export_llm_ready_dataset

config = PipelineConfig(**yaml.safe_load(Path("config.yaml").read_text()))
pipeline = DataMeshPipeline(config)

# Export harmonized dataset
parquet_path = pipeline.export()

# Produce LLM-ready prompts
llm_config = LLMDataExportConfig(
    text_column="text",
    metadata_columns=["content_id"],
    prompt_template="Instruction: {text}\nID: {content_id}"
)
jsonl_path = export_llm_ready_dataset(pipeline, llm_config)
```

## Extensibility
- **New sources**: subclass `BaseIngestionSource` and register it inside `_SOURCE_REGISTRY` in
  `pipeline.py`.
- **Transformations**: add helper functions under `nvidia_datamesh.transformations` and invoke
  them within the pipeline before export.
- **Metadata**: extend `SchemaField` to include validators for modality-specific rules.

## Operational Guidance
- Maintain configurations in version control to trace provenance of exported corpora.
- Use Daft's lazy execution to scale when integrating with RAPIDS-powered clusters.
- Ensure API adapters respect NVIDIA security policies (e.g., TLS enforcement, token rotation).

## Roadmap Notes
- v1.1: Add GPU-accelerated image embeddings using Daft's multimodal operators.
- v1.2: Introduce connectors for data warehouse tables (Snowflake, BigQuery).

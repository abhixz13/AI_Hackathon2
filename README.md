# NVIDIA DataMesh Library

Version 1.0.0

NVIDIA DataMesh is an internal Python library that standardizes multimodal ETL pipelines
using [Daft](https://www.getdaft.io/) to orchestrate tabular, text, and vision data. It is
built for the NVIDIA research and product teams who need to consolidate training corpora
from heterogeneous sources before fine-tuning large language models (LLMs).

## Key Capabilities
- **Multi-source ingestion**: Pull batched data from REST APIs, data lakes, and curated CSVs.
- **Schema harmonization**: Normalize record layouts and metadata via declarative alignment rules.
- **Multimodal fusion**: Convert text, tabular features, and image references into Daft DataFrames
  that can be joined for downstream LLM pre-processing.
- **LLM-prep workflows**: Reusable pipeline templates help feature teams export parquet or JSONL
  corpora that comply with NVIDIA's training contracts.

Refer to the documentation in the `docs/` folder for the Product Requirements Document (PRD)
and detailed library usage guides.

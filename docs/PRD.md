# Product Requirements Document (PRD)

## Product Name
**NVIDIA DataMesh Library** – Version 1.0.0

## Vision
Equip NVIDIA product and research teams with a unified, multimodal ETL foundation that
streamlines the creation of curated corpora for internal LLM training. The library must
provide predictable ingestion, schema harmonization, and export flows that shrink the
onboarding time for new data sources from weeks to days.

## Objectives & Key Results
1. **Centralized ingestion** of at least three heterogeneous sources (CSV/JSONL, REST API).
2. **Schema harmonization** declaratively configured through metadata files.
3. **LLM-ready exports** supporting JSONL and Parquet drop zones for downstream model training.
4. **Extensible architecture** so additional connectors can be added with <2 days of effort.

## Assumptions
- Teams operate in secured NVIDIA environments with access to Daft runtimes.
- Source systems provide pull-based access and authentication tokens managed elsewhere.
- Data privacy reviews are completed before configuring the pipeline.

## User Stories
1. **As an Applied Scientist**, I want to register a new dataset by providing its schema and
   endpoint information so that I can merge it with existing corpora for instruction tuning.
2. **As a Data Engineer**, I want to run a repeatable job that publishes a parquet file into
   the training bucket to avoid manual data wrangling steps.
3. **As a Research PM**, I want documentation that shows how the ETL pipeline aligns with
   model contract requirements so I can approve data releases quickly.

## Functional Requirements
- Provide configuration schema covering sources, schema alignment, and IO targets.
- Offer ingestion adapters for CSV/JSONL files and paginated REST APIs.
- Enforce schema alignment by renaming/casting columns within Daft DataFrames.
- Export pipelines to Parquet or JSONL, as well as dedicated JSONL prompt files for LLMs.
- Capture workspace artifacts under a user-provided directory to support auditing.

## Non-Functional Requirements
- Pipelines must be deterministic: identical configurations yield identical outputs.
- Code must be modular and typed to enable static analysis and internal security reviews.
- Runtime must not assume public internet connectivity beyond configured API endpoints.
- Library should be dependency-light to embed in air-gapped clusters.

## Milestones
1. **M0 – Architecture Complete**: Config schema, ingestion abstraction, transformation API.
2. **M1 – Prototype Ready**: CSV + REST connectors, schema alignment, export path.
3. **M2 – Production Beta**: LLM export helpers, PRD + docs baseline, integration guidelines.

## Open Questions
- How should authentication secrets be provided (Vault vs. env vars)?
- Which additional modalities (images, speech) are highest priority for v1.1?

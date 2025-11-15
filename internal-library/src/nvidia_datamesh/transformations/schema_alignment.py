"""Schema harmonization helpers."""

from __future__ import annotations

from typing import Dict

import daft

from ..config import SchemaConfig


_DAFT_TYPE_MAP: Dict[str, daft.DataType] = {
    "string": daft.DataType.string(),
    "int": daft.DataType.int64(),
    "float": daft.DataType.float64(),
    "bool": daft.DataType.bool(),
}


def align_schema(df: daft.DataFrame, schema: SchemaConfig) -> daft.DataFrame:
    """Rename and cast columns according to the schema definition."""

    for field in schema.fields:
        if field.source not in df.column_names():
            df = df.with_column(field.source, daft.lit(None))
        df = df.rename({field.source: field.target})
        df = df.cast({field.target: _DAFT_TYPE_MAP.get(field.dtype, daft.DataType.string())})
    return df

"""CSV ingestion source."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import daft

from .base_source import BaseIngestionSource


class CSVIngestionSource(BaseIngestionSource):
    """Create a Daft DataFrame from CSV or JSONL files."""

    def __init__(
        self,
        name: str,
        params: Dict[str, Any],
    ) -> None:
        super().__init__(name, params)
        self.path = Path(params.get("path", ""))
        self.format = params.get("format", "csv")
        self.columns: Optional[List[str]] = params.get("columns")

    def to_daft_dataframe(self) -> daft.DataFrame:
        if not self.path.exists():
            raise FileNotFoundError(f"{self.path} was not found for source {self.name}")
        if self.format == "csv":
            df = daft.read_csv(str(self.path), columns=self.columns)
        elif self.format == "jsonl":
            df = daft.read_json(str(self.path))
        else:
            raise ValueError("CSVIngestionSource supports only 'csv' or 'jsonl'")
        return df

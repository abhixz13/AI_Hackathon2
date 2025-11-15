"""REST API ingestion source."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

import daft
import requests

from .base_source import BaseIngestionSource


class APIIngestionSource(BaseIngestionSource):
    """Pull batched JSON payloads from a REST endpoint and convert to Daft DataFrame."""

    def __init__(self, name: str, params: Dict[str, Any]):
        super().__init__(name, params)
        self.endpoint = params["endpoint"]
        self.headers = params.get("headers", {})
        self.batch_param = params.get("batch_param", "page")
        self.page_size = int(params.get("page_size", 100))
        self.max_pages = int(params.get("max_pages", 10))

    def to_daft_dataframe(self) -> daft.DataFrame:
        records: List[Dict[str, Any]] = []
        for payload in self._paginate():
            if isinstance(payload, dict):
                records.append(payload)
            elif isinstance(payload, list):
                records.extend(payload)
            else:
                raise ValueError("API responses must be list or dict of JSON objects")
        return daft.from_pylist(records)

    def _paginate(self) -> Iterable[Any]:
        for page in range(1, self.max_pages + 1):
            response = requests.get(
                self.endpoint,
                headers=self.headers,
                params={self.batch_param: page, "page_size": self.page_size},
                timeout=30,
            )
            response.raise_for_status()
            payload = response.json()
            if not payload:
                break
            yield payload

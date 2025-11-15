"""Base ingestion source."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict

import daft


class BaseIngestionSource(ABC):
    """Abstract base class for all ingestion sources."""

    def __init__(self, name: str, params: Dict[str, Any]):
        self.name = name
        self.params = params

    @abstractmethod
    def to_daft_dataframe(self) -> daft.DataFrame:
        """Return a Daft DataFrame for the source."""

    def __repr__(self) -> str:  # pragma: no cover - convenience
        return f"{self.__class__.__name__}(name={self.name!r})"

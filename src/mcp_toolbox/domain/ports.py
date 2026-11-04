"""Ports the application depends on."""

from __future__ import annotations

from typing import Protocol

from mcp_toolbox.domain.models import BoeDocument


class DocumentSource(Protocol):
    def all_documents(self) -> tuple[BoeDocument, ...]: ...

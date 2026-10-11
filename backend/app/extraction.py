"""Format-independent extraction contract and explicit adapter registration."""
from collections.abc import Callable, Iterable, Mapping
from typing import Protocol

from .models import NormalizedDocument

ProgressCallback = Callable[..., None]


class DocumentAdapter(Protocol):
    @property
    def extensions(self) -> tuple[str, ...]: ...
    @property
    def content_type(self) -> str: ...

    def validate(self, content: bytes) -> None:
        """Reject unreadable content; raise DocumentTooLarge for expansion limits."""
        ...

    def extract(self, content: bytes, result: NormalizedDocument, progress: ProgressCallback) -> None:
        """Append canonical output incrementally so failures retain partial results."""
        ...


class DocumentTooLarge(ValueError):
    """A format-specific expansion limit was exceeded."""


class AdapterRegistry:
    def __init__(self, adapters: Iterable[DocumentAdapter], *, aliases: Mapping[str, str] | None = None):
        self._extensions: dict[str, DocumentAdapter] = {}
        self._content_types: dict[str, DocumentAdapter] = {}
        for adapter in adapters:
            if adapter.content_type in self._content_types:
                raise ValueError(f'Duplicate content type: {adapter.content_type}')
            self._content_types[adapter.content_type] = adapter
            for extension in adapter.extensions:
                extension = extension.lower()
                if extension in self._extensions:
                    raise ValueError(f'Duplicate extension: {extension}')
                self._extensions[extension] = adapter
        for alias, content_type in (aliases or {}).items():
            if alias in self._content_types:
                raise ValueError(f'Duplicate content type: {alias}')
            self._content_types[alias] = self.for_content_type(content_type)

    @property
    def extensions(self) -> tuple[str, ...]:
        return tuple(self._extensions)

    def for_extension(self, extension: str) -> DocumentAdapter:
        try:
            return self._extensions[extension.lower()]
        except KeyError:
            raise ValueError(f'Unsupported extension: {extension}') from None

    def for_content_type(self, content_type: str) -> DocumentAdapter:
        try:
            return self._content_types[content_type]
        except KeyError:
            raise ValueError(f'Unsupported content type: {content_type}') from None

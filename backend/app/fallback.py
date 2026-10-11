"""Optional specialist extraction boundary. The bundled provider returns a demo fixture or a generic mock acknowledgement."""
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol
import json

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .models import ProviderInfo


@dataclass(frozen=True)
class FallbackRequest:
    # A real adapter sends only page_pdf to its service; the hash selects demo fixtures.
    page_pdf: bytes
    document_sha256: str
    original_page: int
    reason: str
    timeout_seconds: float = 30.0


class FallbackBlock(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    type: Literal['paragraph', 'table']
    text: str = Field(default='', max_length=100_000)
    rows: list[list[str]] = Field(default_factory=list, max_length=1000)

    @model_validator(mode='after')
    def usable_content(self):
        if self.type == 'paragraph':
            if not self.text.strip() or self.rows:
                raise ValueError('Paragraphs require text and no table rows')
        elif (self.text or not self.rows or not self.rows[0]
              or any(len(row) != len(self.rows[0]) for row in self.rows)
              or not any(cell.strip() for row in self.rows for cell in row)):
            raise ValueError('Tables require nonempty rectangular rows and no paragraph text')
        return self


class FallbackResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    blocks: list[FallbackBlock] = Field(max_length=200)
    note: str | None = Field(default=None, max_length=2000)


class FallbackProvider(Protocol):
    info: ProviderInfo

    def extract(self, request: FallbackRequest) -> dict:
        """Return untrusted structured data; a network adapter must enforce the timeout.

        Raise TimeoutError for deadlines and other exceptions for service errors.
        The caller validates the entire response before adding any blocks.
        """
        ...


class MockAiExtractor:
    info = ProviderInfo(name='mock_ai_extractor', version='mock-v2', mocked=True)

    def __init__(self):
        self.fixture = json.loads((Path(__file__).parent / 'fixtures' / 'ai_fallback.json').read_text())

    def extract(self, request: FallbackRequest) -> dict:
        if (request.document_sha256 == self.fixture['document_sha256']
                and request.original_page == self.fixture['page']):
            return self.fixture['response']
        generic = self.fixture['default_response']
        return {
            **generic,
            'note': generic['note'].format(page=request.original_page, reason=request.reason),
        }

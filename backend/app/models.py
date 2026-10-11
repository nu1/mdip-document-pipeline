"""Canonical content is authoritative; rendered text and chunks are derived."""
from typing import Literal
from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    page: int | None = None
    block_index: int | None = None
    paragraph_index: int | None = None
    bbox: tuple[float, float, float, float] | None = None


class ProviderInfo(BaseModel):
    name: str
    version: str
    mocked: bool


class FallbackAttempt(BaseModel):
    reason: str
    provider: ProviderInfo
    note: str | None = None
    status: Literal['running', 'succeeded', 'no_content', 'fixture_not_found', 'timeout', 'invalid_response', 'failed'] = 'running'


class Block(BaseModel):
    type: Literal['heading', 'paragraph', 'table']
    order: int
    text: str = ''
    level: int | None = None
    rows: list[list[str]] = Field(default_factory=list)
    source_location: SourceLocation
    extraction_method: Literal['native_docx', 'native_pdf', 'ocr', 'mock_ocr', 'ai_extractor', 'mock_ai']
    provider: ProviderInfo | None = None


class PageSignals(BaseModel):
    char_count: int = 0
    word_count: int = 0
    usable_text: bool = False
    text_quality_ratio: float = 0
    largest_image_ratio: float = 0
    substantial_image_count: int = 0
    uncovered_image_boxes: list[tuple[float, float, float, float]] = Field(default_factory=list)


class RouteDecision(BaseModel):
    page: int
    route: Literal['NATIVE', 'OCR', 'HYBRID', 'EMPTY_OR_UNKNOWN']
    reason: str
    signals: PageSignals
    fallback: FallbackAttempt | None = None
    warnings: list[str] = Field(default_factory=list)


class NormalizedDocument(BaseModel):
    document_id: str
    filename: str
    content_type: str
    blocks: list[Block] = Field(default_factory=list)
    page_routes: list[RouteDecision] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def block_text(block: Block) -> str:
    if block.type == 'table':
        return '\n'.join(' | '.join(cell.replace('\n', ' / ') for cell in row) for row in block.rows)
    return block.text


def render_for_agent(document: NormalizedDocument) -> str:
    parts = []
    for block in document.blocks:
        location = block.source_location
        if location.page is not None:
            label = f'Page {location.page}'
        elif location.block_index is not None:
            label = f'Body block {location.block_index + 1}'
        else:
            label = f'Block {block.order + 1}'
        text = block_text(block)
        if block.extraction_method == 'mock_ai' or (block.provider and block.provider.mocked):
            text = 'This is a mock response for demonstration; no external service was called.\n' + text
        if block.type == 'heading':
            text = '#' * (block.level or 1) + ' ' + text
        parts.append(f'[{label} · {block.extraction_method}]\n{text}')
    for route in document.page_routes:
        if route.fallback and route.fallback.note:
            parts.append(f'[Page {route.page} · specialist fallback notice]\n{route.fallback.note}')
    return '\n\n'.join(parts)


def build_chunks(document: NormalizedDocument) -> list[dict]:
    return [
        {'chunk_index': index, 'text': block_text(block),
         'source_location': block.source_location.model_dump(exclude_none=True),
         'metadata': {'block_order': block.order, 'type': block.type, 'extraction_method': block.extraction_method,
                      **({'provider': block.provider.model_dump()} if block.provider else {})}}
        for index, block in enumerate(b for b in document.blocks if block_text(b).strip())
    ]

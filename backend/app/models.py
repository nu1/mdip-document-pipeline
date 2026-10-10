"""Canonical content is authoritative; rendered text and chunks are derived."""
from typing import Literal
from pydantic import BaseModel, Field


class SourceLocation(BaseModel):
    page: int | None = None
    block_index: int | None = None
    paragraph_index: int | None = None
    bbox: tuple[float, float, float, float] | None = None


class Block(BaseModel):
    type: Literal['heading', 'paragraph', 'table']
    order: int
    text: str = ''
    level: int | None = None
    rows: list[list[str]] = Field(default_factory=list)
    source_location: SourceLocation
    extraction_method: Literal['native_docx', 'native_pdf', 'ocr', 'mock_ocr']


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
        label = f'Page {location.page}' if location.page else f'DOCX block {location.block_index}'
        text = block_text(block)
        if block.type == 'heading':
            text = '#' * (block.level or 1) + ' ' + text
        parts.append(f'[{label} · {block.extraction_method}]\n{text}')
    return '\n\n'.join(parts)


def build_chunks(document: NormalizedDocument) -> list[dict]:
    return [
        {'chunk_index': index, 'text': block_text(block),
         'source_location': block.source_location.model_dump(exclude_none=True),
         'metadata': {'block_order': block.order, 'type': block.type, 'extraction_method': block.extraction_method}}
        for index, block in enumerate(b for b in document.blocks if block_text(b).strip())
    ]

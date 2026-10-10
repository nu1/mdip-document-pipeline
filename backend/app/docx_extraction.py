from io import BytesIO
import re
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from .models import Block, NormalizedDocument, SourceLocation


def extract_docx(content: bytes, result: NormalizedDocument) -> None:
    document = Document(BytesIO(content))
    paragraph_index = 0
    for block_index, element in enumerate(document.element.body):
        location = SourceLocation(block_index=block_index)
        if element.tag.endswith('}p'):
            paragraph = Paragraph(element, document)
            location.paragraph_index = paragraph_index
            paragraph_index += 1
            text = paragraph.text
            if not text.strip():
                continue
            match = re.fullmatch(r'Heading (\d+)', paragraph.style.name if paragraph.style else '')
            result.blocks.append(Block(type='heading' if match else 'paragraph', order=len(result.blocks),
                                       text=text, level=int(match[1]) if match else None,
                                       source_location=location, extraction_method='native_docx'))
        elif element.tag.endswith('}tbl'):
            table = Table(element, document)
            result.blocks.append(Block(type='table', order=len(result.blocks),
                                       rows=[[cell.text for cell in row.cells] for row in table.rows],
                                       source_location=location, extraction_method='native_docx'))
    # Body-only extraction intentionally omits these structures; make loss visible.
    tags = {e.tag.rsplit('}', 1)[-1] for e in document.element.body.iter()}
    if tags & {'drawing', 'pict', 'txbxContent', 'sdt', 'altChunk', 'ins', 'del'}:
        result.warnings.append('docx_unsupported_content: images, text boxes or tracked/embedded content may be omitted')
    if any(len(cell.tables) for table in document.tables for row in table.rows for cell in row.cells):
        result.warnings.append('docx_nested_tables_omitted')
    if not result.blocks:
        result.warnings.append('no_extractable_body_text')

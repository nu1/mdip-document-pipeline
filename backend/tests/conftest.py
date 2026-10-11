from io import BytesIO
from typing import Literal
import pytest
from docx import Document


@pytest.fixture
def docx_bytes():
    document = Document()
    document.add_heading('Agreement', 1)
    document.add_paragraph('Terms of the agreement.')
    table = document.add_table(rows=2, cols=2)
    for row, values in zip(table.rows, [('Item', 'Amount'), ('Fee', '£100')]):
        for cell, text in zip(row.cells, values):
            cell.text = text
    document.add_paragraph('Payment is due within 30 days.')
    output = BytesIO()
    document.save(output)
    return output.getvalue()


@pytest.fixture
def pdf_bytes():
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), 'Terms of the PDF agreement.')
    output = doc.tobytes()
    doc.close()
    return output


@pytest.fixture
def scan_image():
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB', (900, 1200), 'white')
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=44)
    draw.text((70, 180), 'FLETCHERS SCAN TEST', fill='black', font=font)
    draw.text((70, 260), 'Invoice total 125 pounds', fill='black', font=font)
    stream = BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


@pytest.fixture
def mixed_pdf(scan_image):
    import pymupdf
    with pymupdf.open() as document:
        page = document.new_page(width=450, height=600)
        page.insert_text((30, 50), 'Agreement', fontsize=20)
        page = document.new_page(width=450, height=600)
        page.insert_image(page.rect, stream=scan_image)
        page = document.new_page(width=450, height=600)
        page.insert_text((30, 50), 'Native terms above an image', fontsize=14)
        page.insert_image(pymupdf.Rect(30, 200, 420, 570), stream=scan_image)
        page = document.new_page(width=450, height=600)
        page.insert_image(page.rect, stream=scan_image)
        page.insert_text((40, 100), 'Plausible searchable scan text layer', fontsize=14)
        document.new_page(width=450, height=600)
        return document.tobytes()


class MockOcr:
    method: Literal['mock_ocr'] = 'mock_ocr'

    def __init__(self, available: bool = True, text: str = 'FLETCHERS SCAN TEST\nInvoice total 125 pounds'):
        self._available = available
        self._text = text

    def available(self) -> bool:
        return self._available

    def recognize(self, image) -> str:
        return self._text


@pytest.fixture
def mock_ocr():
    return MockOcr()



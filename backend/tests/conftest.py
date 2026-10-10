from io import BytesIO
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

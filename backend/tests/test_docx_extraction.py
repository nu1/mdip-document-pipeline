from app.docx_extraction import extract_docx
from app.models import NormalizedDocument


def test_docx_order(docx_bytes):
    result = NormalizedDocument(document_id='test', filename='test.docx', content_type='docx')
    extract_docx(docx_bytes, result)
    assert [b.type for b in result.blocks] == ['heading', 'paragraph', 'table', 'paragraph']
    assert result.blocks[0].level == 1
    assert result.blocks[2].rows == [['Item', 'Amount'], ['Fee', '£100']]
    assert [b.source_location.block_index for b in result.blocks] == [0, 1, 2, 3]
    assert all(b.source_location.page is None and b.extraction_method == 'native_docx' for b in result.blocks)

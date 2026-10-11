from fastapi.testclient import TestClient
from app.main import create_app
from app.storage import SQLiteRepository


def test_upload_persistence_and_restart(tmp_path, docx_bytes):
    with TestClient(create_app(tmp_path)) as client:
        response = client.post('/documents', files={'file': ('../../agreement.docx', docx_bytes)})
        assert response.status_code == 202
        assert response.json()['status'] == 'queued'
        document_id = response.json()['id']
        result = client.get('/documents/' + document_id).json()
        assert result['status'] == 'completed'
        assert result['filename'] == 'agreement.docx'
        assert len(result['extracted_data']['blocks']) == 4
        assert 'Fee | £100' in result['rendered_text']
        assert 'storage_uri' not in result
        assert (tmp_path / 'originals' / document_id).read_bytes() == docx_bytes
        assert client.get('/documents').json()[0]['id'] == document_id
    with TestClient(create_app(tmp_path)) as client:
        assert client.get('/documents/' + document_id).json() == result
    repository = SQLiteRepository(tmp_path / 'documents.db')
    chunks = repository.chunks(document_id, limit=20, offset=0)
    assert len(chunks) == 4
    assert chunks[2]['source_location'] == {'block_index': 2}
    repository.replace_chunks(document_id, chunks)
    assert repository.chunks(document_id, limit=20, offset=0) == chunks


def test_validation_and_missing_document(tmp_path, docx_bytes):
    with TestClient(create_app(tmp_path, max_upload_bytes=len(docx_bytes))) as client:
        assert client.post('/documents', files={'file': ('test.docx', docx_bytes)}).status_code == 202
        for name, content, code in [('bad.txt', b'text', 415), ('bad.docx', b'not a zip', 422),
                                    ('bad.pdf', b'not a pdf', 422), ('bad.pdf', b'%PDF-broken', 422),
                                    ('empty.pdf', b'', 422),
                                    ('zero_page.pdf', b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF', 422),
                                    ('big.docx', docx_bytes + b'x', 413)]:
            assert client.post('/documents', files={'file': (name, content)}).status_code == code
        assert client.get('/documents/missing').status_code == 404
        assert client.get('/documents?limit=0').status_code == 422
        assert client.get('/documents?offset=1').json() == []


def test_pdf_upload_and_extraction(tmp_path, pdf_bytes):
    with TestClient(create_app(tmp_path)) as client:
        response = client.post('/documents', files={'file': ('agreement.pdf', pdf_bytes)})
        assert response.status_code == 202
        assert response.json()['status'] == 'queued'
        document_id = response.json()['id']
        result = client.get('/documents/' + document_id).json()
        assert result['status'] == 'completed'
        assert result['filename'] == 'agreement.pdf'
        assert result['content_type'] == 'application/pdf'
        assert len(result['extracted_data']['blocks']) >= 1
        assert 'Terms of the PDF agreement.' in result['rendered_text']
        assert (tmp_path / 'originals' / document_id).read_bytes() == pdf_bytes


def test_mixed_pdf_upload_and_e2e_pipeline(tmp_path, mixed_pdf, mock_ocr):
    with TestClient(create_app(tmp_path, ocr=mock_ocr)) as client:
        response = client.post('/documents', files={'file': ('mixed_contract.pdf', mixed_pdf)})
        assert response.status_code == 202
        assert response.json()['status'] == 'queued'
        document_id = response.json()['id']

        result = client.get('/documents/' + document_id).json()
        assert result['status'] == 'completed_with_warnings'
        assert result['filename'] == 'mixed_contract.pdf'
        assert result['content_type'] == 'application/pdf'

        assert '[Page 1 · native_pdf]' in result['rendered_text']
        assert '[Page 2 · mock_ocr]' in result['rendered_text']
        assert 'FLETCHERS SCAN TEST' in result['rendered_text']

        repository = SQLiteRepository(tmp_path / 'documents.db')
        chunks = repository.chunks(document_id, limit=20, offset=0)
        assert len(chunks) == 4
        assert chunks[1]['metadata']['extraction_method'] == 'mock_ocr'
        assert chunks[1]['source_location'] == {'page': 2}



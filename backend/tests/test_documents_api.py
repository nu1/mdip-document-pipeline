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
    chunks = repository.chunks(document_id)
    assert len(chunks) == 4
    assert chunks[2]['source_location'] == {'block_index': 2}
    repository.replace_chunks(document_id, chunks)
    assert repository.chunks(document_id) == chunks


def test_validation_and_missing_document(tmp_path, docx_bytes):
    with TestClient(create_app(tmp_path, max_upload_bytes=len(docx_bytes))) as client:
        assert client.post('/documents', files={'file': ('test.docx', docx_bytes)}).status_code == 202
        for name, content, code in [('bad.txt', b'text', 415), ('bad.docx', b'not a zip', 422),
                                    ('bad.pdf', b'not a pdf', 415), ('bad.pdf', b'%PDF-broken', 415),
                                    ('empty.docx', b'', 422), ('big.docx', docx_bytes + b'x', 413)]:
            assert client.post('/documents', files={'file': (name, content)}).status_code == code
        assert client.get('/documents/missing').status_code == 404
        assert client.get('/documents?limit=0').status_code == 422
        assert client.get('/documents?offset=1').json() == []

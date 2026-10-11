import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.models import NormalizedDocument
from app.storage import SQLiteRepository


def test_ordered_docx_batches_and_final_offsets(tmp_path, docx_bytes):
    with TestClient(create_app(tmp_path)) as client:
        document_id = client.post('/documents', files={'file': ('agreement.docx', docx_bytes)}).json()['id']
        path = f'/documents/{document_id}/chunks'
        first = client.get(path, params={'limit': 2}).json()
        assert first['document_id'] == document_id
        assert first['filename'] == 'agreement.docx'
        assert first['status'] == 'completed'
        assert first['processing_stage'] == 'done'
        assert first['error_message'] is None
        assert first['warnings'] == []
        assert first['next_offset'] == 2
        second = client.get(path, params={'offset': first['next_offset'], 'limit': 2}).json()
        assert second['next_offset'] is None  # A full final batch is still final.
        chunks = first['chunks'] + second['chunks']
        assert [c['chunk_index'] for c in chunks] == [0, 1, 2, 3]
        assert chunks == SQLiteRepository(tmp_path / 'documents.db').chunks(document_id, 20, 0)
        tail = client.get(path, params={'offset': 3, 'limit': 3}).json()
        assert [c['chunk_index'] for c in tail['chunks']] == [3]
        assert tail['next_offset'] is None
        beyond = client.get(path, params={'offset': 4}).json()
        assert beyond['chunks'] == []
        assert beyond['next_offset'] is None


def test_pdf_provenance_and_warnings_are_persisted(tmp_path, mixed_pdf, mock_ocr):
    with TestClient(create_app(tmp_path, ocr=mock_ocr)) as client:
        document_id = client.post('/documents', files={'file': ('mixed.pdf', mixed_pdf)}).json()['id']
        detail = client.get(f'/documents/{document_id}').json()
        response = client.get(f'/documents/{document_id}/chunks', params={'limit': 20})
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'completed_with_warnings'
        assert result['warnings'] == detail['extracted_data']['warnings']
        assert result['warnings']
        # Compare entire stored chunks to cover text, IDs, provenance and methods.
        assert result['chunks'] == SQLiteRepository(tmp_path / 'documents.db').chunks(document_id, 20, 0)
        last = client.get(f'/documents/{document_id}/chunks', params={'offset': 3}).json()
        assert last['warnings'] == result['warnings']
        assert last['next_offset'] is None


@pytest.mark.parametrize(('status', 'stage'), [
    ('queued', 'queued'), ('processing', 'extracting'),
    ('failed', 'failed'), ('completed_with_warnings', 'done'),
])
def test_empty_chunks_do_not_imply_success(tmp_path, status, stage):
    app = create_app(tmp_path)
    with TestClient(app) as client:
        repository = app.state.repository
        repository.create({'id': 'unfinished', 'filename': 'unfinished.pdf', 'content_type': 'application/pdf', 'storage_uri': 'unused'})
        warnings = ['Page 1: ocr_unavailable'] if status != 'queued' else []
        error = 'Extraction failed. Partial results retained.' if status == 'failed' else None
        repository.update('unfinished', status=status, processing_stage=stage, error_message=error,
                          extracted_data=NormalizedDocument(document_id='unfinished', filename='unfinished.pdf',
                                                            content_type='application/pdf', warnings=warnings).model_dump())
        result = client.get('/documents/unfinished/chunks').json()
        assert result['status'] == status
        assert result['processing_stage'] == stage
        assert result['warnings'] == warnings
        assert result['error_message'] == error
        assert result['chunks'] == []
        assert result['next_offset'] is None

        if status == 'failed':
            repository.replace_chunks('unfinished', [{'chunk_index': 0, 'text': 'Partial text',
                'source_location': {'page': 1}, 'metadata': {'extraction_method': 'native_pdf', 'block_order': 0, 'type': 'paragraph'}}])
            partial = client.get('/documents/unfinished/chunks').json()
            assert partial['status'] == 'failed'
            assert partial['error_message'] == error
            assert partial['warnings'] == warnings
            assert partial['chunks'][0]['text'] == 'Partial text'


@pytest.mark.parametrize('query', ['limit=0', 'limit=21', 'offset=-1', 'limit=no'])
def test_invalid_chunk_pagination(tmp_path, query):
    with TestClient(create_app(tmp_path)) as client:
        assert client.get(f'/documents/missing/chunks?{query}').status_code == 422


def test_missing_document(tmp_path):
    with TestClient(create_app(tmp_path)) as client:
        response = client.get('/documents/missing/chunks')
        assert response.status_code == 404
        assert response.json() == {'detail': 'Document not found.'}


def test_repository_orders_before_pagination(tmp_path):
    repository = SQLiteRepository(tmp_path / 'documents.db')
    repository.create({'id': 'ordered', 'filename': 'a.docx', 'content_type': 'docx', 'storage_uri': 'unused'})
    rows = [{'chunk_index': i, 'text': str(i), 'source_location': {'block_index': i},
             'metadata': {'extraction_method': 'native_docx'}} for i in [7, 1, 4]]
    repository.replace_chunks('ordered', rows)
    assert [c['chunk_index'] for c in repository.chunks('ordered', limit=2, offset=0)] == [1, 4]
    assert [c['chunk_index'] for c in repository.chunks('ordered', limit=2, offset=2)] == [7]

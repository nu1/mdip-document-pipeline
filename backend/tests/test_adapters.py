from fastapi.testclient import TestClient

from app.adapters import DocxAdapter, PdfAdapter
from app.extraction import AdapterRegistry
from app.main import create_app
from app.models import Block, SourceLocation


class FixtureAdapter:
    """Test-only format with explicitly mocked output; never registered by default."""
    extensions = ('.fixture',)
    content_type = 'application/x-test-document'

    def __init__(self, fail=False):
        self.fail = fail

    def validate(self, content):
        if content != b'fixture':
            raise ValueError('Invalid fixture')

    def extract(self, content, result, progress):
        result.blocks.append(Block(
            type='paragraph', order=0, text='Mock extracted content',
            source_location=SourceLocation(block_index=0), extraction_method='mock_ocr',
        ))
        result.warnings.append('mock_ocr: test fixture output, not real recognition')
        progress(processing_stage='extracting', extracted_data=result.model_dump(exclude_none=True))
        if self.fail:
            raise RuntimeError('Fixture extraction failed after its first block')


def test_third_adapter_uses_upload_processing_storage_and_retrieval(tmp_path):
    registry = AdapterRegistry((PdfAdapter(), DocxAdapter(), FixtureAdapter()))
    with TestClient(create_app(tmp_path, adapters=registry)) as client:
        invalid = client.post('/documents', files={'file': ('bad.fixture', b'invalid')})
        assert invalid.status_code == 422
        assert client.get('/documents').json() == []

        response = client.post('/documents', files={
            'file': ('example.fixture', b'fixture'),
        })
        assert response.status_code == 202
        document_id = response.json()['id']
        result = client.get(f'/documents/{document_id}').json()
        assert result['status'] == 'completed_with_warnings'
        assert result['content_type'] == FixtureAdapter.content_type
        assert result['rendered_text'] == '[Body block 1 · mock_ocr]\nMock extracted content'
        chunks = client.get(f'/documents/{document_id}/chunks').json()
        assert chunks['warnings'] == result['extracted_data']['warnings']
        assert len(chunks['chunks']) == 1
        assert chunks['chunks'][0]['text'] == 'Mock extracted content'
        assert chunks['chunks'][0]['source_location'] == {'block_index': 0}
        assert chunks['chunks'][0]['metadata']['extraction_method'] == 'mock_ocr'


def test_adapter_failure_retains_partial_output(tmp_path):
    with TestClient(create_app(tmp_path, adapters=AdapterRegistry((FixtureAdapter(fail=True),)))) as client:
        document_id = client.post('/documents', files={'file': ('test.fixture', b'fixture')}).json()['id']
        result = client.get(f'/documents/{document_id}').json()
        assert result['status'] == 'failed'
        assert result['extracted_data']['blocks'][0]['text'] == 'Mock extracted content'
        assert result['error_message']
        assert client.get(f'/documents/{document_id}/chunks').json()['chunks'] == []


def test_docx_expansion_limit_still_returns_413(tmp_path, docx_bytes, monkeypatch):
    monkeypatch.setattr('app.adapters.MAX_UNPACKED_DOCX', 1)
    with TestClient(create_app(tmp_path)) as client:
        response = client.post('/documents', files={'file': ('test.docx', docx_bytes)})
        assert response.status_code == 413
        assert 'archive limits' in response.json()['detail']
        assert client.get('/documents').json() == []

from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.fallback import MockAiExtractor
from app.main import create_app
from app.models import NormalizedDocument, ProviderInfo
from app.pdf_extraction import extract_pdf
from tests.conftest import MockOcr

DEMO = Path(__file__).resolve().parents[2] / 'demo' / 'ai-fallback.pdf'


class RecordingFallback:
    info = ProviderInfo(name='test_specialist', version='v1', mocked=True)

    def __init__(self, response=None, error=None):
        self.requests = []
        self.response = response if response is not None else {'blocks': [{'type': 'paragraph', 'text': 'Recovered fixture text'}]}
        self.error = error

    def extract(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


class BrokenOcr(MockOcr):
    def recognize(self, image):
        raise RuntimeError('private provider details')


def run(content, ocr=None, fallback=None):
    result = NormalizedDocument(document_id='test', filename='test.pdf', content_type='application/pdf')
    updates = []
    extract_pdf(content, result, ocr, lambda **data: updates.append(data), fallback)
    return result, updates


@pytest.mark.parametrize('ocr,reason', [
    (None, 'ocr_unavailable'),
    (MockOcr(text=''), 'ocr_no_text'),
    (BrokenOcr(), 'ocr_failed'),
])
def test_ocr_fallback_sends_one_page_and_preserves_local_results(mixed_pdf, ocr, reason):
    provider = RecordingFallback()
    result, updates = run(mixed_pdf, ocr, provider)
    assert len(provider.requests) == 1
    request = provider.requests[0]
    assert (request.original_page, request.reason) == (2, reason)
    with pymupdf.open(stream=request.page_pdf, filetype='pdf') as sent:
        assert sent.page_count == 1
        assert sent[0].get_image_info()
    assert [b.source_location.page for b in result.blocks] == [1, 2, 3, 4]
    assert result.blocks[1].provider == provider.info
    assert result.blocks[1].extraction_method == 'mock_ai'
    assert result.page_routes[1].route == 'OCR'
    assert result.page_routes[1].fallback.status == 'succeeded'
    assert any(u.get('processing_stage') == 'ai_fallback' for u in updates)
    assert updates[-1]['processed_pages'] == 5


def test_successful_ocr_and_warning_counts_do_not_trigger_fallback(mixed_pdf):
    provider = RecordingFallback()
    result, _ = run(mixed_pdf, MockOcr(), provider)
    assert result.warnings  # HYBRID, searchable-scan and blank-page warnings.
    assert provider.requests == []


@pytest.mark.parametrize('response,error,status', [
    (None, TimeoutError('private timeout detail'), 'timeout'),
    ({'blocks': [{'type': 'paragraph', 'text': 'valid'},
                 {'type': 'table', 'rows': [['a'], ['b', 'c']]}]}, None, 'invalid_response'),
])
def test_failed_fallback_does_not_add_partial_response_or_stop_later_pages(mixed_pdf, response, error, status):
    result, updates = run(mixed_pdf, fallback=RecordingFallback(response, error))
    assert [b.source_location.page for b in result.blocks] == [1, 3, 4]
    assert result.page_routes[1].fallback.status == status
    assert any(f'ai_fallback_{status}' in w for w in result.warnings)
    assert 'private' not in str(result.model_dump())
    assert updates[-1]['processed_pages'] == 5


def test_demo_opt_in_unknown_page_blank_skip_and_persisted_provenance(tmp_path):
    content = DEMO.read_bytes()
    with TestClient(create_app(settings=Settings(data_dir=tmp_path, ai_fallback='disabled'))) as client:
        document_id = client.post('/documents', files={'file': ('demo.pdf', content)}).json()['id']
        result = client.get('/documents/' + document_id).json()
        assert all(r.get('fallback') is None for r in result['extracted_data']['page_routes'])
    with TestClient(create_app(settings=Settings(data_dir=tmp_path, ai_fallback='mock'))) as client:
        document_id = client.post('/documents', files={'file': ('renamed.pdf', content)}).json()['id']
        result = client.get('/documents/' + document_id).json()
        assert result['status'] == 'completed_with_warnings'
        assert result['processed_pages'] == 3
        routes = result['extracted_data']['page_routes']
        assert [r['route'] for r in routes] == ['NATIVE', 'EMPTY_OR_UNKNOWN', 'EMPTY_OR_UNKNOWN']
        assert routes[1]['fallback']['reason'] == 'unknown_with_content'
        assert routes[1]['fallback']['status'] == 'succeeded'
        assert routes[2].get('fallback') is None
        assert '[Page 2 · mock_ai]' in result['rendered_text']
        assert 'This is a mock response for demonstration; no external service was called.' in result['rendered_text']
        chunks = client.get(f'/documents/{document_id}/chunks').json()['chunks']
        assert chunks[-1]['metadata']['provider']['mocked'] is True
        assert chunks[-1]['source_location'] == {'page': 2}
        assert chunks[-1]['text'] == 'Label | Value\nTOTAL | 125'
    with TestClient(create_app(settings=Settings(data_dir=tmp_path, ai_fallback='disabled'))) as client:
        assert client.get('/documents/' + document_id).json() == result


def test_other_documents_get_generic_notice_without_placeholder_chunks(tmp_path, mixed_pdf):
    with TestClient(create_app(tmp_path, ocr=MockOcr(available=False), fallback=MockAiExtractor())) as client:
        document_id = client.post('/documents', files={'file': ('other.pdf', mixed_pdf)}).json()['id']
        result = client.get('/documents/' + document_id).json()
        attempt = result['extracted_data']['page_routes'][1]['fallback']
        assert attempt['status'] == 'no_content'
        assert 'This is a mock response' in attempt['note']
        assert 'page 2 (trigger: ocr_unavailable)' in attempt['note']
        assert attempt['note'] in result['rendered_text']
        chunks = client.get(f'/documents/{document_id}/chunks').json()['chunks']
        assert [chunk['source_location']['page'] for chunk in chunks] == [1, 3, 4]
        assert all('This is a mock response' not in chunk['text'] for chunk in chunks)

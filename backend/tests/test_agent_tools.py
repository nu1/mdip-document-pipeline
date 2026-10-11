import io
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from examples import agent_tools


def test_functions_and_example_against_http_contract(tmp_path, docx_bytes, monkeypatch, capsys):
    # In-process HTTP transport: exercise the real routes without a network service.
    monkeypatch.setenv('MDIP_API_BASE_URL', 'http://mdip.test/')
    with TestClient(create_app(tmp_path)) as client:
        document_id = client.post('/documents', files={'file': ('example.docx', docx_bytes)}).json()['id']
        calls = []

        def local_urlopen(url, timeout):
            parsed = urlsplit(url)
            assert parsed.netloc == 'mdip.test'
            path = f'{parsed.path}?{parsed.query}'
            calls.append(path)
            response = client.get(path)
            if response.is_error:
                raise HTTPError(url, response.status_code, response.reason_phrase, {}, io.BytesIO(response.content))
            return io.BytesIO(response.content)

        monkeypatch.setattr(agent_tools, 'urlopen', local_urlopen)
        assert agent_tools.list_documents(limit=1, offset=0)[0]['id'] == document_id
        assert agent_tools.list_documents(limit=1, offset=1) == []
        assert agent_tools.read_document_chunks(document_id) == client.get(f'/documents/{document_id}/chunks').json()
        with pytest.raises(HTTPError) as missing:
            agent_tools.read_document_chunks('missing')
        assert missing.value.code == 404
        assert json.load(missing.value) == {'detail': 'Document not found.'}
        calls.clear()
        monkeypatch.setattr('sys.argv', ['agent_tools.py', '--document-id', document_id, '--limit', '2'])
        agent_tools.main()
        assert calls == ['/documents?limit=20&offset=0',
                         f'/documents/{document_id}/chunks?limit=2&offset=0',
                         f'/documents/{document_id}/chunks?limit=2&offset=2']
        assert 'Continuation at offset 2:' in capsys.readouterr().out


def test_example_empty_library(monkeypatch, capsys):
    monkeypatch.setattr('sys.argv', ['agent_tools.py'])
    monkeypatch.setattr(agent_tools, 'list_documents', lambda: [])
    agent_tools.main()
    assert 'No documents yet.' in capsys.readouterr().out

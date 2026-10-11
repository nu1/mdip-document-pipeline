import { useEffect, useRef, useState } from "react";
import { getDocumentChunks } from "../../api/documents";
import type { DocumentChunksResponse } from "../../types/document";
import { formatSourceLocation, prettyText } from "../../utils/formatters";
import { Badge } from "../common/Badge";
import { ExtractionWarnings } from "../workspace/ExtractionWarnings";

// App keys this component by selectedId so changing documents resets the preview.
export function ForAgents({ selectedId }: { selectedId: string | null }) {
  const [offset, setOffset] = useState(0);
  const [response, setResponse] = useState<DocumentChunksResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const request = useRef<AbortController | null>(null);
  const limit = 5;
  const args = { document_id: selectedId, offset, limit };
  const requestJson = JSON.stringify({ name: "read_document_chunks", arguments: args }, null, 2);
  const responseJson = response ? JSON.stringify(response, null, 2) : "";

  useEffect(() => () => request.current?.abort(), []);

  async function preview(nextOffset = offset) {
    if (!selectedId) return;
    request.current?.abort();
    const controller = new AbortController();
    request.current = controller;
    setOffset(nextOffset);
    setLoading(true);
    setError("");
    setResponse(null);
    setCopyMessage("");
    try {
      const result = await getDocumentChunks(selectedId, { offset: nextOffset, limit }, controller.signal);
      if (!controller.signal.aborted) setResponse(result);
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : "Unable to preview chunks.");
      }
    } finally {
      if (!controller.signal.aborted) setLoading(false);
    }
  }

  async function copy(text: string, label: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopyMessage(`${label} copied.`);
    } catch {
      setCopyMessage("Clipboard unavailable. Select and copy the JSON manually.");
    }
  }

  return (
    <section className="workspace agents" aria-labelledby="agents-title">
      <h2 id="agents-title">For Agents</h2>
      <p>Two callable tools give a host application access to already-extracted document content.</p>
      <ul className="agent-tools">
        <li><code>list_documents(limit=20, offset=0)</code> lists IDs, filenames and processing states. The document library uses this API.</li>
        <li><code>read_document_chunks(document_id, offset=0, limit=5)</code> reads persisted chunks in their original order, with source locations and extraction warnings.</li>
      </ul>
      <p className="muted">No model is connected. This preview makes a real REST request; it does not demonstrate autonomous tool selection.</p>

      {!selectedId ? (
        <p role="status" className="agent-empty">Select a document from the library to preview its chunks. If the library is empty, upload a PDF or DOCX first.</p>
      ) : (
        <>
          <h3>read_document_chunks arguments</h3>
          <pre aria-label="Tool request">{requestJson}</pre>
          <div className="agent-actions">
            <button className="button" disabled={loading} onClick={() => void preview()}>
              {loading ? "Loading…" : "Preview response"}
            </button>
            <button disabled={loading} onClick={() => void copy(requestJson, "Request")}>Copy request</button>
            {offset > 0 && <button disabled={loading} onClick={() => void preview(0)}>Start from beginning</button>}
          </div>
          {loading && <p role="status">Loading persisted chunks…</p>}
          {error && <div className="error" role="alert">{error} Use Preview response to retry.</div>}
          {response && (
            <div aria-label="Chunk response">
              <h3>{response.filename}</h3>
              <div className="status-line">
                <Badge status={response.status} />
                <span>Stage: {prettyText(response.processing_stage)}</span>
              </div>
              {!['completed', 'completed_with_warnings'].includes(response.status) && (
                <p className="warning-text">Extraction has not completed successfully. Any available chunks may be partial. Preview again to check the current state.</p>
              )}
              {response.error_message && <p className="error" role="alert">{response.error_message}</p>}
              <ExtractionWarnings warnings={response.warnings} />
              {response.chunks.length === 0 && <p>No persisted chunks at this offset. Check the document status and extraction notes above.</p>}
              {response.chunks.map(chunk => (
                <article className="block" key={chunk.id}>
                  <div className="block-label">
                    <span>{formatSourceLocation(chunk.source_location)} · {prettyText(chunk.metadata.extraction_method)}</span>
                    <span>Chunk index {chunk.chunk_index}</span>
                  </div>
                  <p>{chunk.text}</p>
                  <small className="muted">ID: {chunk.id}</small>
                </article>
              ))}
              <div className="agent-actions">
                {response.next_offset !== null ? (
                  <button className="button" onClick={() => void preview(response.next_offset!)}>Read next batch</button>
                ) : <p className="muted">No further persisted chunks. This does not by itself indicate successful extraction.</p>}
                <button onClick={() => void copy(responseJson, "Response")}>Copy JSON response</button>
              </div>
              <details>
                <summary>JSON response</summary>
                <pre aria-label="JSON response">{responseJson}</pre>
              </details>
            </div>
          )}
          <p role="status" className="muted">{copyMessage}</p>
        </>
      )}

      <details className="agent-integration">
        <summary>Integration example and API instructions</summary>
        <p>Use the standard-library Python functions and JSON argument schemas in <code>examples/agent_tools.py</code> as building blocks for a host to register. From the repository root, with the backend running:</p>
        <pre>{'python3 examples/agent_tools.py --limit 2\npython3 examples/agent_tools.py --document-id DOCUMENT_ID --limit 2'}</pre>
        <p>The example lists documents, reads the chosen document, and follows <code>next_offset</code> for a second batch when present. Calls are deterministic; no model chooses tools.</p>
        <pre>{'GET /documents?limit=20&offset=0\nGET /documents/{document_id}/chunks?offset=0&limit=5'}</pre>
        <p>Python defaults to <code>http://127.0.0.1:8000</code>. Set <code>MDIP_API_BASE_URL</code> to change it. Document limits are 1–100; chunk limits are 1–20. Offsets are non-negative. Invalid pagination returns 422; a missing document returns 404.</p>
        <p>Read status, warnings and error_message before using chunks. Extraction methods stay in chunk metadata; PDF pages and DOCX body positions stay in source_location.</p>
      </details>
      <p className="muted">Retrieval is sequential, not relevance-ranked. A chunk limit does not guarantee a model token budget. Extraction warnings remain relevant to any downstream answer.</p>
    </section>
  );
}

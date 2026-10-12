import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ForAgents } from "./ForAgents";
import type { DocumentChunksResponse } from "../../types/document";

const firstBatch: DocumentChunksResponse = {
  document_id: "doc-1",
  filename: "contract.pdf",
  status: "completed_with_warnings",
  processing_stage: "done",
  warnings: ["Page 3: hybrid_partial"],
  error_message: null,
  chunks: [
    {
      id: "doc-1:0",
      document_id: "doc-1",
      chunk_index: 0,
      text: "Original terms.",
      source_location: { page: 2, bbox: [1, 2, 3, 4] },
      metadata: {
        extraction_method: "native_pdf",
        block_order: 0,
        type: "paragraph",
      },
    },
  ],
  next_offset: 5,
};

const secondBatch: DocumentChunksResponse = {
  document_id: "doc-1",
  filename: "contract.pdf",
  status: "completed_with_warnings",
  processing_stage: "done",
  warnings: ["Page 3: hybrid_partial"],
  error_message: null,
  chunks: [
    {
      id: "doc-1:5",
      document_id: "doc-1",
      chunk_index: 5,
      text: "Final paragraph.",
      source_location: { block_index: 8, paragraph_index: 6 },
      metadata: {
        extraction_method: "native_docx",
        block_order: 8,
        type: "paragraph",
      },
    },
  ],
  next_offset: null,
};

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status });
}

const fetchMock = vi.fn<typeof fetch>();
const writeTextMock = vi.fn().mockResolvedValue(undefined);

beforeEach(() => {
  fetchMock.mockReset();
  writeTextMock.mockReset();
  vi.stubGlobal("fetch", fetchMock);
  Object.defineProperty(navigator, "clipboard", {
    configurable: true,
    value: { writeText: writeTextMock },
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("ForAgents tool preview", () => {
  it("renders the empty state explanation when no document is selected", () => {
    render(<ForAgents selectedId={null} />);

    expect(screen.getByText(/Select a document from the library/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Preview response" })).toBeNull();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fetches and renders extracted chunks, provenance, and warnings", async () => {
    let resolveResponse!: (response: Response) => void;
    fetchMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveResponse = resolve;
      }),
    );

    render(<ForAgents selectedId="doc-1" />);

    expect(screen.getByLabelText("Tool request").textContent).toContain('"offset": 0');

    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));

    expect(screen.getByText("Loading persisted chunks…")).toBeTruthy();
    expect(
      (screen.getByRole("button", { name: "Loading…" }) as HTMLButtonElement).disabled,
    ).toBe(true);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/documents/doc-1/chunks?offset=0&limit=5",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );

    await act(async () => {
      resolveResponse(jsonResponse(firstBatch));
    });

    expect(screen.getByText("Original terms.")).toBeTruthy();
    expect(screen.getByText("Page 2 · native pdf")).toBeTruthy();
    expect(screen.getByText("Page 3: hybrid partial")).toBeTruthy();
    expect(screen.getByText("completed with warnings")).toBeTruthy();
  });

  it("copies request arguments and response JSON to the clipboard", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(firstBatch));

    render(<ForAgents selectedId="doc-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));
    await screen.findByText("Original terms.");

    fireEvent.click(screen.getByRole("button", { name: "Copy request" }));
    await screen.findByText("Request copied.");
    expect(JSON.parse(writeTextMock.mock.calls[0][0])).toEqual({
      name: "read_document_chunks",
      arguments: { document_id: "doc-1", offset: 0, limit: 5 },
    });

    fireEvent.click(screen.getByRole("button", { name: "Copy JSON response" }));
    await screen.findByText("Response copied.");
    expect(JSON.parse(writeTextMock.mock.calls[1][0])).toEqual(firstBatch);
  });

  it("paginates through chunks and allows resetting to the first batch", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(firstBatch));

    render(<ForAgents selectedId="doc-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));
    await screen.findByText("Original terms.");

    // Fetch next batch using next_offset (5)
    fetchMock.mockResolvedValueOnce(jsonResponse(secondBatch));
    fireEvent.click(screen.getByRole("button", { name: "Read next batch" }));

    await screen.findByText("Final paragraph.");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/documents/doc-1/chunks?offset=5&limit=5",
      expect.anything(),
    );
    expect(screen.getByLabelText("Tool request").textContent).toContain('"offset": 5');
    expect(screen.getByText("Body block 9 · native docx")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Read next batch" })).toBeNull();
    expect(screen.queryByText("Original terms.")).toBeNull();

    // Reset pagination to offset 0
    fetchMock.mockResolvedValueOnce(jsonResponse(firstBatch));
    fireEvent.click(screen.getByRole("button", { name: "Start from beginning" }));

    await screen.findByText("Original terms.");
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/documents/doc-1/chunks?offset=0&limit=5",
      expect.anything(),
    );
  });

  it.each(["processing", "failed"])(
    "warns user and does not present empty %s state as successful extraction",
    async (status) => {
      fetchMock.mockResolvedValueOnce(
        jsonResponse({
          ...firstBatch,
          status,
          processing_stage: status,
          chunks: [],
          next_offset: null,
          error_message: status === "failed" ? "Extraction failed." : null,
        }),
      );

      render(<ForAgents selectedId="doc-1" />);
      fireEvent.click(screen.getByRole("button", { name: "Preview response" }));

      await screen.findByText(/Extraction has not completed successfully/);
      expect(screen.getByText(/No persisted chunks at this offset/)).toBeTruthy();

      if (status === "failed") {
        expect(screen.getByRole("alert").textContent).toBe("Extraction failed.");
      }
    },
  );

  it("displays error messages on network or HTTP failure and recovers after retry", async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: "Document not found." }, 404));

    render(<ForAgents selectedId="missing" />);
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Document not found.");

    fetchMock.mockRejectedValueOnce(new Error("Network unavailable"));
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));
    await screen.findByText(/Network unavailable/);

    fetchMock.mockResolvedValueOnce(jsonResponse(firstBatch));
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));
    await screen.findByText("Original terms.");
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("discards inflight chunk requests when document selection changes", async () => {
    let resolveSlowRequest!: (response: Response) => void;
    fetchMock.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveSlowRequest = resolve;
      }),
    );

    const view = render(<ForAgents key="doc-1" selectedId="doc-1" />);
    fireEvent.click(screen.getByRole("button", { name: "Preview response" }));

    // User switches to doc-2 before doc-1 responds
    view.rerender(<ForAgents key="doc-2" selectedId="doc-2" />);

    await act(async () => {
      resolveSlowRequest(jsonResponse(firstBatch));
    });

    expect(screen.queryByText("Original terms.")).toBeNull();
    expect(screen.getByLabelText("Tool request").textContent).toContain('"document_id": "doc-2"');
    expect(screen.getByLabelText("Tool request").textContent).toContain('"offset": 0');
  });
});

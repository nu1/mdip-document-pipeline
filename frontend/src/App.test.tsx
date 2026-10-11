import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { App } from "./App";

const document = {
  id: "saved", filename: "saved.docx", status: "completed", processing_stage: "done",
  processed_pages: null, total_pages: null, created_at: "2026-10-11T10:00:00Z", error_message: null,
  rendered_text: "Saved extracted text", extracted_data: { blocks: [{ type: "paragraph", order: 0, text: "Saved extracted text",
    source_location: { block_index: 0 }, extraction_method: "native_docx" }], page_routes: [], warnings: [] },
};
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("reuses library selection across navigation and keeps upload/progress/results available", async () => {
  let uploaded = false;
  const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
    let body: unknown;
    if (options?.method === "POST") { uploaded = true; body = { id: "new", status: "queued" }; }
    else if (url === "/api/health") body = { max_upload_bytes: 10485760 };
    else if (url.startsWith("/api/documents?")) body = [document];
    else if (url === "/api/documents/saved") body = document;
    else if (url === "/api/documents/new") body = { ...document, id: "new", filename: "new.docx", status: "processing", extracted_data: null };
    else throw new Error(`Unexpected request ${url}`);
    return new Response(JSON.stringify(body));
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: /saved.docx/ }));
  await screen.findByText("Saved extracted text");
  fireEvent.click(screen.getByRole("button", { name: "For Agents" }));
  expect(screen.getByLabelText("Tool request").textContent).toContain('"document_id": "saved"');
  fireEvent.click(screen.getByRole("button", { name: "Documents" }));
  expect(screen.getByText("Saved extracted text")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "For Agents" }));
  fireEvent.change(screen.getByLabelText("Upload DOCX or PDF document"), {
    target: { files: [new File(["fixture"], "new.docx")] },
  });
  await waitFor(() => expect(uploaded).toBe(true));
  await screen.findByRole("heading", { name: "new.docx" });
  expect(screen.getByRole("button", { name: "Documents" }).getAttribute("aria-pressed")).toBe("true");
  expect(screen.queryByRole("heading", { name: "For Agents" })).toBeNull();
  expect(screen.getByText("Processing document. Status updates automatically.")).toBeTruthy();
});

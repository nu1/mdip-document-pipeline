import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import { PageRoutesView } from "./PageRoutesView";
import { StructuredBlocksView } from "./StructuredBlocksView";

const provider = { name: "mock_ai_extractor", version: "mock-v2", mocked: true };
afterEach(cleanup);

it("labels mock content explicitly and keeps its page and original route visible", () => {
  render(<>
    <PageRoutesView routes={[{ page: 2, route: "EMPTY_OR_UNKNOWN", reason: "no_usable_text",
      signals: {}, warnings: [], fallback: { reason: "unknown_with_content", provider, status: "succeeded" } }]} />
    <StructuredBlocksView blocks={[{ type: "table", order: 0, text: "", rows: [["TOTAL", "125"]],
      source_location: { page: 2 }, extraction_method: "mock_ai", provider }]} />
  </>);
  expect(screen.getByText("EMPTY OR UNKNOWN")).toBeTruthy();
  expect(screen.getByText("AI fallback (mock): succeeded")).toBeTruthy();
  expect(screen.getByText("Page 2 · mock ai")).toBeTruthy();
  expect(screen.getByText(/This is a mock response for demonstration; no external service was called/)).toBeTruthy();
  expect(screen.getByRole("cell", { name: "125" })).toBeTruthy();
});

it("shows a generic mock notice once even when no content was recovered", () => {
  const note = "This is a mock response for demonstration; page 2 received no extracted document content.";
  render(<PageRoutesView routes={[{ page: 2, route: "OCR", reason: "raster_content",
    signals: {}, warnings: [`ai_fallback_note: ${note}`], fallback: { reason: "ocr_unavailable", provider, status: "no_content", note } }]} />);
  expect(screen.getByText("AI fallback (mock): no content")).toBeTruthy();
  expect(screen.getAllByText(note)).toHaveLength(1);
});

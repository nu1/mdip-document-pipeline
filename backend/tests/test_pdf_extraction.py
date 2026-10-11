import pymupdf
from app.models import NormalizedDocument
from app.pdf_extraction import extract_pdf, inspect_page, render_for_ocr
from app.routing import choose_route
from tests.conftest import MockOcr


def test_pdf_routing_decisions(mixed_pdf):
    with pymupdf.open(stream=mixed_pdf, filetype='pdf') as document:
        routes = [choose_route(inspect_page(page), index + 1) for index, page in enumerate(document)]

    assert [r.route for r in routes] == ['NATIVE', 'OCR', 'HYBRID', 'NATIVE', 'EMPTY_OR_UNKNOWN']
    assert routes[0].reason == 'usable_native_text_without_uncovered_image_candidates'
    assert routes[0].warnings == []

    assert routes[1].reason == 'substantial_raster_without_usable_native_text'
    assert routes[1].warnings == []

    assert routes[2].reason == 'native_text_with_uncovered_image_candidates'
    assert 'hybrid_partial' in routes[2].warnings[0]

    assert routes[3].reason == 'usable_text_over_dominant_image'
    assert 'searchable_scan_candidate' in routes[3].warnings[0]

    assert routes[4].reason == 'no_usable_text_or_substantial_raster'
    assert 'empty_or_unknown' in routes[4].warnings[0]


def test_pdf_extraction_with_mock_ocr(mixed_pdf, mock_ocr):
    result = NormalizedDocument(document_id='test-pdf', filename='mixed.pdf', content_type='application/pdf')
    progress_updates = []

    extract_pdf(mixed_pdf, result, mock_ocr, lambda **kwargs: progress_updates.append(kwargs))

    assert len(result.page_routes) == 5
    assert [r.route for r in result.page_routes] == ['NATIVE', 'OCR', 'HYBRID', 'NATIVE', 'EMPTY_OR_UNKNOWN']
    assert len(result.blocks) == 4

    assert result.blocks[0].source_location.page == 1
    assert result.blocks[0].extraction_method == 'native_pdf'
    assert 'Agreement' in result.blocks[0].text

    assert result.blocks[1].source_location.page == 2
    assert result.blocks[1].extraction_method == 'mock_ocr'
    assert 'FLETCHERS SCAN TEST' in result.blocks[1].text

    assert result.blocks[2].source_location.page == 3
    assert result.blocks[2].extraction_method == 'native_pdf'
    assert 'Native terms above an image' in result.blocks[2].text

    assert result.blocks[3].source_location.page == 4
    assert result.blocks[3].extraction_method == 'native_pdf'
    assert 'Plausible searchable scan text layer' in result.blocks[3].text

    assert any('Page 2: mock_ocr' in w for w in result.warnings)
    assert any('Page 3: hybrid_partial' in w for w in result.warnings)
    assert any('Page 4: searchable_scan_candidate' in w for w in result.warnings)
    assert any('Page 5: empty_or_unknown' in w for w in result.warnings)
    assert len(progress_updates) > 0


def test_pdf_extraction_without_ocr_provider(mixed_pdf):
    result = NormalizedDocument(document_id='test-no-ocr', filename='mixed.pdf', content_type='application/pdf')
    extract_pdf(mixed_pdf, result, None, lambda **kwargs: None)

    # Page 2 has no OCR provider, so only 3 native text blocks are extracted
    assert len(result.blocks) == 3
    assert [b.source_location.page for b in result.blocks] == [1, 3, 4]
    assert any('ocr_unavailable: no OCR provider configured' in w for w in result.warnings)


def test_pdf_extraction_ocr_unavailable(mixed_pdf):
    result = NormalizedDocument(document_id='test-unavail', filename='mixed.pdf', content_type='application/pdf')
    extract_pdf(mixed_pdf, result, MockOcr(available=False), lambda **kwargs: None)

    assert len(result.blocks) == 3
    assert any('ocr_unavailable: OCR provider is not available' in w for w in result.warnings)


def test_render_for_ocr_dimensions(mixed_pdf):
    with pymupdf.open(stream=mixed_pdf, filetype='pdf') as document:
        raster = render_for_ocr(document.load_page(1))
        assert raster.mode == 'RGB'
        assert raster.width > 0 and raster.height > 0
        raster.close()

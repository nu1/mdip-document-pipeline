"""Native inspection → pure routing → execution. Only OCR execution renders."""
from collections.abc import Callable
import math
import unicodedata
from threading import RLock
import pymupdf
from PIL import Image
from .models import Block, NormalizedDocument, PageSignals, SourceLocation
from .ocr import OcrProvider
from .routing import choose_route, SUBSTANTIAL_IMAGE_RATIO, MIN_TEXT_QUALITY, MIN_IMAGE_TEXT_ENVELOPE

# Shared with upload validation to serialize all MuPDF access in this process.
PDF_LOCK = RLock()

ProgressCallback = Callable[..., None]

def inspect_page(page) -> PageSignals:
    # 1. Visible page boundaries (derotated to account for page rotation)
    visible_page = page.rect * page.derotation_matrix

    # 2. Extract words and filter to those within visible page bounds.
    # Explicit flags prevent image extraction in text APIs; no pixels or OCR here.
    raw_words = page.get_text('words', flags=pymupdf.TEXTFLAGS_WORDS & ~pymupdf.TEXT_PRESERVE_IMAGES)
    visible_words = []
    for w in raw_words:
        word_box = pymupdf.Rect(w[:4])
        if (word_box & visible_page).get_area() > 0:
            midpoint = pymupdf.Point((word_box.x0 + word_box.x1) / 2, (word_box.y0 + word_box.y1) / 2)
            visible_words.append((word_box, str(w[4]), midpoint))

    # 3. Text quality and usability evaluation
    text = ''.join(word_text for _, word_text, _ in visible_words)
    # Check printable characters while excluding replacement chars (\ufffd) and Unicode control codes (category 'C*')
    valid_chars = sum(
        c.isprintable() and c != '\ufffd' and not unicodedata.category(c).startswith('C')
        for c in text
    )
    quality = valid_chars / len(text) if text else 0.0
    usable = quality >= MIN_TEXT_QUALITY and any(c.isalnum() for c in text)

    # 4. Image inspection and text coverage heuristic
    page_area = max(visible_page.get_area(), 1.0)
    image_ratios, uncovered_image_boxes = [], []
    substantial_image_count = 0

    for img in page.get_image_info(hashes=False, xrefs=False):
        # Clip image bounding box to visible page
        image_box = pymupdf.Rect(img['bbox']) & visible_page
        ratio = image_box.get_area() / page_area
        image_ratios.append(ratio)

        if ratio < SUBSTANTIAL_IMAGE_RATIO:
            continue
        substantial_image_count += 1

        # Find words whose center points fall inside the image box
        words_inside = [
            word_box for word_box, _, midpoint in visible_words
            if image_box.contains(midpoint)
        ]

        # Calculate bounding envelope (union of word boxes) as a spatial proxy for searchable scans
        word_envelope = pymupdf.Rect()
        for word_box in words_inside:
            word_envelope |= word_box

        # An envelope requires at least 3 words and sufficient area coverage (>= 15%)
        overlap_area = (word_envelope & image_box).get_area()
        coverage_ratio = overlap_area / max(image_box.get_area(), 1.0)
        is_covered = len(words_inside) >= 3 and coverage_ratio >= MIN_IMAGE_TEXT_ENVELOPE

        if not is_covered:
            uncovered_image_boxes.append(tuple(image_box))

    return PageSignals(
        char_count=len(text),
        word_count=len(visible_words),
        usable_text=usable,
        text_quality_ratio=quality,
        largest_image_ratio=max(image_ratios, default=0.0),
        substantial_image_count=substantial_image_count,
        uncovered_image_boxes=uncovered_image_boxes,
    )


def native_blocks(page, page_number: int, result: NormalizedDocument) -> None:
    for item in page.get_text('blocks', sort=True, flags=pymupdf.TEXTFLAGS_BLOCKS & ~pymupdf.TEXT_PRESERVE_IMAGES):
        if item[6] == 0 and item[4].strip():
            result.blocks.append(Block(type='paragraph', order=len(result.blocks), text=item[4].strip(),
                                       extraction_method='native_pdf', source_location=SourceLocation(page=page_number, bbox=tuple(item[:4]))))


def render_for_ocr(page) -> Image.Image:
    # Bounded 150dpi RGB raster. This function is called only after the OCR decision.
    scale = min(150 / 72, math.sqrt(16_000_000 / max(page.rect.get_area(), 1)))
    pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csRGB, alpha=False)
    return Image.frombytes('RGB', (pixmap.width, pixmap.height), pixmap.samples)


def extract_pdf(
    content: bytes,
    result: NormalizedDocument,
    ocr: OcrProvider | None,
    progress: ProgressCallback,
) -> None:
    provider = ocr
    with PDF_LOCK:
        document = pymupdf.open(stream=content, filetype='pdf')
        total = document.page_count
    try:
        progress(processing_stage='inspecting', processed_pages=0, total_pages=total)
        for index in range(total):
            progress(processing_stage='inspecting')
            with PDF_LOCK:
                page = document.load_page(index)
                decision = choose_route(inspect_page(page), index + 1)
            result.page_routes.append(decision)
            progress(processing_stage='extracting')
            if decision.route in {'NATIVE', 'HYBRID'}:
                with PDF_LOCK:
                    native_blocks(page, index + 1, result)
            elif decision.route == 'OCR':
                if provider is None:
                    decision.warnings.append('ocr_unavailable: no OCR provider configured to extract this page')
                elif not provider.available():
                    decision.warnings.append('ocr_unavailable: OCR provider is not available to extract this page')
                else:
                    progress(processing_stage='ocr')
                    with PDF_LOCK:
                        image = render_for_ocr(page)
                    try:
                        text = provider.recognize(image).strip()
                    finally:
                        image.close()
                    if provider.method == 'mock_ocr':
                        decision.warnings.append('mock_ocr: deterministic test fixture, not real recognition')
                    if text:
                        result.blocks.append(Block(type='paragraph', order=len(result.blocks), text=text,
                                                   extraction_method=provider.method,
                                                   source_location=SourceLocation(page=index + 1)))
                    else:
                        decision.warnings.append('ocr_no_text: no text recognised; image may contain no text')
            result.warnings.extend(f'Page {index + 1}: {warning}' for warning in decision.warnings)
            progress(processed_pages=index + 1, extracted_data=result.model_dump(exclude_none=True))
    finally:
        with PDF_LOCK:
            document.close()

"""Pure application policy. Ratios below are heuristics, never confidence scores."""
from .models import PageSignals, RouteDecision

# Ignore small logos; a dominant image can be a searchable scanned page.
SUBSTANTIAL_IMAGE_RATIO = 0.12
FULL_PAGE_IMAGE_RATIO = 0.85
MIN_TEXT_QUALITY = 0.8
MIN_IMAGE_TEXT_ENVELOPE = 0.15


def choose_route(signals: PageSignals, page: int = 1) -> RouteDecision:
    warnings = []
    if signals.usable_text:
        if signals.largest_image_ratio >= FULL_PAGE_IMAGE_RATIO:
            route, reason = 'NATIVE', 'usable_text_over_dominant_image'
            warnings.append('searchable_scan_candidate: image/text equivalence is unverified')
        elif signals.uncovered_image_boxes:
            route, reason = 'HYBRID', 'native_text_with_uncovered_image_candidates'
            warnings.append('hybrid_partial: native text retained; candidate images were not OCRed or merged')
        else:
            route, reason = 'NATIVE', 'usable_native_text_without_uncovered_image_candidates'
    elif signals.substantial_image_count:
        route, reason = 'OCR', 'substantial_raster_without_usable_native_text'
    else:
        route, reason = 'EMPTY_OR_UNKNOWN', 'no_usable_text_or_substantial_raster'
        warnings.append('empty_or_unknown: blank, vector-only or unsupported content may be present')
    return RouteDecision(page=page, route=route, reason=reason, signals=signals, warnings=warnings)

"""The real adapter never invents text. Test fakes must use method='mock_ocr'."""
import shutil
from typing import Protocol, Literal, cast
from PIL import Image
import pytesseract


class OcrProvider(Protocol):
    @property
    def method(self) -> Literal['ocr', 'mock_ocr']: ...
    def available(self) -> bool: ...
    def recognize(self, image: Image.Image) -> str: ...


class TesseractProvider:
    method: Literal['ocr'] = 'ocr'

    def available(self) -> bool:
        if not shutil.which('tesseract'):
            return False
        try:
            return 'eng' in pytesseract.get_languages(config='')
        except (OSError, RuntimeError, pytesseract.TesseractError):
            return False

    def recognize(self, image: Image.Image) -> str:
        return cast(str, pytesseract.image_to_string(image, lang='eng', timeout=60))


def init_ocr() -> OcrProvider:
    """Instantiate and return the default OCR engine."""
    return TesseractProvider()

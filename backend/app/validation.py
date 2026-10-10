from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile
import unicodedata
from docx import Document
from fastapi import HTTPException

MAX_UNPACKED_DOCX = 40 * 1024 * 1024


def validate_upload(filename: str, content: bytes) -> tuple[str, str]:
    name = PurePosixPath(filename.replace('\\', '/')).name
    name = ''.join(c for c in name if not unicodedata.category(c).startswith('C'))[:240]
    extension = PurePosixPath(name).suffix.lower()
    if extension not in {'.docx'}:
        raise HTTPException(415, 'Only DOCX files are supported.')
    if not content:
        raise HTTPException(422, 'The uploaded file is empty.')
    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 2000 or sum(e.file_size for e in entries) > MAX_UNPACKED_DOCX:
                raise HTTPException(413, 'DOCX expands beyond the supported archive limits.')
            if 'word/document.xml' not in archive.namelist() or '[Content_Types].xml' not in archive.namelist():
                raise ValueError('Missing OOXML document')
            if any(e.flag_bits & 1 for e in entries):
                raise ValueError('Encrypted archive')
        Document(BytesIO(content))
        return name, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(422, 'Invalid, encrypted or unreadable DOCX file.') from error

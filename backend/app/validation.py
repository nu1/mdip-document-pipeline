from io import BytesIO
from pathlib import PurePosixPath
from zipfile import ZipFile
import unicodedata
from docx import Document
from fastapi import HTTPException
import pymupdf

from .pdf_extraction import PDF_LOCK

MAX_UNPACKED_DOCX = 40 * 1024 * 1024


def validate_upload(filename: str, content: bytes) -> tuple[str, str]:
    name = PurePosixPath(filename.replace('\\', '/')).name
    name = ''.join(c for c in name if not unicodedata.category(c).startswith('C'))[:240]
    extension = PurePosixPath(name).suffix.lower()
    if extension not in {'.docx', '.pdf'}:
        raise HTTPException(415, 'Only DOCX and PDF files are supported.')
    if not content:
        raise HTTPException(422, 'The uploaded file is empty.')
    try:
        if extension == '.docx':
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

        if extension == '.pdf':
            if not content.startswith(b'%PDF-'):
                raise ValueError('Missing PDF header')
            with PDF_LOCK, pymupdf.open(stream=content, filetype='pdf') as document:
                if document.needs_pass or document.page_count == 0:
                    raise ValueError('Encrypted or empty PDF')
            return name, 'application/pdf'
    except HTTPException:
        raise
    except Exception as error:
        file_type = 'PDF' if extension == '.pdf' else 'DOCX'
        raise HTTPException(422, f'Invalid, encrypted or unreadable {file_type} file.') from error


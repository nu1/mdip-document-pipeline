from pathlib import PurePosixPath
import unicodedata
from fastapi import HTTPException
from .extraction import AdapterRegistry, DocumentTooLarge


def validate_upload(filename: str, content: bytes, adapters: AdapterRegistry) -> tuple[str, str]:
    name = PurePosixPath(filename.replace('\\', '/')).name
    name = ''.join(c for c in name if not unicodedata.category(c).startswith('C'))[:240]
    extension = PurePosixPath(name).suffix.lower()
    try:
        adapter = adapters.for_extension(extension)
    except ValueError as error:
        supported = ', '.join(adapters.extensions)
        raise HTTPException(415, f'Supported file extensions: {supported}.') from error
    if not content:
        raise HTTPException(422, 'The uploaded file is empty.')
    try:
        adapter.validate(content)
    except DocumentTooLarge as error:
        raise HTTPException(413, str(error)) from error
    except Exception as error:
        file_type = extension.lstrip('.').upper()
        raise HTTPException(422, f'Invalid, encrypted or unreadable {file_type} file.') from error
    return name, adapter.content_type

